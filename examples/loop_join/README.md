# Loop-join failure: `&mut self` iterator call before a loop

A 14-line Rust function that pristine Aeneas (the pinned commit in `aeneas/`, 399081f when found, still at de16f3c) rejects with
`Could not match the contexts`, a one-line change that makes it pass, and
the two matcher arms that fix it in `aeneas_mod/`.

```
examples/loop_join/run.sh            # verdicts + loop signatures + the patch
examples/loop_join/run.sh --trace    # also the matcher trace at the failure
```

## The two programs

`fails.rs` and `passes.rs` differ in one line:

```rust
let c = match ch.chars().next() { ... }   // fails:  fn next(&mut self)
let c = match ch.chars().last() { ... }   // passes: fn last(self)
```

followed by a `while` loop over an unrelated `Vec<char>` that only reads `c`.
`nth(0)` fails like `next`; `collect::<Vec<char>>()[0]` passes like `last`.
The receiver mode of an iterator call made *before* the loop is the whole
story.

## What Aeneas does with a loop

Aeneas interprets the function symbolically. Its environment holds values,
borrows, loans, and *region abstractions*: records of borrows that are still
outstanding, left behind by every call that took or returned a reference.

To translate a loop it needs one environment shape valid at the loop head on
every iteration. `compute_loop_entry_fixed_point`
(`aeneas/src/interp/InterpLoopsFixedPoint.ml`) evaluates the body
repeatedly, *joining* the entry state with each back-edge state, until the
shape stabilises. Then `match_ctx_with_target`
(`aeneas/src/interp/InterpJoin.ml:1348`) joins the real entry state with that
fixed point and must *match* the result back onto the fixed point, pairing
every abstraction with one on the other side. If any abstraction cannot be
paired it raises `Could not match the contexts` (`InterpJoin.ml:1571`).

## What the trace shows (`run.sh --trace`)

At the loop head, both programs still carry three abstractions from before
the loop: one for `Deref<str> for String`, one for `str::chars()`, and one for
the iterator call. The first two pair fine in both programs. The third differs:

| program | abstraction content for the iterator call | matcher |
|---|---|---|
| `passes.rs` (`last(self)`) | `(s@4 <: Chars<'2>)`, a **live borrow projector** | has an arm: pairs |
| `fails.rs` (`next(&mut self)`) | `@ended_ignored_mut_borrow((s@4 <: Chars<'2>), ended_aproj_loans (_))`: the `&mut` borrow of the temporary ended after the call, leaving an **ended loan projector** | no arm: falls to `Unreachable`, swallowed as "no matching abs" |

The two contexts being matched are *textually identical* (only a fresh
symbolic id on `n` differs). The failure is purely a missing case in
`MakeMatcher.match_tavalues`, `ASymbolic` branch
(`aeneas/src/interp/InterpMatchCtxs.ml` ≈ line 570), which handles
`AProjBorrows` and `AProjLoans` but not `AEndedProjLoans`.

## The loop invariant, annotated (`fails.rs`, from `out/fails.pristine.log`)

This is `src_ctx` in the `About to match:` block: the fixed point Aeneas
computed for the `while` head. `joined_ctx` (entry state joined with the
fixed point) differs from it in exactly one token: `n -> s@19` vs `s@21`.

```
# Ended regions: { 3, 4, 5 }        regions that have already ended; 0,1,2 are live
  s^1  : Vec<char> -> s@0           input vector, a symbolic value: unknown contents
  ch^2 : String    -> SL@0(s@1)     ch is a *shared loan* SL@0: someone holds a &ch (abs@0)
  c^3  : char      -> s@9           the char from next(): opaque symbolic value
  n^11 : i32       -> s@19          counter: fresh symbolic value each iteration (the join)
  i^12 : usize     -> 0usize        index: concrete 0 at entry (this dump is the entry side)

  abs@0 {regions={0}}               call Deref<str> for String: &'0 String -> &'0 str
    SB@0(^0)                          holds shared borrow SB@0 of ch (ends region 0 => ch usable again)
    SL@1(s@3 : str, _)                lends out the str it returned (SL@1), s@3 = its contents
  abs@1 {regions={1}}               call str::chars: &'1 str -> Chars<'1>
    SB@1(^2)                          holds shared borrow SB@1 of that str
    ⌊s@4 <: Chars<'1>⌋                *live loan projector* on s@4, the Chars value it returned:
                                      "whoever holds s@4 is borrowing from me"
  abs@3 {regions={2}}               call Chars::next: &'2 mut Chars<'1> -> Option<char>
    @ended_ignored_mut_borrow(        the &mut borrow of the temporary Chars (s@4) has ENDED
        (s@4 <: Chars<'2>),           child: a live borrow projector on s@4 (region 2 side)
        ended_aproj_loans (_))        given-back: the Chars handed back when the &mut ended;
                                      its loan projector is ENDED and has nothing to give back
    _                                 the Option<char> output: ignored (already consumed into c)
```

