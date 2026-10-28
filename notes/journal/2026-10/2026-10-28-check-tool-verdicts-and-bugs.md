# check.py: verdict design and the bugs the first real inputs exposed

[OBS 2026-10-28] `tools/check.py` runs Charon → Aeneas → `lake env lean` →
`#print axioms` per function and prints JSON: `versions`, per-stage
`status` (ok/partial/failed/skipped), per-function status
(translated/sorry/missing/axiom + `error_ref` into the stage diagnostics),
`axioms` (lean name, rust name, origin stdlib/dependency/local/library,
used_by), `reasons`, `verdict`. Exit code = verdict: 0 translates,
1 unsupported_code, 2 missing_context, 3 invalid_rust, 4 toolchain_problem.
`invalid_rust` was added because rustc rejections fit none of the brief's
three categories. Verdict = most severe reason found.

[OBS 2026-10-28] All six `tests/` cases give the intended verdict
(compile_ok1 → 0; raw_ptr, async_fn → 1; ref_mul, missing_dep → 2;
invalid → 3). `toolchain_problem` (4) has no test case yet. [OPEN]

[OBS 2026-10-28] Bugs found by the first MBPP run, all fixed the same day:
- rustc lints (`dead_code`, `non_snake_case`) were parsed as Charon
  warnings → false `unsupported_code`. MBPP functions are non-`pub` and
  keep names like `differ_At_One_Bit_Pos`. Fix: pass `-Awarnings`;
  verified Charon's own "not supported" warnings are not lints and still
  print.
- Lean "`x` is not a field of structure …" was `toolchain_problem`; it
  means Aeneas emitted a call the Lean lib lacks → now `missing_context`.
- Doc-header regex missed type axioms (no `:` after `]`), multi-line
  `@[rust_fun\n "..."]` attributes, and `axiom\n  name` → axioms showed as
  origin "library" with no Rust name.
- Closure `call_once`/`call_mut` share one span → duplicate function rows.
Attempt-1 verdicts were re-derived with `mbpp.py recheck` and committed;
the wrong originals stay in git history.

[OBS 2026-10-28] Later the same day: with the Aeneas Lean library not built,
the Lean stage was `skipped` but the verdict could still be `translates`
(no type-check, no `#print axioms`; only file-declared `axiom`s were seen).
Now a skipped Lean stage is a `toolchain_problem` reason; missing `lake` is
a clean skip; a missing `charon`/`aeneas` binary still emits a JSON report
(exit 4) instead of a bare stderr line. Also on the user's call: `result.json`
and `problem.json` dropped — `check.json` is the result record (written by
`mbpp.py` from check.py's stdout), `status.json` holds provenance + attempt
index.

[HYP] Matching LLBC functions to Lean decls by source span will break on
trait-impl methods and generated code; untested beyond free functions and
closures.

## See also

- ../../empirical/exit-codes-do-not-reflect-translation-status.md
- 2026-10-28-mbpp-loop-first-three-problems.md
