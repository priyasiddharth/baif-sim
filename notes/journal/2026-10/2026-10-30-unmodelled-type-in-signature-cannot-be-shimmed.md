# An unmodelled type pinned by the signature cannot be shimmed in Rust

Pins: aeneas de16f3c, fork ed1312f, charon 373d840, Lean v4.35.0. Both
checkouts behave the same here.

[FACT] remove_Occ attempt 4 (`fn remove_Occ(s: String, ch: String) ->
String`) leaves exactly three axioms under both checkouts:
`alloc::string::String::new`, `String::push`, and `impl Deref<str> for
String`::deref (reached implicitly by `s.chars()`). The Aeneas Lean library
declares `alloc::string::String` opaque, mapped to Lean's `String`
(`aeneas/backends/lean/Aeneas/Std/Alloc/String.lean`, `rust_type … (body :=
.opaque)`), and models exactly one string function, `core::str::{str}::chars`
(`aeneas/src/extract/ExtractBuiltinLean.ml:1321`); no `String` method and no
other `str` method has a model. Verify: `grep -n 'alloc::string\|core::str'
aeneas/src/extract/ExtractBuiltinLean.ml`;
`grep -n '^axiom' mbpp/aeneas_pristine/mbpp_11_remove_Occ/attempt-4/lean/Mbpp11RemoveOcc.lean`.

[FACT] Why the skill's shim rule does not apply. A shim replaces a library
call with safe Rust over *modelled* primitives (`count_ones` → bit loop,
`sort_unstable_by` → selection sort over `Vec` indexing). `String` has no
modelled primitive, so a shim for `new`/`push` must itself call an
`alloc::string` constructor, and reading the input needs the deref. A local
`MyString(Vec<char>)` with in-file definitions makes the *algorithm*
axiom-free (attempt 4 already works on a `Vec<char>`), but the two
conversions at the signature boundary — read a `String` in, build a `String`
out — stay axioms: 3 → at best 2, never 0, while the signature says `String`.
With a `Vec<char>` signature the function translates today. The signature is
fixed by the dataset tests (`candidate(String::from("hello"), …) ==
String::from("heo")`) and by the brief's "preserve its behaviour"; the harness
enforces it (`mbpp.py test` compiles solution + tests).
Also: the shim policy entered the skill on 2026-10-30, two days after the
remove_Occ attempts (2026-10-28), so no attempt has yet run under it.

[FACT] The Lean-side fix is small: since the Rust `String` is Lean's
`String`, `new` is `ok ""`, `push` is `ok (s.push c)`, and the deref returns
the string as a `Str`. Three one-line models in the fork's library (or
upstream) would make attempt 4 translate unchanged.

[OPEN] Policy question raised with the user, not decided: when an
unmodelled type is pinned by the signature, should the skill (a) isolate it —
algorithm on a local type, public function a thin wrapper, axioms confined to
the two conversions, per-function report shows the core clean, verdict still
`missing_model`; (b) add Lean models in the fork; (c) leave it as the
recorded limit? Discussion stopped before a choice.

## See also

- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- 2026-10-30-missing-context-is-four-things.md (the shim rule's origin)
- ../../durable/opaque-functions-become-axioms-or-lean-lib-models.md
