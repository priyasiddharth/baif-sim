# Dataset pinned to a revision; mbpp_8_square_nums passes at attempt 2; loop-join failure traced

[OBS 2026-10-29] Pushed the repo to `github.com/priyasiddharth/baif-sim`.
GitHub had pre-created `main` with a one-line README; merged it with
`--allow-unrelated-histories` rather than force-push, renamed local
`master` → `main`, deleted remote `master`. README is still a stub.

[OBS 2026-10-29] User asked whether to submodule "the MBPP project".
Answer: no — what we use is not the `google-research/mbpp` repo
(Python-only) nor the `nuprl/MultiPL-E` GitHub repo (translation tooling)
but one 354-row split of the HF *dataset* `nuprl/MultiPL-E`, which is
parquet behind LFS for ~20 languages × 2 benchmarks. The real gap was
pinning: `fetch` read the rows API unpinned, so a dataset update could
silently change prompts/tests behind a recorded attempt. Done instead:
`data/mbpp-rs.json` = all rows + HF revision `28441b6` (lastModified
2025-07-15) + snapshot date; `mbpp.py fetch` reads it (`--remote` for
the API), `mbpp.py snapshot` refreshes it; every `status.json` source
now carries the revision. The five recorded problems were byte-identical
to the snapshot before re-stamping.
Verify: `python3 -c "import json;print(json.load(open('data/mbpp-rs.json'))['revision'])"`.

[OBS 2026-10-29] mbpp_8_square_nums (`Vec<isize> -> Vec<isize>`, offset 3):
attempt 1 `nums.iter().map(|x| x * x).collect()` → `missing_context`,
axioms `Iterator::map`, `Map::next`, `Mul<&isize> for &isize`; Lean also
reports `map`/`collect` "is not a field of structure
core.iter.traits.iterator.Iterator". Attempt 2 index `while` + `Vec::new`
/`push` + `x * x` on the owned element → `translates`, no axioms. Exactly
the pattern of problems 3/4/6/12; predicted before running.

[OBS 2026-10-29] Tally: 6 problems, 0/6 first attempt, 5/6 at attempt 2,
`mbpp_11_remove_Occ` unresolved at 4. The non-string repair is now
routine enough that attempt 1 is only measuring the generator's default
style, which is the point of the part-3 allowlist experiment.

[OBS 2026-10-29] "Could not match the contexts" (remove_Occ attempts 2–3)
traced with Aeneas logging. Minimal repro `tests/unsupported/chars_next_before_loop.rs`
(14 lines, verdict 1): `let c = match ch.chars().next() { Some(c) => c, None => return 0 }`
then a `while` over an unrelated `Vec<char>`. The same function with
`c` taken from `ch.chars().collect::<Vec<char>>()[0]` translates.
Run: `aeneas/bin/aeneas -backend lean X.llbc -dest D -log InterpJoin -log-debug InterpMatchCtxs`.
What the log shows:
- `compute_loop_entry_fixed_point` (InterpLoopsFixedPoint.ml) finds a
  fixed point; `match_ctx_with_target` (InterpJoin.ml:1348) then joins
  the entry context with it and must match the result back onto the
  fixed point. The two dumped contexts are textually identical apart
  from one fresh symbolic id (`n -> s@19` vs `s@21`).
- The loop-entry environment carries three abstractions from before the
  loop: abs@0 = `Deref<str> for String` (`SL@1(s@3 : str)`), abs@1 =
  `str::chars` (`⌊s@4 <: Chars<'1>⌋`), abs@3 = `Chars::next`
  (continuation `FunCall(abs_id@3)[(Option<char>)]`) holding
  `@ended_ignored_mut_borrow((s@4 <: Chars<'2>), ended_aproj_loans (_))`.
- `pop_first_matching_abs` matches abs@0 and abs@1, then fails on abs@3
  against its own copy: `MakeMatcher.match_tavalues` (InterpMatchCtxs.ml:570,
  `ASymbolic` case) has arms for `AProjBorrows` and `AProjLoans` only;
  the child here is `AEndedProjLoans` (printed `ended_aproj_loans`,
  Values.ml:499) and falls to `| _ -> craise_recover "Unreachable"`,
  which `pop_first_matching_abs` swallows as "no matching abs". The
  `check_equiv:false` matcher's `match_aended_ignored_mut_borrow` itself
  is fine (takes meta from the left).
So the 2026-10-28 [HYP] was right about *which* value (the one through
`Chars::next`) and slightly wrong about *why*: it is not that the borrow
of `ch` is alive, it is that the `next` call's abstraction contains an
ended loan projector the loop matcher cannot handle. abs@3 exists
because `next` takes `&mut Chars` and returns an owned `Option<char>`;
region `'2` ended right after the call, which turns its loan projector
into `AEndedProjLoans`, and nothing ever removes the abstraction before
the loop.
[SUPERSEDED same day] I first wrote that the `Vec<char>` route works
"because `collect` consumes the iterator, so the abstractions end before
the loop". Wrong: the passing log has the same three abstractions at
loop entry (Deref, chars, and abs@2 for `collect`). The difference is the
*shape*: `collect(self)` takes `Chars` by value, so abs@2 holds a live
borrow projector `(s@4 <: Chars<'2>)` (`AProjBorrows`, which the matcher
handles); `next(&mut self)` borrows the temporary `Chars` mutably, the
borrow's region ends after the call, and what remains is
`@ended_ignored_mut_borrow(…, ended_aproj_loans)`. Misled by not
rereading the passing context before explaining it.
Confirmed by varying the receiver mode alone (same loop, same `s`):
`ch.chars().last()` (`fn last(self)`) → join succeeds, verdict
`missing_context` only (no model for `Chars::last`);
`ch.chars().nth(0)` (`fn nth(&mut self, _)`) → "Could not match the
contexts" at the `while`, like `next`. Rule for generated code: do not
call a `&mut self` iterator method on a temporary before a loop; use a
by-value consumer (`collect`, `last`) or index into a `Vec`. [OPEN] whether
Aeneas intends to collapse such ended abstractions before entering a loop
or whether this is simply an unimplemented matcher arm — parked as an
upstream question.

## See also

- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- 2026-10-28-mbpp-loop-first-three-problems.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
