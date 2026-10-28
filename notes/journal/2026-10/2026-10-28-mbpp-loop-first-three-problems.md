# MBPP generate → test → check loop, first three problems

[OBS 2026-10-28] Built `tools/mbpp.py` (fetch / test / attempt / recheck /
log / report) and the `mbpp-aeneas` skill. Problems come from MultiPL-E
`mbpp-rs` (HF `nuprl/MultiPL-E`, 354 rows) via the datasets-server rows
API: `prompt` = doc comment + signature, `tests` = a `main` of
`assert_eq!`s prefixed by the `}` that closes the prompt. Tests compile
with Charon's pinned nightly so test and translation use one rustc.

[OBS 2026-10-28] Loop discipline that the user asked for, now enforced:
unit tests run immediately after every codegen; `attempt` refuses to
record a failing version (exit 2, no directory); each attempt appends to
one accumulating `mbpp/<name>/failures.md` (reasons, delta vs previous
attempt: resolved / still failing / new, unified code diff) and commits
the new program together with the log.

[OBS 2026-10-28] Results — 0/3 first attempt, 3/3 at attempt 2:

| problem | attempt 1 | attempt 2 |
|---|---|---|
| mbpp_3_is_not_prime | `(2..).take_while().any()` → iterator models missing, `&isize*&isize` axiom | `while i*i <= n` |
| mbpp_4_heap_queue_largest | `sort_unstable_by`, `truncate` missing | selection sort by index + `push` |
| mbpp_6_differ_At_One_Bit_Pos | `count_ones` missing | `x & (x-1) == 0` (+ `isize::MIN` guard) |

Our reading: the generator's default style is the problem, not Rust
semantics — see idiomatic-rust-fails-on-missing-stdlib-models.md.

[OPEN] Skill needs splitting into a generic loop + MBPP adapter before a
second dataset is added (parked in loose-ends).

[OPEN] Datasets to consider next: Vericoding (2.3k Rust/Verus problems,
needs Verus syntax stripped), VeruSAGE-Bench (systems code, needs heavy
context). Neither is Aeneas-specific.

## See also

- 2026-10-28-check-tool-verdicts-and-bugs.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
