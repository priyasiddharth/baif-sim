#!/usr/bin/env python3
"""MBPP (Rust, via MultiPL-E) problems as test inputs for the Aeneas check loop.

Subcommands:
  fetch   N [--offset K] | fetch NAME...   copy problems from data/mbpp-rs.json into every tree
                                           (--remote: query the Hugging Face rows API instead)
  snapshot                                 refresh data/mbpp-rs.json from Hugging Face (records the
                                           dataset revision; existing mbpp/ dirs are not touched)
  test    NAME SOLUTION.rs                 compile solution + supplied tests, run them
  attempt NAME SOLUTION.rs [--commit]      record an attempt: run tests (refuses to record a
                                           failing version), then check.py under each selected
                                           Aeneas checkout; writes <tree>/<name>/attempt-N/,
                                           status.json, failures.md in each tree
  recheck NAME [--commit]                  rerun check.py on recorded attempts (after a check.py or
                                           Aeneas change); a tree without the problem is seeded with
                                           the attempts recorded in another tree
  log     NAME [--commit]                  rebuild failures.md from recorded attempts
  report  [NAME...]                        summarize attempts per problem and checkout (JSON)

Trees: one attempt history per Aeneas checkout, mbpp/aeneas_pristine/ (the
upstream pin in aeneas/) and mbpp/aeneas_mod/ (the fork in aeneas_mod/).
`--aeneas` is a comma-separated selection (default: $AENEAS or "pristine,mod");
a path to another checkout gets a tree named after its directory.

A problem directory <tree>/<name>/ holds prompt.rs (doc comment + signature),
tests.rs (the `main` with the assertions), status.json (dataset provenance +
attempt index) and failures.md (one section per attempt: check reasons, delta
from the previous attempt, code diff). Each attempt-N/ holds <name>.rs (the
solution), tests.txt, check.json (the check.py report — the result record)
and lean/ (check.py output). An `attempt` records the same solution as the
next attempt of every selected tree, so the trees stay aligned unless one is
run alone.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MBPP_DIR = ROOT / "mbpp"
CHECK = ROOT / "tools" / "check.py"
CHARON = ROOT / "charon" / "bin" / "charon"
HF_ROWS = "https://datasets-server.huggingface.co/rows"
HF_META = "https://huggingface.co/api/datasets/{dataset}"
DATASET = {"dataset": "nuprl/MultiPL-E", "config": "mbpp-rs", "split": "test"}
SNAPSHOT = ROOT / "data" / "mbpp-rs.json"   # pinned copy of the split, see `snapshot`
KNOWN_CHECKOUTS = ("pristine", "mod")        # as tools/check.py --aeneas
DEFAULT_CHECKOUTS = os.environ.get("AENEAS", ",".join(KNOWN_CHECKOUTS))


def toolchain():
    """The rustc nightly Charon is pinned to, so tests and translation agree."""
    try:
        out = subprocess.run([str(CHARON), "toolchain-version"], capture_output=True, text=True, check=True).stdout
        return out.strip().splitlines()[-1]
    except (OSError, subprocess.CalledProcessError):
        return "nightly"


# ---------------------------------------------------------------- trees

def parse_checkouts(s):
    cks = [c.strip() for c in s.split(",") if c.strip()]
    if not cks:
        sys.exit("--aeneas: empty selection")
    return cks


def tree(checkout):
    """mbpp/aeneas_<checkout>/: the attempt history recorded under that Aeneas checkout."""
    key = checkout if checkout in KNOWN_CHECKOUTS else Path(checkout).expanduser().resolve().name
    return MBPP_DIR / f"aeneas_{key}"


def trees():
    return sorted(p for p in MBPP_DIR.glob("aeneas_*") if p.is_dir())


def problem_inputs(name):
    """prompt.rs + tests.rs of a problem from whichever tree has them (they are identical)."""
    for t in trees():
        if (t / name / "prompt.rs").exists():
            return t / name
    return None


def problem_dir(t, name):
    """<tree>/<name>/, seeding prompt.rs/tests.rs/source from another tree if this one lacks them."""
    d = t / name
    if not (d / "prompt.rs").exists():
        src = problem_inputs(name)
        if src is None:
            sys.exit(f"no such problem: {name} (run `mbpp.py fetch {name}`)")
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(src / "prompt.rs", d / "prompt.rs")
        shutil.copy(src / "tests.rs", d / "tests.rs")
        status = load_status(d)
        status["source"] = load_status(src).get("source")
        (d / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    return d


# ---------------------------------------------------------------- fetch

def hf_rows(offset, length):
    q = urllib.parse.urlencode({**DATASET, "offset": offset, "length": length})
    with urllib.request.urlopen(f"{HF_ROWS}?{q}", timeout=60) as r:
        data = json.load(r)
    return data["num_rows_total"], [row["row"] for row in data["rows"]]


def hf_all_rows():
    rows, offset, total = [], 0, 1
    while offset < total:
        total, page = hf_rows(offset, 100)
        rows += page
        offset += 100
    return rows


def cmd_snapshot(args):
    """Pin the split: all rows plus the dataset's current git revision."""
    with urllib.request.urlopen(HF_META.format(**DATASET), timeout=60) as r:
        meta = json.load(r)
    rows = hf_all_rows()
    names = [row["name"] for row in rows]
    if len(set(names)) != len(names):
        sys.exit("duplicate problem names in dataset")
    snap = {**DATASET, "revision": meta["sha"], "last_modified": meta.get("lastModified"),
            "snapshot_date": datetime.date.today().isoformat(), "num_rows": len(rows), "rows": rows}
    SNAPSHOT.parent.mkdir(exist_ok=True)
    SNAPSHOT.write_text(json.dumps(snap, indent=1, ensure_ascii=False) + "\n")
    print(f"{SNAPSHOT.relative_to(ROOT)}: {len(rows)} rows, revision {meta['sha'][:7]}")


