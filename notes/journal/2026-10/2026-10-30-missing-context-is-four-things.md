# `missing_context` is four different things; stdlib bodies cannot be translated today

Pins: aeneas de16f3c / fork ee1c669, charon 373d840, rustc nightly-2026-09-17,
Lean v4.35.0. All runs under the pristine checkout unless said otherwise.

## Why unmodelled stdlib compiles while missing user code does not

[FACT] Rustc resolves `Iterator::map` because `core` ships with the
toolchain; what is missing is a *Lean* definition. Charon skips bodies of
foreign-crate items by default (`charon/charon/src/options.rs`:
`extract_opaque_bodies`, "Usually we skip the bodies of foreign methods"),
Aeneas prints an `axiom` for any opaque function it has no library mapping
for (`aeneas/src/extract/ExtractBase.ml:1413` `| Builtin -> Some "axiom"
| Declared -> Some "axiom"`), and Lean accepts axioms. So the hole only
shows in `#print axioms`, which is why check.py runs it. Missing *user*
code fails earlier: rustc name resolution (E0405/E0412/E0425/…), before
Charon.
Verify: `tools/check.py mbpp/aeneas_pristine/mbpp_8_square_nums/attempt-1/mbpp_8_square_nums.rs --human`
and `grep -n "^axiom" mbpp/aeneas_pristine/mbpp_8_square_nums/attempt-1/lean/Mbpp8SquareNums.lean`.

## `--extract-opaque-bodies` makes every program fail

[OBS 2026-10-30] `tools/check.py <file> --charon-arg=--extract-opaque-bodies`
on five recorded programs: square_nums/heap_queue/swap_List attempt 1 →
`unsupported_code`; is_not_prime attempt 1 → `toolchain_problem` ("Aeneas:
Internal error: please file an issue"); square_nums attempt 2 (Vec
new/push/len/index only, `translates` without the flag) → `unsupported_code`,
47 reasons. Charon: "Thread panicked when extracting body." Aeneas rejects
bodies in 20 `core`/`alloc` files the program never names (`raw_vec`,
`MaybeUninit`, `core_simd/masks.rs`, `str/pattern.rs`, `fmt/builders.rs`,
`panic/location.rs`): "Breaks/Continue to outer loops are not supported
yet". LLBC for the minimal program: 11 declarations / 161 KB → ~1509 / 24 MB.
Reproduce: `charon/bin/charon rustc --preset=aeneas --extract-opaque-bodies
--print-llbc -- <file> --crate-type=lib | grep -c "^fn"`.

[FACT] Decision: keep the flag off. The brief asks to distinguish unsupported
code from missing context; with the flag every verdict becomes "unsupported
code inside core", which measures Aeneas's coverage of the standard library,
not the Rust the agent wrote. Opaque library functions + hand-written models
are the design Aeneas is built around (upstream CI never sets the flag:
`aeneas/.github/workflows/ci.yml`). Targeted `--include=<item>` for one
small pure body remains possible through `--charon-arg` if ever wanted.

## Two routes to a `missing_context` reason from Aeneas/Lean

[FACT] Route 1, axioms: `#print axioms` lists a non-standard axiom;
check.py maps it to the Rust name via the `rust_fun` attribute and
`axiom_origin` classifies by leading crate (`core`/`alloc`/`std` → "stdlib",
input crate → "local", else "dependency"). Reason text "no Lean model for
standard-library item: …". Fires for free functions and impl methods with
opaque bodies: `Vec::truncate`, `count_ones`, `ptr::swap`, `Mul` on `&isize`,
`Map::next`, and for provided trait methods as `<trait>.<method>.default`.