Reading it as an invariant: at every iteration `s`, `c` are fixed values,
`n` and `i` vary, `ch` is still lent to abs@0, abs@0 still lends the `str`
to abs@1, abs@1 still lends the `Chars` (s@4) to abs@3, and abs@3 is a
finished `&mut` call whose borrow has been returned. The loop body touches
none of abs@0..3; they are dead weight that Aeneas has not yet collected.

`passes.rs` reaches the same head with abs@2 for `last(self)` instead:
```
  abs@2 {regions={2}} { (s@4 <: Chars<'2>), _ }   plain live borrow projector, no &mut wrapper
```

## The missing match

`match_ctx_with_target` must pair every abstraction of `joined_ctx` with
one of `src_ctx`. Pairing = recursively matching their avalues with
`MakeMatcher.match_tavalues`. Trace (`run.sh --trace`):

```
paired:   abs@0      SB + SL on both sides: arms exist
paired:   abs@1      SB + ⌊AProjLoans⌋:     arms exist
unpaired: abs@3
  match_abstractions: matching values
  - value0: @ended_ignored_mut_borrow((s@4 <: Chars<'2>), ended_aproj_loans (_))   AEndedIgnoredMutBorrow: arm exists (line ~517)
  - value1: (same)
  borrows
  - value0: (s@4 <: Chars<'2>)        child, AProjBorrows: arm exists (line ~572)
  - value1: (same)
  Matching symbolic avalues
  - value0: ended_aproj_loans (_)     given_back, AEndedProjLoans: NO ARM
  - value1: ended_aproj_loans (_)        -> `| _ -> craise_recover "Unreachable"`
distinct: Could not find a matching abs in right environment
```

So the matcher gets two levels deep into abs@3, successfully, and dies on
the innermost value even though both sides print identically. The
`[%craise_recover]` is caught by `pop_first_matching_abs`, which treats it
as "this candidate does not match", runs out of candidates, and raises
`Distinct`, which surfaces as `Could not match the contexts`.

## The fix (in `aeneas_mod/`, branch `loop-matcher-ended-proj-loans`)

One arm, between the `AProjLoans` arm and the catch-all:

```ocaml
| ( AEndedProjLoans { proj = _; consumed = []; borrows = [] },
    AEndedProjLoans { proj = _; consumed = []; borrows = [] } ) ->
    [%sanity_check_recover] M.recover M.span (pm0 = pm1);
    { v0 with ty }
```

Both sides are ended projectors with nothing left to give back, so there is
nothing to match; keep the left value. With it, `fails.rs` translates with
the same loop signature as `passes.rs`, `count_first_loop (s c n i)`, and the
leftover abstraction stays outside the loop interface. The full Aeneas test
suite passes (116 invocations, no expected-output changes).

## The fix that looks right but is wrong

The simplifier that runs before every loop (`simplify_dummy_values_useless_abs`)
*visits* the dead abstraction, finds no live loans, and still keeps it, because
`abs_mut_borrows_loans_in_fixed` (`InterpBorrows.ml`) refuses whenever the
abstraction's borrow projector intersects a loan projector anywhere, ignoring
the fixed-abstraction set it is documented to check. Making it honour that set
also fixes this example, but ends abstractions earlier elsewhere: `make test`
then crashes on `tests/src/static.rs` and rewrites `tests/lean/Iterators.lean`
(loops gain `to_slice_mut_back`/`iter_mut_back` inputs). That guard is
load-bearing; leave it.

## Where this came from

MBPP problem `remove_Occ` (`mbpp/mbpp_11_remove_Occ/`, attempts 2 and 3), via
`tests/unsupported/chars_next_before_loop.rs`. Notebook entries:
`notes/journal/2026-10/2026-10-29-dataset-pinned-and-square-nums.md` and
`notes/journal/2026-10/2026-10-29-aeneas-loop-matcher-fix-experiment.md`.
