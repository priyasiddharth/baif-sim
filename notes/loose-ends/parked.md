# Parked explorations

## Split mbpp-aeneas skill into generic loop + dataset adapter
**Status:** parked 2026-10-28
**Context:** The generate → test-immediately → check → delta-log → commit → revise loop is generic. MBPP-specific: `fetch`/`snapshot` (HF MultiPL-E rows API → `data/mbpp-rs.json`, field names), `split_tests` (leading `}`), the "solution + tests.rs main" harness, `mbpp/` layout. Since 2026-10-29 the adapter's "read rows" is just the pinned JSON, which makes the split easier.
**Why parked:** User: "at some point"; three problems done first.
**To resume:** `tools/loop.py` taking a problem dir (`prompt.rs`, `tests.rs`, a test command) + `tools/sources/mbpp.py`; generic skill `aeneas-loop`. Keep `mbpp.py` CLI as a thin wrapper.
**Effort estimate:** ~2 h
**References:** 2026-10-28-mbpp-loop-first-three-problems.md

## check.py: crate and selected-lines input
**Status:** parked 2026-10-28
**Context:** Brief asks how a crate, one file, or a few lines would be handled. Tool does single files as lib crates. Crate = `charon cargo --preset=aeneas`; lines = wrap in a stub crate with the needed surrounding items.
**Why parked:** Single-file case needed first for the MBPP loop.
**To resume:** add `--crate DIR` (run `charon cargo` in it) and `--snippet` (template a lib with the pasted lines; report which names failed to resolve as missing context).
**Effort estimate:** ~half-day
**References:** how-to-translate-a-rust-file-to-lean-and-check-it.md

## No test case for verdict 4 (toolchain_problem)
**Status:** resolved 2026-10-28 — `tests/unsupported/or_in_loop_bool.rs` (Aeneas emits a `Prop` for a stored `||` inside a loop; Lean fails to type-check; exit 4). Charon-panic and version-mismatch variants still untested.
**References:** 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md

## Report the stored-`||`-in-loop Prop/Bool bug upstream (Aeneas)
**Status:** parked 2026-10-28
**Context:** `skip = a || b` inside a loop body → `let b ← if a then ok true else ok (b)` with `b : Prop`. Minimal repro is `tests/unsupported/or_in_loop_bool.rs` (standalone / in `if` / in tuple variants all translate, so the loop is required). Aeneas 399081f.
**Why parked:** Workaround known (branch instead of store); not blocking.
**To resume:** check `aeneas/src` for where `||` is translated (search for the short-circuit `if … then ok true else` shape in the pure AST passes) to see if a `decide` is missing in the loop-body path, then file an issue with the fixture.
**Effort estimate:** ~30 min to file; unknown to fix
**References:** 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md

## More hand-written unsupported cases
**Status:** parked 2026-10-28
**Context:** `tests/unsupported/` has 5 cases. Not covered: unions, inline asm, `dyn Trait`, closures returning refs, GATs, higher-ranked lifetime bounds, `unsafe` beyond raw-pointer deref.
**Why parked:** MBPP loop took priority.
**To resume:** port the upstream known-failure inputs (where-the-upstream-unsupported-feature-tests-are.md) into `tests/unsupported/`, run `check.py` on each, record verdicts.
**Effort estimate:** ~1 h
**References:** where-the-upstream-unsupported-feature-tests-are.md

## Brief parts 2 and 3
**Status:** parked 2026-10-28
**Context:** Part 2 (repair skill): `failures.md` + `error_ref` locations are the input; attempt-2 diffs are three worked examples. Part 3 (first-attempt strategy): the stdlib-allowlist hypothesis in idiomatic-rust-fails-on-missing-stdlib-models.md; comparison metric = first-attempt pass rate on held-out MBPP with/without the guide.
**Why parked:** Part 1 tooling first.
**To resume:** generate `docs/aeneas-rust-guide.md` from `ExtractBuiltinLean.ml` + the supported-core list; rerun `/mbpp-aeneas` on problems 7–16 with the guide in context; compare `report`.
**Effort estimate:** ~half-day each
**References:** idiomatic-rust-fails-on-missing-stdlib-models.md

## Report the ended-loan-projector loop-match failure upstream (Aeneas)
**Status:** parked 2026-10-29
**Context:** A value taken through `Chars::next` before a loop leaves a region abstraction whose child is `AEndedProjLoans`; `MakeMatcher.match_tavalues` (`aeneas/src/interp/InterpMatchCtxs.ml`, `ASymbolic` case) has no arm for it, so `match_ctx_with_target` fails with "Could not match the contexts" even though the two contexts are identical. Minimal repro `tests/unsupported/chars_next_before_loop.rs`; trace command in 2026-10-29-dataset-pinned-and-square-nums.md. Aeneas 399081f.
**Why parked:** Workaround known (collect to `Vec<char>` first); not blocking the loop.
**To resume:** Check whether upstream HEAD already handles `AEndedProjLoans` in that match (grep the constructor in `InterpMatchCtxs.ml`), else file an issue with the fixture and the log excerpt. Ask whether ended abstractions are meant to be collapsed before `compute_loop_entry_fixed_point`.
**Effort estimate:** ~30 min to file
**References:** 2026-10-29-dataset-pinned-and-square-nums.md, 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
