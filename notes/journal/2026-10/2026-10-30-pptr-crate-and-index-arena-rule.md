# Source-language route for pointers: a `PPtr`/`PointsTo` crate; sharing via index arenas

Pins: aeneas de16f3c, fork ed1312f, charon 373d840, Lean v4.35.0.

[FACT] The Aeneas Lean library models no shared-ownership or interior-
mutability type: no entry for `alloc::rc`, `core::cell` (`Cell`, `RefCell`)
in `aeneas/src/extract/ExtractBuiltinLean.ml`, and no test under
`aeneas/tests/src` uses `Rc` or `RefCell`. Verify: `grep -n
'alloc::rc\|core::cell\|RefCell' aeneas/src/extract/ExtractBuiltinLean.ml;
grep -rl 'Rc<\|RefCell' aeneas/tests/src`. Consequence: `Rc<RefCell<T>>`
programs end in axioms whose types cannot carry the write, the same class as
`ptr::swap` (2026-10-30-missing-context-is-four-things.md, cause (4)).

[FACT] Of the three safe-Rust encodings of sharing and cycles — `Box` (trees
only), `Rc<RefCell<T>>`/`Weak`, and index arenas (`Vec<Node>` + `usize`
handles) — only the arena translates today: `Vec` indexing and index
assignment are in the always-translating core
(idiomatic-rust-fails-on-missing-stdlib-models.md). Lean model = functional
vector; a dangling handle is an out-of-bounds `Result` failure; invariants
are "index < len". Recorded as a generator rule in README Stage 2 §2.
Correction of the user's premise "graphs are not representable in safe
Rust": they are, via `Rc<RefCell>` or arenas; arenas are the only
*translatable* form.

[HYP] Pointer effects can be made visible without changing Aeneas by moving
the tokens into the source language: an ordinary Rust crate with `PPtr<T>`
(wraps `*mut T`) and `PointsTo<T>` (zero-sized, move-only, owns the pointee),
every operation taking and returning tokens, e.g. `swap(p, q, pa, qb) ->
(PointsTo<T>, PointsTo<T>)`; `unsafe` only inside the crate; one hand-written
Lean model per function where `PointsTo` carries the value (`swap : Ptr T →
Ptr T → PointsTo p a → PointsTo q b → Result (PointsTo p b × PointsTo q a)`).
Generated code is plain token threading; the trusted base is the crate's
models, same status as the stdlib models. Returning the token is the
write-back, the role a borrow's backward function plays for `&mut`. Modelled
on Verus `vstd` `PPtr`/`PointsTo` (`Tracked` permissions). Open: aliasing must
be impossible by construction (constructors), existing unsafe code must be
ported, and check.py must translate the crate with the solution (parked crate
input / `--include`). Test: `swap_List` against the crate should reach
`translates` on attempt 1. Not built. README Stage 2 §1.1 holds the write-up.

## See also

- 2026-10-29-swap-list-raw-pointers-become-opaque-values.md (why `ptr::swap`'s
  axiom cannot be filled correctly)
- 2026-10-30-unmodelled-type-in-signature-cannot-be-shimmed.md
- ../../loose-ends/parked.md ("Memory model for raw pointers")

## Smallest arena example (added same day)

[OBS 2026-10-30] `tests/arena_cycle.rs`: `Node { value: u32, next: usize }`,
`Arena { nodes: Vec<Node> }`, `add` pushes and returns the index, `walk`
follows `next` for k hops, `two_cycle` builds 1 → 2 → 1 and walks five hops
(sum 7). Verdict `translates` under both checkouts, zero axioms; Lean `add :
Arena → U32 → Usize → Result (Usize × Arena)` returns the handle with the
updated arena, `walk_loop.body` is `Vec.index` + field reads. Expected rows
added (46/46).
[OBS 2026-10-30] check.py wart found by it: Charon synthesises drop glue for
a local type that owns a `Vec` (`fun_decls` name `[…, Impl, Builtin
DropGlue]`, `is_local`), Aeneas emits nothing for it, and the report listed
`Arena::{impl}: missing (aeneas_error)` while the verdict stayed
`translates`. Fixed: `local_functions` skips names with a `Builtin` segment
(`is_compiler_generated`), `name_to_str` renders the segment as `{DropGlue}`;
two unit tests (27 total). Verify: `tools/check.py tests/arena_cycle.rs --human`
lists exactly three functions.
