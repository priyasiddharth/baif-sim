#!/usr/bin/env python3
"""Check whether a Rust file translates to Lean through Charon and Aeneas.

Runs Charon, then Aeneas, then type-checks the generated Lean and prints the
axioms each translated function depends on. Prints one JSON report on stdout
(or a human-readable summary with --human).

Exit codes mirror the verdict:
  0 translates, 1 unsupported_code, 2 missing_context, 3 invalid_rust,
  4 toolchain_problem, 64 usage error.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHARON = ROOT / "charon" / "bin" / "charon"
# Which Aeneas checkout to run: "pristine" (aeneas/, the upstream pin), "mod"
# (aeneas_mod/, our fork with local patches) or a path. Default from $AENEAS,
# overridden by --aeneas. The Lean library comes from the same checkout when it
# is built there, otherwise from the pristine one (same library at the same
# base commit; the patches so far only touch the OCaml side).
AENEAS_CHECKOUTS = {"pristine": ROOT / "aeneas", "mod": ROOT / "aeneas_mod"}
AENEAS_DIR = None   # set by select_aeneas()
AENEAS = None
LEAN_LIB = None


def select_aeneas(which):
    global AENEAS_DIR, AENEAS, LEAN_LIB
    AENEAS_DIR = AENEAS_CHECKOUTS.get(which) or Path(which).expanduser().resolve()
    AENEAS = AENEAS_DIR / "bin" / "aeneas"
    own_lib = AENEAS_DIR / "backends" / "lean"
    LEAN_LIB = own_lib if (own_lib / ".lake" / "build").exists() else AENEAS_CHECKOUTS["pristine"] / "backends" / "lean"
    return AENEAS_DIR


select_aeneas(os.environ.get("AENEAS", "pristine"))

EXIT_CODES = {
    "translates": 0,
    "unsupported_code": 1,
    "missing_context": 2,
    "invalid_rust": 3,
    "toolchain_problem": 4,
}
# Most severe first: the overall verdict is the most severe problem found.
SEVERITY = ["toolchain_problem", "invalid_rust", "unsupported_code", "missing_context"]

# Axioms every Lean proof may use; not holes in the translation.
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}
STDLIB_CRATES = {"core", "alloc", "std"}
# rustc errors that mean surrounding code or a dependency is missing.
MISSING_CONTEXT_CODES = {"E0405", "E0412", "E0422", "E0425", "E0432", "E0433", "E0463"}

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, ANSI.sub("", p.stdout), ANSI.sub("", p.stderr)


def git_rev(path):
    code, out, _ = run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"])
    return out.strip() if code == 0 else None


def versions():
    code, out, _ = run([str(CHARON), "toolchain-version"])
    rustc = out.strip().splitlines()[-1] if code == 0 and out.strip() else None
    pin = None
    pin_file = ROOT / "aeneas" / "charon-pin"
    if pin_file.exists():
        lines = [l for l in pin_file.read_text().splitlines() if l and not l.startswith("#")]
        pin = lines[0].strip() if lines else None
    code, full_charon, _ = run(["git", "-C", str(ROOT / "charon"), "rev-parse", "HEAD"])
    lean_toolchain = LEAN_LIB / "lean-toolchain"
    lean = lean_toolchain.read_text().strip().split(":")[-1] if lean_toolchain.exists() else None
    which = next((k for k, v in AENEAS_CHECKOUTS.items() if v == AENEAS_DIR), str(AENEAS_DIR))
    return {
        "aeneas": git_rev(AENEAS_DIR),
        "aeneas_checkout": which,
        "aeneas_dir": str(AENEAS_DIR.relative_to(ROOT)) if AENEAS_DIR.is_relative_to(ROOT) else str(AENEAS_DIR),
        "lean_lib": str(LEAN_LIB.relative_to(ROOT)) if LEAN_LIB.is_relative_to(ROOT) else str(LEAN_LIB),
        "charon": git_rev(ROOT / "charon"),
        "charon_matches_pin": pin is not None and full_charon.strip() == pin,
        "rustc": rustc,
        "lean": lean,
    }


# ---------------------------------------------------------------- Charon

def parse_charon_output(text):
    """Return (warnings, errors) from Charon/rustc diagnostics."""
    warnings, errors = [], []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(warning|error)(\[(E\d+)\])?: (.*)$", line)
        panic = re.match(r"^thread '.*' panicked at (.*)$", line)
        if m:
            kind, code, msg = m.group(1), m.group(3), m.group(4)
            if re.match(r"(aborting due to|The extraction generated|\d+ warnings? emitted)", msg):
                continue
            diag = {"message": msg, "code": code}
            for nxt in lines[i + 1:i + 4]:
                loc = re.match(r"^\s*--> (.*):(\d+):(\d+)$", nxt)
                if loc:
                    diag.update(file=loc.group(1), line=int(loc.group(2)), col=int(loc.group(3)))
                    break
            (warnings if kind == "warning" else errors).append(diag)
        elif panic:
            msg = lines[i + 1].strip() if i + 1 < len(lines) else ""
            errors.append({"message": f"charon panicked at {panic.group(1)}: {msg}", "code": "panic"})
    return warnings, errors


def charon_stage(src, out_dir, charon_args):
    llbc = out_dir / f"{src.stem}.llbc"
    # Run from the source directory with a relative path: Aeneas copies the
    # path into Lean doc comments, and a path containing "/-" opens a comment.
    cmd = [str(CHARON), "rustc", "--preset=aeneas", f"--dest-file={llbc}", *charon_args,
           "--", "--crate-type=lib", "--edition=2021", "-Awarnings", src.name]
    # -Awarnings silences rustc lints (dead_code, naming); Charon's own
    # "not supported" warnings are not lints and still print.
    code, out, err = run(cmd, cwd=src.parent)
    log = out + err
    warnings, errors = parse_charon_output(log)
    data = None
    if llbc.exists():
        try:
            data = json.loads(llbc.read_text())
        except json.JSONDecodeError:
            data = None
    if code != 0 or data is None:
        status = "failed"
    elif warnings or errors or data.get("has_errors"):
        status = "partial"
    else:
        status = "ok"
    stage = {
        "status": status,
        "rust_compiled": "Code failed to compile" not in log,
        "warnings": warnings,
        "errors": errors,
    }
    return stage, data, llbc, log


def name_to_str(name):
    parts = []
    for elem in name:
        if "Ident" in elem:
            parts.append(elem["Ident"][0])
        elif "Impl" in elem:
            parts.append("{impl}")
    return "::".join(parts)


def span_start(span):
    data = span.get("Untagged", {}).get("data") if isinstance(span, dict) else None
    if not data:
        return None
    return data["beg"]["line"], data["beg"]["col"]


def local_functions(llbc_data):
    funs = []
    for decl in llbc_data["translated"]["fun_decls"]:
        if not decl:
            continue
        meta = decl["item_meta"]
        if not meta.get("is_local"):
            continue
        funs.append({
            "rust": name_to_str(meta["name"]),
            "start": span_start(meta["span"]),
            "charon_error": bool(meta.get("has_errors")) or "Error" in (decl.get("body") or {}),
        })
    return funs


# ---------------------------------------------------------------- Aeneas

_rustc_src = None


def rustc_src_root():
    """The toolchain's rust-src, for resolving rustc's remapped /rustc/library/ paths."""
    global _rustc_src
    if _rustc_src is None:
        _, tc, _ = run([str(CHARON), "toolchain-version"])
        tc = tc.strip().splitlines()[-1] if tc.strip() else "nightly"
        code, out, _ = run(["rustup", "run", tc, "rustc", "--print", "sysroot"])
        _rustc_src = Path(out.strip()) / "lib/rustlib/src/rust/library" if code == 0 else Path("/nonexistent")
    return _rustc_src


def source_snippet(file, line):
    p = Path(file)
    if file.startswith("/rustc/library/"):
        p = rustc_src_root() / file[len("/rustc/library/"):]
    try:
        return p.read_text().splitlines()[line - 1].strip()
    except (OSError, IndexError, UnicodeDecodeError):
        return None


def parse_aeneas_output(text):
    """Return [Error]/[Warn] blocks with their source locations.

    Aeneas prints a bare error (e.g. "Unimplemented") at a stdlib location, then
    a warning "Could not translate ... 'item' because of previous error" that
    names the item and where user code uses it; an uncaught exception ends the
    run with "Fatal error: exception ...". All three are folded together here.
    """
    text = text.replace("\r", "\n")
    blocks, cur, crash = [], None, None
    for line in text.splitlines():
        m = re.match(r"^.*?\[(Error|Warn |Info )\] (.*)$", line)
        fatal = re.match(r"^Fatal error: exception (.*)$", line)
        frame = re.match(r"^(?:Raised at|Called from) (\S+) in file \"([^\"]+)\", lines? (\d+)", line)
        if m:
            cur = {"level": m.group(1).strip(), "lines": [m.group(2)]}
            blocks.append(cur)
        elif fatal:
            crash, cur = {"exception": fatal.group(1), "frames": []}, None
        elif frame and crash is not None:
            crash["frames"].append(f"{frame.group(1)} ({frame.group(2)}:{frame.group(3)})")
        elif cur is not None and line.strip():
            cur["lines"].append(line.strip())
    errors, warnings = [], []
    for b in blocks:
        if b["level"] == "Info":
            continue
        msg_lines, diag, sources = [], {}, []
        for l in b["lines"]:
            src = re.match(r"^Source: (?:Source: )?'(.*?)', lines (\d+):(\d+)-(\d+):(\d+)", l)
            name = re.match(r"^Name pattern: '(.*)'$", l)
            if src:
                sources.append({"file": src.group(1), "line": int(src.group(2)), "col": int(src.group(3)),
                                "end_line": int(src.group(4))})
            elif name:
                diag["item"] = name.group(1)
            elif re.match(r"^(Compiler source|Definition span|Trait declaration|This definition is)", l):
                continue
            elif not sources:
                msg_lines.append(l)
        if sources:
            diag.update(sources[0])
            snippet = source_snippet(sources[0]["file"], sources[0]["line"])
            if snippet:
                diag["snippet"] = snippet
            user = [s for s in sources if not s["file"].startswith("/rustc/")]
            if user:
                diag["used_at"] = [f"{s['file']}:{s['line']}:{s['col']}" for s in user]
        diag = {"message": " ".join(msg_lines), **diag}
        if b["level"] == "Error":
            errors.append(diag)
        else:
            warnings.append(diag)
            if "because of previous error" in diag["message"] and errors and "item" not in errors[-1]:
                for k in ("item", "used_at"):
                    if k in diag:
                        errors[-1][k] = diag[k]
    if crash:
        where = crash["frames"][1] if len(crash["frames"]) > 1 else (crash["frames"] or ["?"])[0]
        errors.append({"message": f"Aeneas aborted with exception {crash['exception']} in {where}; "
                                  "no functions were translated", "crash": True})
    return warnings, errors


def describe(e):
    """One-line human form of a diagnostic: message, item, location, source line, use sites."""
    s = e["message"]
    if e.get("item"):
        s += f" — in `{e['item']}`"
    if e.get("file"):
        s += f" at {e['file']}:{e['line']}"
    if e.get("snippet"):
        s += f" (`{e['snippet']}`)"
    if e.get("used_at"):
        s += f", used from {', '.join(e['used_at'])}"
    return s


def aeneas_stage(llbc, out_dir, namespace):
    for old in out_dir.glob("*.lean"):
        old.unlink()
    cmd = [str(AENEAS), "-backend", "lean", str(llbc), "-dest", str(out_dir), "-namespace", namespace]
    code, out, err = run(cmd)
    warnings, errors = parse_aeneas_output(out + err)
    lean_files = sorted(out_dir.glob("*.lean"))
    if code == 0 and lean_files:
        status = "ok"
    elif lean_files:
        status = "partial"
    else:
        status = "failed"
    return {"status": status, "warnings": warnings, "errors": errors}, (lean_files[0] if lean_files else None)


DOC_HEADER = re.compile(
    r"/-- \[(?P<rust>[^\n]+?)\]:?(?P<extra>[^\n]*)\n\s*Source: '[^']*', lines (?P<line>\d+):(?P<col>\d+)"
    r"(?:(?!-/).)*?-/\n(?P<attrs>(?:@\[.*?\]\s*)*)(?P<kind>noncomputable def|def|axiom|opaque|structure|inductive|abbrev|class|instance)\s+(?P<name>[^\s:({\[]+)",
    re.S,
)


def lean_decls(lean_file):
    """Top-level declarations Aeneas generated, keyed by Lean name."""
    decls = []
    text = lean_file.read_text()
    for m in DOC_HEADER.finditer(text):
        # Bodies stop at the next doc comment; "sorry" marks a body Aeneas failed on.
        body_end = text.find("/--", m.end())
        body = text[m.end(): body_end if body_end != -1 else len(text)]
        decls.append({
            "rust": m.group("rust"),
            "is_loop": bool(m.group("extra").strip()),
            "start": (int(m.group("line")), int(m.group("col"))),
            "kind": m.group("kind").split()[-1],
            "lean": m.group("name"),
            "sorry": bool(re.search(r"\bsorry\b", body)),
        })
    return decls


# ---------------------------------------------------------------- Lean

def lean_stage(lean_file, namespace, def_names):
    if not (LEAN_LIB / ".lake" / "build").exists():
        return {"status": "skipped", "reason": "Aeneas Lean library not built (run lake build in aeneas/backends/lean)",
                "errors": []}, {}
    check = lean_file.with_name(f"_check_{lean_file.name}")
    n_lines = len(lean_file.read_text().splitlines())
    prints = "".join(f"\n#print axioms {namespace}.{n}" for n in def_names)
    check.write_text(lean_file.read_text() + "\n" + prints + "\n")
    try:
        _, out, err = run(["lake", "env", "lean", str(check)], cwd=LEAN_LIB)
    except FileNotFoundError:
        return {"status": "skipped", "reason": "lake not on PATH (install elan)", "errors": []}, {}
    finally:
        check.unlink(missing_ok=True)
    text = out + err
    errors = []
    # A Lean diagnostic is "file:line:col: error: msg" and runs until the next
    # "file:line:col: level:" header (continuation lines are not all indented).
    header = r"^[^\n]*?:(\d+):(\d+): (error|warning|info)(?:\([^)]*\))?: "
    for m in re.finditer(header + r"(.*?)(?=" + header + r"|\Z)", text, re.M | re.S):
        line = int(m.group(1))
        if m.group(3) == "error" and line <= n_lines:
            msg = " ".join(l.strip() for l in m.group(4).splitlines() if l.strip())
            errors.append({"message": msg[:600], "line": line, "col": int(m.group(2))})
    axioms = {}
    for m in re.finditer(r"'([^']+)' depends on axioms: \[(.*?)\]", text, re.S):
        axioms[m.group(1)] = [a.strip().replace("«", "").replace("»", "")
                              for a in m.group(2).split(",") if a.strip()]
    for m in re.finditer(r"'([^']+)' does not depend on any axioms", text):
        axioms[m.group(1)] = []
    return {"status": "failed" if errors else "ok", "errors": errors}, axioms


# ---------------------------------------------------------------- Report

def classify_charon(stage):
    reasons = []
    if not stage["rust_compiled"]:
        codes = {e.get("code") for e in stage["errors"]}
        if codes & MISSING_CONTEXT_CODES:
            reasons.append(("missing_context", "rustc cannot resolve names: surrounding code or a dependency is missing"))
        else:
            reasons.append(("invalid_rust", "rustc rejected the code"))
        return reasons
    for e in stage["errors"] + stage["warnings"]:
        msg = e["message"]
        if e.get("code") == "panic":
            reasons.append(("toolchain_problem", f"Charon crashed: {msg}"))
        elif "--include" in msg or "opaque" in msg:
            reasons.append(("missing_context", f"Charon: {msg}"))
        else:
            reasons.append(("unsupported_code", f"Charon: {msg}"))
    if stage["status"] == "failed" and not reasons:
        reasons.append(("toolchain_problem", "Charon failed without a diagnostic"))
    return reasons


def classify_aeneas(stage, charon_had_problems):
    reasons = []
    for e in stage["errors"]:
        msg = e["message"]
        if "type error in the output of charon" in msg or "Internal error" in msg:
            if not charon_had_problems:
                reasons.append(("toolchain_problem", f"Aeneas: {msg}"))
            # Otherwise a consequence of the Charon problem already reported.
        elif e.get("crash"):
            # A crash right after a reported limitation is that limitation's
            # consequence; a crash with no diagnostic is a tool bug.
            reasons.append(("unsupported_code" if reasons else "toolchain_problem", f"Aeneas: {msg}"))
        else:
            reasons.append(("unsupported_code", f"Aeneas: {describe(e)}"))
    if stage["status"] == "failed" and not reasons and not charon_had_problems:
        reasons.append(("toolchain_problem", "Aeneas produced no Lean file"))
    return reasons


def axiom_origin(rust_name, crate):
    if rust_name is None:
        return "library"
    head = rust_name.split("::")[0]
    if head in STDLIB_CRATES:
        return "stdlib"
    if head == crate:
        return "local"
    return "dependency"


def check(src, out_dir, charon_args):
    crate = src.stem
    namespace = "".join(p[:1].upper() + p[1:] for p in re.split(r"[_\-]", crate) if p) or "Crate"
    report = {"input": str(src), "versions": versions(), "stages": {}, "functions": [], "axioms": [],
              "verdict": None, "reasons": [], "output_dir": str(out_dir)}
    reasons = []
    if not report["versions"]["charon_matches_pin"]:
        report["reasons"].append("note: charon is not at the commit in aeneas/charon-pin")

    charon, llbc_data, llbc, _ = charon_stage(src, out_dir, charon_args)
    report["stages"]["charon"] = charon
    reasons += classify_charon(charon)
    skipped = {"status": "skipped", "errors": []}

    if charon["status"] == "failed":
        report["stages"]["aeneas"] = report["stages"]["lean"] = skipped
    else:
        aeneas, lean_file = aeneas_stage(llbc, out_dir, namespace)
        report["stages"]["aeneas"] = aeneas
        reasons += classify_aeneas(aeneas, charon["status"] != "ok")

        decls = lean_decls(lean_file) if lean_file else []
        by_start = {d["start"]: d for d in decls if d["kind"] in ("def", "opaque", "axiom") and not d["is_loop"]}
        local = local_functions(llbc_data)
        starts = sorted(f["start"][0] for f in local if f["start"])

        def owner_line(line):
            # The function an error belongs to: the last one starting at or before it.
            before = [s for s in starts if s <= line]
            return before[-1] if before else None

        functions = []
        for f in local:
            d = by_start.get(f["start"])
            entry = {"rust": f["rust"], "lean": None, "status": "missing", "reason": None, "error_ref": None}
            if d:
                entry["rust"] = d["rust"]
                entry["lean"] = f"{namespace}.{d['lean']}"
                entry["status"] = "sorry" if d["sorry"] else ("axiom" if d["kind"] != "def" else "translated")
            if entry["status"] != "translated":
                entry["reason"] = "charon_error" if f["charon_error"] else "aeneas_error"
                # error_ref points at the diagnostic, e.g. {"stage": "aeneas", "list": "errors", "index": 0}.
                stage_name = "charon" if f["charon_error"] else "aeneas"
                stage = charon if f["charon_error"] else aeneas
                for list_name in ("errors", "warnings"):
                    for i, e in enumerate(stage[list_name]):
                        if f["start"] and e.get("line") is not None and owner_line(e["line"]) == f["start"][0]:
                            entry["error_ref"] = {"stage": stage_name, "list": list_name, "index": i}
                            break
                    if entry["error_ref"]:
                        break
            # Several LLBC decls can share a span (closure call_once/call_mut),
            # so they map to one Lean decl; keep one entry each.
            if entry not in functions:
                functions.append(entry)
        report["functions"] = functions

        if lean_file is None:
            report["stages"]["lean"] = skipped
        else:
            defs = [f["lean"][len(namespace) + 1:] for f in functions if f["status"] in ("translated", "sorry")]
            lean, axioms_by_fn = lean_stage(lean_file, namespace, defs)
            report["stages"]["lean"] = lean
            if lean["status"] == "skipped":
                # No type-check and no #print axioms: the verdict cannot be "translates".
                reasons.append(("toolchain_problem", f"Lean check skipped: {lean['reason']}"))
            for e in lean["errors"]:
                msg = e["message"]
                # Aeneas emitted a call to a method the Lean library's model
                # does not define: a missing model, not a broken toolchain.
                if re.search(r"is not a field of structure|unknown (constant|identifier)", msg):
                    reasons.append(("missing_context", f"Lean library lacks a model: {msg}"))
                else:
                    reasons.append(("toolchain_problem", f"generated Lean does not type-check: {msg}"))

            rust_of_axiom = {f"{namespace}.{d['lean']}": d["rust"] for d in decls if d["kind"] == "axiom"}
            axioms = {}
            for fn, used in axioms_by_fn.items():
                for ax in used:
                    if ax in STANDARD_AXIOMS or ax == "sorryAx":
                        continue
                    a = axioms.setdefault(ax, {"lean": ax, "rust": rust_of_axiom.get(ax),
                                               "origin": axiom_origin(rust_of_axiom.get(ax), crate),
                                               "used_by": []})
                    a["used_by"].append(fn)
            # Axioms declared in the file but used by nothing checked (e.g. only
            # called from a body that became sorry) are still holes.
            for ax, rust in rust_of_axiom.items():
                axioms.setdefault(ax, {"lean": ax, "rust": rust, "origin": axiom_origin(rust, crate), "used_by": []})
            report["axioms"] = list(axioms.values())
            for a in report["axioms"]:
                what = {"stdlib": "no Lean model for standard-library item",
                        "dependency": "dependency not translated (try --include)",
                        "local": "local item left opaque",
                        "library": "axiom from the Aeneas Lean library"}[a["origin"]]
                reasons.append(("missing_context", f"{what}: {a['rust'] or a['lean']}"))

    found = {v for v, _ in reasons}
    report["verdict"] = next((v for v in SEVERITY if v in found), "translates")
    report["reasons"] += list(dict.fromkeys(f"{v}: {msg}" for v, msg in reasons))
    return report


def human(report):
    lines = [f"input:     {report['input']}"]
    v = report["versions"]
    lines.append(f"versions:  aeneas {v['aeneas']} · charon {v['charon']}"
                 f"{' (= charon-pin)' if v['charon_matches_pin'] else ' (≠ charon-pin)'}"
                 f" · rustc {v['rustc']} · lean {v['lean']}")
    for name, st in report["stages"].items():
        msgs = [describe(e) for e in st.get("errors", [])] + [w["message"] for w in st.get("warnings", [])]
        lines.append(f"{name + ':':10} {st['status']}" + (f" — {msgs[0]}" if msgs else ""))
    for f in report["functions"]:
        lines.append(f"  fn {f['rust']}: {f['status']}" + (f" ({f['reason']})" if f["reason"] else ""))
    for a in report["axioms"]:
        used = ", ".join(a["used_by"]) or "nothing checked"
        lines.append(f"  axiom {a['lean']} [{a['origin']}] ← {a['rust']}  used by {used}")
    lines.append(f"verdict:   {report['verdict']}")
    for r in report["reasons"]:
        lines.append(f"  - {r}")
    lines.append(f"output:    {report['output_dir']}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.error = lambda msg: (parser.print_usage(sys.stderr), print(f"error: {msg}", file=sys.stderr), sys.exit(64))
    parser.add_argument("file", type=Path, help="Rust source file (translated as a library crate)")
    parser.add_argument("-o", "--out", type=Path, help="output directory (default: a new temp dir)")
    parser.add_argument("--charon-arg", action="append", default=[],
                        help="extra argument for charon, e.g. --charon-arg=--include=foo (repeatable)")
    parser.add_argument("--human", action="store_true", help="print a readable summary instead of JSON")
    parser.add_argument("--aeneas", default=os.environ.get("AENEAS", "pristine"),
                        help="Aeneas checkout to run: pristine (aeneas/), mod (aeneas_mod/) or a path "
                             "(default: $AENEAS or pristine)")
    args = parser.parse_args()
    select_aeneas(args.aeneas)

    src = args.file.resolve()
    if not src.is_file() or src.suffix != ".rs":
        parser.error(f"not a .rs file: {args.file}")
    problems = [f"not built: {t}" for t in (CHARON, AENEAS) if not t.exists()]
    if not AENEAS_DIR.is_dir():
        problems = [f"no such Aeneas checkout {args.aeneas!r} (known: {', '.join(AENEAS_CHECKOUTS)}, or a path)"]
    if problems:
        # Still a JSON report, so a caller always gets a structured verdict.
        report = {"input": str(src), "versions": versions(), "stages": {}, "functions": [], "axioms": [],
                  "verdict": "toolchain_problem",
                  "reasons": [f"toolchain_problem: {m}" for m in problems], "output_dir": None}
        print(human(report) if args.human else json.dumps(report, indent=2))
        sys.exit(EXIT_CODES["toolchain_problem"])

    out_dir = args.out.resolve() if args.out else Path(tempfile.mkdtemp(prefix=f"{src.stem}-lean."))
    out_dir.mkdir(parents=True, exist_ok=True)

    report = check(src, out_dir, args.charon_arg)
    print(human(report) if args.human else json.dumps(report, indent=2))
    sys.exit(EXIT_CODES[report["verdict"]])


if __name__ == "__main__":
    main()
