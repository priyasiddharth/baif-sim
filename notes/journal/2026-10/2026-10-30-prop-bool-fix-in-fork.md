# Stored `||` in a loop: fixed in the fork via the type-annotation micro-pass

Pins: aeneas de16f3c, fork ed1312f (= ee1c669 + this), charon 373d840,
rustc nightly-2026-09-17, Lean v4.35.0.

[FACT] Cause. Aeneas prints `==` on scalars as Lean `=`, a `Prop`. Lean
inserts `decide` when the expected type is known (`f : … → Result Bool`
returning `ok (seen = total)` translates). In `let b ← if seen2 = 1#i32 then
ok true else ok (seen2 = total)` the expected type of the bound expression
is unknown, Lean infers `Prop`, and the later `ok (seen2, b)` fails
("Application type mismatch … Prop … Bool"). Verify: hand-editing the else
branch of the generated `OrInLoopBool.lean` to `ok ((seen2 = total) : Bool)`
and running `lake env lean` on it exits 0 under the pristine pin.

[FACT] Upstream state (checked 2026-10-30 with `gh pr view 1374`): issue
#1279; PR #1374 "Lean backend: Type comparisons as `Bool`" is OPEN against
main, not in de16f3c (commit 0e15bf80, only on `origin/cezar/loops` and
`origin/cezar/unicode-ident`). It wraps every Lean comparison in
`extract_binop` as `(a = b : Bool)` and prints Bool `¬` as `!`. The one
review comment (sonmarcho) asks to annotate only when the boolean is not an
`if` condition, through the existing type-annotation micro-pass. Its source
hunks apply cleanly to the fork; its regenerated tests do not (they come
from a newer branch with raw-pointer test files we lack).

[OBS 2026-10-30] Implemented the reviewer's variant in the fork
(`aeneas_mod/src/pure/PureMicroPassesAnnots.ml`): in `visit_App`, the
`Binop` case returns `need_annot = (backend = Lean && comparison && ty =
hole)` so `mk_type_annot` wraps the comparison; in `visit`, the `Switch`
discriminant is visited with `TLiteral TBool` when the body is an `If`
(known type, so conditions stay bare) and with the hole for a `Match`.
`ExtractBase.ml`: `unop_name (Not None)` prints `!` instead of `¬`.
`make test`: 117/117, 7 committed outputs change, every changed line is
`¬ b` → `! b` or `: Bool` on the operands of `||` inside `massert`
(`git -C aeneas_mod show ed1312f --stat`). Regression tests: upstream's
`issue-1279-comparison-prop-type.rs` (verbatim from 0e15bf80) and our loop
case `issue-1279-stored-comparison-in-loop.rs`; both outputs type-check;
`tests/lean/script.sh` regenerated the lakefile.

[OBS 2026-10-30] Effect on our suite: `tests/unsupported/or_in_loop_bool.rs`
mod → `translates` (pristine still `toolchain_problem`); remove_Occ
attempts 2–3 under mod → `missing_model` (String::new/push, Deref<str>),
attempt 4 unchanged; `tests/expected.json` 44/44 after moving exactly those
two rows. The fixture is the first case where the fork, not a rewrite by
the generator, closes a gap.

[OPEN] Offer the variant upstream on issue #1279 (PR #1374 is the broader
form). Whether `massert` should take the annotated `Bool` or a `Prop` is for
upstream to decide; both type-check today.

## See also

- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md (the bug's discovery)
- 2026-10-29-aeneas-loop-matcher-fix-experiment.md (the fork's first patch)
- ../../loose-ends/parked.md
