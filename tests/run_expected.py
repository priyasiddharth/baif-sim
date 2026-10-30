#!/usr/bin/env python3
"""Run tools/check.py on every input in tests/expected.json, for each Aeneas
checkout listed there, and compare the result with the expected one.

  tests/run_expected.py                  all inputs, all checkouts
  tests/run_expected.py --aeneas mod     one checkout only
  tests/run_expected.py --update         rewrite the expected verdicts with what ran

An expectation is either a verdict string, or an object:
  {"verdict": "...",
   "reasons": ["substring", ...],        each must occur in some reason
   "noted_axioms": ["core::ptr::swap"],  each must match an axiom carrying a note
   "axioms": 3}                          exact number of axioms reported
--update rewrites only the verdict; the other fields are kept and still checked.

Exit 0 when every expectation holds, 1 otherwise. Prints one row per input.
"""

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ROOT / "tests" / "expected.json"
CHECK = ROOT / "tools" / "check.py"


def run_check(src, aeneas):
    p = subprocess.run([sys.executable, str(CHECK), str(ROOT / src), "--aeneas", aeneas],
                       capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"verdict": "no_report", "reasons": [p.stderr.strip()[-300:]], "axioms": []}


def mismatches(report, want):
    """Human-readable list of expectation failures (empty when all hold)."""
    want = {"verdict": want} if isinstance(want, str) else want
    out = []
    if report["verdict"] != want["verdict"]:
        out.append(f"verdict {report['verdict']} (expected {want['verdict']})")
    reasons = report.get("reasons", [])
    for sub in want.get("reasons", []):
        if not any(sub in r for r in reasons):
            out.append(f"no reason contains {sub!r}")
    axioms = report.get("axioms", [])
    for sub in want.get("noted_axioms", []):
        if not any(sub in (a.get("rust") or a["lean"]) and a.get("note") for a in axioms):
            out.append(f"no noted axiom matches {sub!r}")
    if "axioms" in want and len(axioms) != want["axioms"]:
        out.append(f"{len(axioms)} axioms (expected {want['axioms']})")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aeneas", action="append", help="restrict to this checkout (repeatable)")
    ap.add_argument("--update", action="store_true", help="write the observed verdicts back to expected.json")
    ap.add_argument("-j", "--jobs", type=int, default=4)
    args = ap.parse_args()

    expected = json.loads(EXPECTED.read_text())
    cases = [(src, which, want) for src, by in expected.items() if not src.startswith("_")
             for which, want in by.items() if not args.aeneas or which in args.aeneas]
    with ThreadPoolExecutor(args.jobs) as pool:
        reports = list(pool.map(lambda c: run_check(c[0], c[1]), cases))

    failed = 0
    for (src, which, want), report in zip(cases, reports):
        problems = mismatches(report, want)
        failed += bool(problems)
        print(f"{'ok  ' if not problems else 'FAIL'} {which:8} {src:72} {report['verdict']}")
        for pr in problems:
            print(f"       {pr}")
        if any(pr.startswith("verdict") for pr in problems):
            for r in report.get("reasons", [])[:3]:
                print(f"       {r[:200]}")
        if args.update:
            if isinstance(expected[src][which], dict):
                expected[src][which]["verdict"] = report["verdict"]
            else:
                expected[src][which] = report["verdict"]
    if args.update:
        EXPECTED.write_text(json.dumps(expected, indent=2) + "\n")
    print(f"{len(cases) - failed}/{len(cases)} expectations hold")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