def load_snapshot():
    if not SNAPSHOT.exists():
        sys.exit(f"{SNAPSHOT.relative_to(ROOT)} missing; run `tools/mbpp.py snapshot` (or fetch --remote)")
    snap = json.loads(SNAPSHOT.read_text())
    for k in ("dataset", "config", "split"):
        if snap.get(k) != DATASET[k]:
            sys.exit(f"{SNAPSHOT.relative_to(ROOT)} is for {snap.get(k)!r}, expected {DATASET[k]!r}")
    return snap


def split_tests(tests):
    # MultiPL-E tests start with the "}" that closes the prompt's function.
    return re.sub(r"^\s*}\s*\n", "", tests, count=1)


def save_problem(row, source, checkouts):
    dirs = []
    for ck in checkouts:
        d = tree(ck) / row["name"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "prompt.rs").write_text(row["prompt"])
        (d / "tests.rs").write_text(split_tests(row["tests"]))
        # Provenance lives in status.json; prompt.rs/tests.rs are the only inputs used.
        status = load_status(d)
        status["source"] = {**source, "name": row["name"]}
        (d / "status.json").write_text(json.dumps(status, indent=2) + "\n")
        dirs.append(d)
    return dirs


def cmd_fetch(args):
    if args.remote:
        # Unpinned: whatever revision the rows API serves right now.
        source = {**DATASET, "revision": None}
        all_rows = None
    else:
        snap = load_snapshot()
        source = {**DATASET, "revision": snap["revision"]}
        all_rows = snap["rows"]
    rows = []
    if args.what and not args.what[0].isdigit():
        wanted = set(args.what)
        if all_rows is None:
            all_rows = hf_all_rows()
        for row in all_rows:
            if row["name"] in wanted:
                rows.append(row)
                wanted.discard(row["name"])
        if wanted:
            sys.exit(f"not found: {', '.join(sorted(wanted))}")
    else:
        n = int(args.what[0]) if args.what else 3
        if all_rows is None:
            _, rows = hf_rows(args.offset, n)
        else:
            rows = all_rows[args.offset:args.offset + n]
    for row in rows:
        for d in save_problem(row, source, parse_checkouts(args.aeneas)):
            print(d)


# ---------------------------------------------------------------- test

