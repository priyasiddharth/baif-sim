# Where the upstream tests for unsupported Rust live (and how thin they are)

[FACT] Both repos mark expected failures with a `//@ known-failure` header and
       commit the tool's output as a sibling `.out` file.
       → aeneas/tests/README.md:57-75 ; charon/charon/tests/ui.rs:58
       Aeneas' README says Charon-level failures belong in Charon's suite, and
       there is no option for "translates but fails in the backend".

[FACT] Aeneas `tests/src` (≈120 inputs) has 7 known-failure tests:
       raw pointer deref (`raw_pointers.rs`, InterpPaths.ml:197), associated
       types in mutually-recursive traits / GATs (`mutually-recursive-traits.rs`,
       SymbolicToPure.ml:224), higher-ranked ↔ free lifetime constraints
       (3 × `higher_ranked_implied_bounds_*.rs`, TypesAnalysis.ml:994), and two
       `-borrow-check` negatives.

[FACT] Charon `tests/ui` (≈300 inputs) has 18 known-failure tests, of which
       ~7 are genuine unsupported features: coroutines (`simple/coroutine.rs`),
       GATs with `--lift-associated-types` (`associated_types/issue-1068-*`),
       assoc-type expansion depth (`issue-1519-*`), `Box<dyn FnOnce>` and two
       `dyn` vtable panics, matching on an opaque enum. The rest are rustc
       errors, CLI/attribute misuse, or MiniRust interpreter tests. The
       `ui/unsupported/` folder name is misleading (one test now passes, one
       is a plain rustc error).

Verify: `grep -l known-failure aeneas/tests/src/*.rs charon/charon/tests/ui/*.rs charon/charon/tests/ui/*/*.rs`

## Why this matters

No upstream catalogue of unsupported Rust exists; our `tests/unsupported/`
has to be built by hand. The `.out` files are good expected-output fixtures
for the check tool's error classification.

## See also

- ../journal/2026-10/2026-10-28-check-tool-verdicts-and-bugs.md
