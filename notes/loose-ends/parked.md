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
**Why parked:** Workaround known (collect to `Vec<char>` first); not blocking the loop. Fix exists (2026-10-29) in the fork: `aeneas_mod/` submodule, branch `main` = pin + commit 38531ab (rebased from 4f8b688 when the pin moved to de16f3c; pushed to priyasiddharth/aeneas) — see 2026-10-29-aeneas-loop-matcher-fix-experiment.md. Do **not** loosen `abs_mut_borrows_loans_in_fixed` (regresses `static.rs`, changes `Iterators.lean`).
**To resume:** `make test` is green with the matcher arm (116/116, no expected-output changes, 2026-10-29); upstream de16f3c (now the pin) still lacks the arm; open an upstream PR from the fork's `main` with `tests/unsupported/chars_next_before_loop.rs` as a `tests/src/` case; the pristine pin stays until upstream merges.
**Effort estimate:** ~1 h to PR once the suite is green
**References:** 2026-10-29-dataset-pinned-and-square-nums.md, 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md

## Classify raw-pointer effects as unsupported_code in check.py
**Status:** parked 2026-10-29
**Context:** `mbpp_591_swap_List` attempt 1 (`as_mut_ptr` + `ptr::swap`) is `missing_context`, but the translation drops the write: no model of the three axioms can make it correct. Candidate rule: calls to pointer read/write functions → `unsupported_code` with a clear reason.
**Why parked:** One data point; blanket type-based flagging is too blunt.
**To resume:** Find a second case (hand-write fixtures with `ptr::write`/`read`/`copy`, and a pointer-only-as-value case that should stay `missing_context`/`translates`); if the pattern holds, add the rule to `classify_aeneas` and rows to `tests/expected.json`.
**Effort estimate:** ~1 h
**References:** 2026-10-29-swap-list-raw-pointers-become-opaque-values.md

## Memory model for raw pointers in Aeneas (design question)
**Status:** parked 2026-10-29
**Context:** Pointer writes through library calls are lost in translation (`swap_List` attempt 1). Options discussed: global heap (rejected: taxes safe code), local heap + ownership handoff (needs region-end info raw pointers don't have), per-pointer points-to tokens (Verus-style; needs annotations/inference). See 2026-10-29-swap-list-raw-pointers-become-opaque-values.md.
**Why parked:** Aeneas feature work, out of scope for the brief; only needed if unsafe code must be verified.
**To resume:** Check upstream Aeneas issues/PRs and the paper for raw-pointer plans; see how Charon represents `*mut T` deref/offset in LLBC; prototype the token typing of `ptr::swap` by hand in Lean against the generated `swap_List` to see what the Lean side would need.
**Effort estimate:** unknown (research)
**References:** 2026-10-29-swap-list-raw-pointers-become-opaque-values.md