def run_tests(problem_dir, solution):
    """Compile solution + tests.rs with the pinned nightly and run the binary."""
    src = Path(solution).read_text()
    if "fn main" in src:
        return {"passed": False, "stage": "compile", "output": "solution.rs must not define main (tests supply it)"}
    program = src.rstrip() + "\n\n" + (problem_dir / "tests.rs").read_text()
    with tempfile.TemporaryDirectory(prefix="mbpp-test.") as tmp:
        main_rs = Path(tmp) / "main.rs"
        main_rs.write_text(program)
        exe = Path(tmp) / "main"
        build = subprocess.run(["rustup", "run", toolchain(), "rustc", "--edition=2021", "-O",
                                "-o", str(exe), str(main_rs)], capture_output=True, text=True)
        if build.returncode != 0:
            return {"passed": False, "stage": "compile", "output": build.stderr}
        try:
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return {"passed": False, "stage": "run", "output": "timed out after 60s"}
        if run.returncode != 0:
            return {"passed": False, "stage": "run", "output": run.stderr + run.stdout}
    return {"passed": True, "stage": "run", "output": run.stdout}


def cmd_test(args):
    d = problem_inputs(args.name)
    if d is None:
        sys.exit(f"no such problem: {args.name} (run `mbpp.py fetch {args.name}`)")
    res = run_tests(d, args.solution)
    print("PASS" if res["passed"] else f"FAIL ({res['stage']})")
    if res["output"].strip():
        print(res["output"].rstrip())
    sys.exit(0 if res["passed"] else 1)


# ---------------------------------------------------------------- attempt

def load_status(d):
    f = d / "status.json"
    return json.loads(f.read_text()) if f.exists() else {"name": d.name, "attempts": [], "done": False}