[FACT] Route 2, Lean type error "`map` is not a field of structure
`core.iter.traits.iterator.Iterator`". Occurs only for methods of a trait
Aeneas treats as *builtin* (mapped by `ExtractBuiltin.ml`
`builtin_trait_decls_map` to a hand-written structure). Aeneas does not
declare the trait in the output; it generates the `impl_def` instance with
one field per method the program used (`next := …`, `map := …`,
`collect := …`, see `Mbpp8SquareNums.lean` lines 57–75), but the library
structure `aeneas/backends/lean/Aeneas/Std/Core/Iter.lean:86` has only
`next`, `step_by`, `enumerate`, `take`. The source says why: "adding more
fields like rev leads to a circularity" and "TODO: collect" — a field whose
type mentions an adapter whose own instance refers back to `Iterator`
cannot be in the same Lean structure (dictionary passing needs a definition
order; Rust's trait checker does not). A user-defined trait never hits this:
Aeneas generates structure and instance together from the same program.
Minimal repro (6 lines): `struct Up(u32); impl Iterator for Up { type Item
= u32; fn next(&mut self) -> Option<u32> {…} } fn f(mut u: Up) -> bool {
u.any(|x| x > 3) }` → route 2; replace the body with `u.next()` →
translates. Both routes fire on square_nums attempt 1 (map/collect by
route 2, `map.default`/`Map::next`/`Mul` by route 1). In MBPP so far:
route 2 = `map`, `collect`, `take_while`, `any`, `sum`; route 1 = the other
17 reasons.

## The four things behind exit 2

[FACT] (1) *Missing context*: rustc cannot resolve a name, or Charon says
opaque/`--include`. Fix: supply items/flags. Never seen in MBPP (single
files, no deps).
[FACT] (2) *Missing model*: route 1 axiom whose type carries the whole
effect (`Self → F → Result (Map Self F)`; `&mut self` threaded back as an
output). Fix: write the model in the Lean library, or avoid the API. 17/22
MBPP reasons.
[FACT] (3) *Encoding gap*: route 2. A model alone cannot fix it; the
library's trait encoding must change (break the record: small `Iterator`
with `next`, provided methods as functions over it, as the source comment
suggests). From the user's side it behaves like unsupported code.
[FACT] (4) *Unmodellable axiom*: route 1 axiom whose Rust effect is on
state absent from the type. `core.ptr.swap : MutRawPtr T → MutRawPtr T →
Result Unit`; the Vec is neither input nor output, `RawPtr` is a
placeholder (`Aeneas/Std/RawPtr.lean`: `structure RawPtr … where v : T`,
"We don't really use raw pointers for now … once we have separation
logic"), so every filling makes `swap_List` the identity — type-checks,
clean `#print axioms`, refuted by the Rust tests. The axiom is generated by
Aeneas from the signature, not hand-written; `core::ptr::swap` has no entry
in `ExtractBuiltinLean.ml` (only `core::ptr::alignment::*`). Members of
this class: writes through raw pointers (`ptr::write/swap/copy/replace/
drop_in_place`, `*p = x`), interior mutability (`Cell::set`,
`RefCell::borrow_mut`), `static mut`, I/O — everything the borrow checker
does not track. Fix: Aeneas pointer semantics (parked memory-model
question), not a model.

[SUPERSEDED → next paragraph] Proposed check.py split: keep `missing_context`
for (1); new `missing_model` for (2); report (3) as `unsupported_code` with
the library structure named; flag (4) by a signature rule ("stdlib axiom
taking `MutRawPtr`/`ConstRawPtr` … returning nothing that carries the
pointee") as a separate outcome.

[FACT 2026-10-30] Decision (user): merge (4) into (2). The tool can tell
(1), (2), (3) apart from evidence it has — rustc error codes, an axiom in
`#print axioms`, a "not a field of structure" error — but (4) differs from
(2) only in whether a correct model *could* exist, a fact about Rust
semantics that no pipeline output states. The pointer-signature rule is a
guess at it, misses interior mutability and `static mut`, and would claim a
distinction that was not checked (the brief: say what was actually checked).
So: three verdict causes. (4) survives only as a per-axiom *note* on the
report entry when the signature mentions `MutRawPtr`/`ConstRawPtr` ("type
may not carry the effect"), verdict unchanged. Why I was misled: I let the
swap_List human judgement ("no model can be correct") look like something
the tool could compute. Moves five `tests/expected.json` verdicts (the
attempt-1 iterator cases) when implemented; see loose-ends.

## Implemented (same day)

[OBS 2026-10-30] check.py now emits `missing_model` (exit 5, least severe)
for axioms, keeps `missing_context` (2) for rustc/Charon visibility, and
reports "is not a field of structure `core.`/`alloc.`/`std.`…" as
`unsupported_code` ("library trait structure lacks the method (no model can
be added from outside)"). Axioms whose declaration text mentions
`MutRawPtr`/`ConstRawPtr` carry `note: "type may not carry the effect…"`,
verdict unchanged. Fixtures: `tests/unsupported/user_trait_any.rs`
(unsupported_code, both checkouts), `tests/user_trait_next.rs`
(translates), `tests/unsupported/raw_ptr_value.rs` (missing_model, note on
both axioms). `tests/expected.json`: 44 rows, 44/44; moved exactly the
predicted six (ref_mul both; chars_next_before_loop mod; loop_join/fails
mod; loop_join/passes both; remove_Occ attempt-4 both; swap_List attempt-1
both → missing_model). Rechecked all seven problems under both trees:
square_nums and is_not_prime attempt 1 become `unsupported_code` (route 2
outranks the axioms), the other attempt-1 verdicts `missing_model`; attempt
2 verdicts unchanged. Skill: "What the verdicts mean, and what to do" per
verdict and sub-cause; for a modellable stdlib axiom the generator writes a
local safe shim with the same behaviour (user's choice), falling back to an
inline rewrite; raw-pointer note → must-rewrite.
[OBS 2026-10-30] Pre-existing wart seen while testing: a Lean error message
in `reasons` can have the following `#print axioms` lines glued on ("…
'UserTraitAny.past_three' depends on axioms: […]"); the verdict is right,
the text is noisy. Not fixed.

## See also

- 2026-10-29-swap-list-raw-pointers-become-opaque-values.md (the probe and
  the memory-model discussion)
- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
- ../../loose-ends/parked.md ("Classify raw-pointer effects", "Memory model")
