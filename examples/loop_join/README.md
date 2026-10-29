# Loop-join failure: `&mut self` iterator call before a loop

A 14-line Rust function that pristine Aeneas (commit 399081f) rejects with
`Could not match the contexts`, a one-line change that makes it pass, and
the four-line Aeneas fix in `aeneas_mod/`.

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
