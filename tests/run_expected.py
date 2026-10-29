#!/usr/bin/env python3
"""Run tools/check.py on every input in tests/expected.json, for each Aeneas
checkout listed there, and compare the verdict with the expected one.

  tests/run_expected.py                  all inputs, all checkouts
  tests/run_expected.py --aeneas mod     one checkout only
  tests/run_expected.py --update         rewrite expected.json with what ran

Exit 0 when every verdict matches, 1 otherwise. Prints one row per input.
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


def verdict(src, aeneas):
    p = subprocess.run([sys.executable, str(CHECK), str(ROOT / src), "--aeneas", aeneas],
                       capture_output=True, text=True)
    try:
        report = json.loads(p.stdout)
    except json.JSONDecodeError:
        return "no_report", [p.stderr.strip()[-300:]]
    return report["verdict"], report.get("reasons", [])


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
        results = list(pool.map(lambda c: verdict(c[0], c[1]), cases))

    failed = 0
    for (src, which, want), (got, reasons) in zip(cases, results):
        ok = got == want
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {which:8} {src:72} {got}" + ("" if ok else f" (expected {want})"))
        if not ok:
            for r in reasons[:3]:
                print(f"       {r[:200]}")
        if args.update:
            expected[src][which] = got
    if args.update:
        EXPECTED.write_text(json.dumps(expected, indent=2) + "\n")
    print(f"{len(cases) - failed}/{len(cases)} verdicts as expected")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
