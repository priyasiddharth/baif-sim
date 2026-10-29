# Fixing the loop-join failure in Aeneas: one guard patch regresses, one matcher arm holds

Follow-up to 2026-10-29-dataset-pinned-and-square-nums.md ("Could not
match the contexts" after a `&mut self` iterator call before a loop).
User asked "is it easy to fix in aeneas itself?". Work done on a scratch
branch of the submodule, `experiment/end-dead-abs-before-loop`, on top of
399081f. Not committed to the pin.

[OBS 2026-10-29] Why the dead abstraction survives until the loop.
`eval_loop` (aeneas/src/interp/InterpLoops.ml:513) first runs
`simplify_dummy_values_useless_abs`, whose `EAbs` branch ends any
endable, parentless abstraction with no live loans. With
`-log-debug InterpBorrows` it visits abs@3 (the `Chars::next` call),
logs "No non-ignored aloans in abs", and still moves on. The reason is
the guard `abs_mut_borrows_loans_in_fixed` (InterpBorrows.ml, just above
`eliminate_ended_shared_loans`): its `AProjBorrows` arm raises `Found`
for *any* intersecting `AProjLoans` on the same symbolic value anywhere
in the context, ignoring the `fixed_abs_ids` set that the docstring and
the sibling `AMutBorrow` arm consult. abs@3 carries
`(s@4 <: Chars<'2>)` and abs@1 (`str::chars`, not fixed) carries
`⌊s@4 <: Chars<'1>⌋`, so abs@3 is never ended.

[OBS 2026-10-29] Patch A (make that arm check `fixed_abs_ids`, 6 lines):
incremental `dune build` 3 s. Fixes every case (fixture, `nth`, remove_Occ
attempts 2–3 now reach the next wall, the stored-`||` Prop/Bool bug), and
the generated loop has no extra inputs. But `make test` regresses:
- `tests/src/static.rs` lines 605–610: internal error in
  `destructure_abs` (InterpBorrows.ml:2084) during a loop join.
- `tests/lean/Iterators.lean` changes: loops in
  `slice_iter_mut_while_early_return*` now take `to_slice_mut_back` /
  `iter_mut_back` as inputs and return the `Array` instead of the
  iterator. Equivalent but a different interface for every user of
  those lemmas.
So that guard is load-bearing beyond its docstring: ending abstractions
earlier changes which abstractions are "fixed" across loops. Reverted.

[OBS 2026-10-29] Patch B (the actual failure point): add one arm to
`MakeMatcher.match_tavalues`, `ASymbolic` case
(aeneas/src/interp/InterpMatchCtxs.ml, after the `AProjLoans` arm):
```ocaml
| ( AEndedProjLoans { proj = _; consumed = []; borrows = [] },
    AEndedProjLoans { proj = _; consumed = []; borrows = [] } ) ->
    [%sanity_check_recover] M.recover M.span (pm0 = pm1);
    { v0 with ty }
```
Rationale: the matcher already accepts the live `AProjBorrows` in the
same abstraction (the `last(self)` variant proved an abstraction holding
`(s@4 <: Chars<'2>)` is matched and is *not* part of the loop interface —
`count_first_loop (s c n i)` with the original binary). An ended loan
projector with nothing left to give back has nothing to match, so
keeping the left value is sound. Build 3 s. Same results as Patch A on
all our cases; loop signature identical to the `last` variant's.
[OPEN] full `make test` on Patch B running at time of writing; result
to be appended here. Until it passes, the claim is "fixes our cases",
not "safe".

[HYP] `SymbolicToPureAbs.ml:946/1028` raise "Not implemented yet" on
`AEndedIgnoredMutBorrow` when an abstraction *is* a loop input/output.
Patch B never reaches that because such an abstraction stays fixed. A
program where the loop body touches the iterator after `next` would.

## Why this matters

The brief's "unsupported" category is softer than it looks: this one was
a missing match arm, 4 lines, found in an afternoon from the trace. Worth
an upstream PR with the fixture as a test — but only after the suite is
green, and the Iterators diff from Patch A shows how easily "fixes" here
change generated interfaces.

## See also

- 2026-10-29-dataset-pinned-and-square-nums.md
- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- ../../loose-ends/parked.md (ended-loan-projector entry)