def save_status(d, status):
    status["done"] = bool(status["attempts"]) and status["attempts"][-1]["outcome"] == "pass"
    status["first_attempt_pass"] = bool(status["attempts"]) and status["attempts"][0]["outcome"] == "pass"
    (d / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    write_failure_log(d, status)


def record_attempt(d, status, ck, solution, tests):
    """Store `solution` as the next attempt of tree dir `d` and check it under checkout `ck`."""
    n = len(status["attempts"]) + 1
    adir = d / f"attempt-{n}"
    adir.mkdir(exist_ok=True)
    # The solution file must be named after the problem: check.py uses the
    # file name as the crate name.
    sol = adir / f"{d.name}.rs"
    shutil.copy(solution, sol)
    (adir / "tests.txt").write_text(f"PASS ({tests['stage']})\n{tests['output']}")
    # check.py's report (check.json) is the result record; status.json only indexes attempts.
    check = run_check(sol, adir, ck)
    result = {"attempt": n, "tests": {"passed": True, "stage": tests["stage"]}, "outcome": outcome_of(check),
              "aeneas": check.get("versions", {}).get("aeneas_checkout", ck)}
    status["attempts"].append(result)
    save_status(d, status)
    return result, check


def cmd_attempt(args):
    checkouts = parse_checkouts(args.aeneas)
    dirs = {ck: problem_dir(tree(ck), args.name) for ck in checkouts}
    statuses = {ck: load_status(d) for ck, d in dirs.items()}
    if all(s["done"] for s in statuses.values()) and not args.force:
        done = ", ".join(f"{ck}: attempt {len(s['attempts'])}" for ck, s in statuses.items())
        sys.exit(f"{args.name} already passed ({done}); use --force to add more")

    # Gate: a version that fails the supplied tests is never recorded, so every
    # committed attempt conforms to the tests. tests.rs is the same in every tree.
    tests = run_tests(dirs[checkouts[0]], args.solution)
    if not tests["passed"]:
        print(f"TESTS FAIL ({tests['stage']}) — not recorded\n{tests['output'].rstrip()}", file=sys.stderr)
        sys.exit(2)

    shown, outcomes, ns = {}, {}, {}
    for ck in checkouts:
        result, check = record_attempt(dirs[ck], statuses[ck], ck, args.solution, tests)
        shown[ck] = {**result, "check": summarize(check)}
        outcomes[ck], ns[ck] = result["outcome"], result["attempt"]
    all_pass = all(s["done"] for s in statuses.values())
    if args.commit:
        shown["committed"] = commit(dirs.values(), f"mbpp {args.name}: attempt {attempt_label(ns, outcomes)}")
    print(json.dumps(shown, indent=2))
    sys.exit(0 if all_pass else 1)


def attempt_label(ns, outcomes):
    """'2 pass' when every tree agrees, else '2 pristine=check:unsupported_code mod=pass'."""
    n = "/".join(sorted({str(n) for n in ns.values()}, key=int))
    if len(set(outcomes.values())) == 1:
        o = next(iter(outcomes.values()))
        return f"{n} {o}" if set(outcomes) == set(KNOWN_CHECKOUTS) else f"{n} {o} (aeneas: {', '.join(outcomes)})"
    return f"{n} " + " ".join(f"{ck}={o}" for ck, o in outcomes.items())


def write_failure_log(d, status):
    """<tree>/<name>/failures.md: one accumulating log, one section per attempt,
    with the delta in check reasons and the code diff from the previous attempt."""
    import difflib
    lines = [f"# {d.name} — failure log ({d.parent.name.replace('_', ': ', 1)})", ""]
    prev, prev_chk = None, {}
    for r in status["attempts"]:
        n = r["attempt"]
        chk = summarize(load_check(d, n))
        lines += [f"## Attempt {n} — {r['outcome']}", ""]
        reasons = chk.get("reasons", [])
        if prev is not None:
            prev_reasons = prev_chk.get("reasons", [])
            resolved = [x for x in prev_reasons if x not in reasons]
            remaining = [x for x in prev_reasons if x in reasons]
            new = [x for x in reasons if x not in prev_reasons]
            lines.append(f"Delta from attempt {n - 1}:")
            for label, items in (("resolved", resolved), ("still failing", remaining), ("new", new)):
                lines.append(f"- {label}: {len(items)}")
                lines += [f"  - {x}" for x in items]
        else:
            lines.append("Initial version.")
            lines += ["Reasons:"] + [f"- {x}" for x in reasons] if reasons else ["No check failures."]
        fns = ", ".join(f"{a.split('::')[-1] if '{' not in a else '{closure}'} {b}" for a, b in chk.get("functions", []))
        lines += ["", f"Functions: {fns or 'none'}", f"Axioms: {', '.join(chk.get('axioms', [])) or 'none'}", ""]
        cur_src = (d / f"attempt-{n}" / f"{d.name}.rs").read_text().splitlines()
        if prev is not None:
            prev_src = (d / f"attempt-{prev['attempt']}" / f"{d.name}.rs").read_text().splitlines()
            diff = list(difflib.unified_diff(prev_src, cur_src, f"attempt-{n - 1}", f"attempt-{n}", lineterm=""))
            lines += [f"Code diff from attempt {n - 1}:", "```diff", *diff, "```", ""]
        else:
            lines += ["Code:", "```rust", *cur_src, "```", ""]
        prev, prev_chk = r, chk
    (d / "failures.md").write_text("\n".join(lines))


def run_check(sol, adir, aeneas="pristine"):
    """Run check.py on a solution; its JSON report is saved as attempt-N/check.json.
    `aeneas` selects the checkout (pristine | mod | path); check.json records it under versions."""
    proc = subprocess.run([sys.executable, str(CHECK), str(sol), "-o", str(adir / "lean"), "--aeneas", aeneas],
                          capture_output=True, text=True)
    try:
        check = json.loads(proc.stdout)
    except json.JSONDecodeError:
        check = {"verdict": "toolchain_problem", "reasons": [f"check.py produced no report: {proc.stderr[-2000:]}"]}
    check.pop("output_dir", None)
    (adir / "check.json").write_text(json.dumps(check, indent=2) + "\n")
    return check


def load_check(d, n):
    f = d / f"attempt-{n}" / "check.json"
    return json.loads(f.read_text()) if f.exists() else {}


def outcome_of(check):
    return "pass" if check.get("verdict") == "translates" else f"check:{check.get('verdict')}"


def summarize(check):
    return {"verdict": check.get("verdict"), "reasons": check.get("reasons", []),
            "functions": [(f["rust"], f["status"]) for f in check.get("functions", [])],
            "axioms": [a.get("rust") or a["lean"] for a in check.get("axioms", [])]}


def seed_attempts(d, name):
    """Copy the recorded solutions of `name` from the tree with the most attempts into `d`
    (which has none), so a new tree can be checked on the same history."""
    best, best_status = None, {"attempts": []}
    for t in trees():
        if t / name != d:
            st = load_status(t / name) if (t / name / "status.json").exists() else {"attempts": []}
            if len(st["attempts"]) > len(best_status["attempts"]):
                best, best_status = t / name, st
    if best is None:
        return load_status(d)
    status = load_status(d)
    for r in best_status["attempts"]:
        src, dst = best / f"attempt-{r['attempt']}", d / f"attempt-{r['attempt']}"
        dst.mkdir(exist_ok=True)
        shutil.copy(src / f"{name}.rs", dst / f"{name}.rs")
        if (src / "tests.txt").exists():
            shutil.copy(src / "tests.txt", dst / "tests.txt")
        status["attempts"].append({"attempt": r["attempt"], "tests": r.get("tests"), "outcome": None})
    return status


def cmd_recheck(args):
    """Rerun check.py on every recorded attempt (after a check.py or Aeneas change); tests are not rerun.
    A selected tree without attempts for the problem is seeded from the fullest other tree."""
    out, dirs = {}, []
    for ck in parse_checkouts(args.aeneas):
        d = problem_dir(tree(ck), args.name)
        dirs.append(d)
        status = load_status(d)
        if not status["attempts"]:
            status = seed_attempts(d, args.name)
        for result in status["attempts"]:
            adir = d / f"attempt-{result['attempt']}"
            if result["tests"] is None or result["tests"]["passed"]:
                check = run_check(adir / f"{d.name}.rs", adir, ck)
                result["outcome"] = outcome_of(check)
                result["aeneas"] = check.get("versions", {}).get("aeneas_checkout", ck)
                result.pop("check", None)
        save_status(d, status)
        out[ck] = [(a["attempt"], a["outcome"]) for a in status["attempts"]]
    if args.commit:
        cks = list(out)
        tag = "" if set(cks) == set(KNOWN_CHECKOUTS) else f" (aeneas: {', '.join(cks)})"
        commit(dirs, f"mbpp {args.name}: recheck{tag}")
    print(json.dumps(out))


def commit(dirs, msg):
    subprocess.run(["git", "-C", str(ROOT), "add", *[str(d.relative_to(ROOT)) for d in dirs]], check=True)
    subprocess.run(["git", "-C", str(ROOT), "commit", "-q", "-m", msg], check=True)
    return msg


# ---------------------------------------------------------------- report

def cmd_log(args):
    """Rebuild failures.md from the recorded attempts."""
    dirs = []
    for ck in parse_checkouts(args.aeneas):
        d = problem_dir(tree(ck), args.name)
        write_failure_log(d, load_status(d))
        dirs.append(d)
        print(d / "failures.md")
    if args.commit:
        commit(dirs, f"mbpp {args.name}: failure log")


def cmd_report(args):
    ts = trees()
    names = args.names or sorted({p.name for t in ts for p in t.iterdir() if (p / "prompt.rs").exists()})
    rows = []
    for name in names:
        row = {"name": name}
        for t in ts:
            if not (t / name / "status.json").exists():
                continue
            st = load_status(t / name)
            row[t.name.removeprefix("aeneas_")] = {
                "done": st["done"], "attempts": len(st["attempts"]),
                "first_attempt_pass": st.get("first_attempt_pass", False),
                "history": [a["outcome"] for a in st["attempts"]]}
        rows.append(row)
    print(json.dumps(rows, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch"); f.add_argument("what", nargs="*"); f.add_argument("--offset", type=int, default=0)
    f.add_argument("--remote", action="store_true", help="query Hugging Face instead of data/mbpp-rs.json")
    sub.add_parser("snapshot")
    t = sub.add_parser("test"); t.add_argument("name"); t.add_argument("solution")
    a = sub.add_parser("attempt"); a.add_argument("name"); a.add_argument("solution")
    a.add_argument("--commit", action="store_true"); a.add_argument("--force", action="store_true")
    rc = sub.add_parser("recheck"); rc.add_argument("name"); rc.add_argument("--commit", action="store_true")
    lg = sub.add_parser("log"); lg.add_argument("name"); lg.add_argument("--commit", action="store_true")
    for sp in (f, a, rc, lg):
        sp.add_argument("--aeneas", default=DEFAULT_CHECKOUTS,
                        help="Aeneas checkouts, comma-separated: pristine (aeneas/), mod (aeneas_mod/) or a path; "
                             "one tree mbpp/aeneas_<checkout>/ each (default: $AENEAS or pristine,mod)")
    r = sub.add_parser("report"); r.add_argument("names", nargs="*")
    args = p.parse_args()
    {"fetch": cmd_fetch, "snapshot": cmd_snapshot, "test": cmd_test, "attempt": cmd_attempt, "recheck": cmd_recheck,
     "log": cmd_log, "report": cmd_report}[args.cmd](args)


if __name__ == "__main__":
    main()
