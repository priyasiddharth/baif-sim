# What happens to a function Charon does not translate the body of

[FACT] Charon assigns every item an opacity: Transparent (full), Foreign (default
       for other crates incl. core/alloc/std: signature only, except enums and
       all-public structs), Opaque (signature only), Invisible (nothing).
       → charon/charon/src/ast/meta.rs:21 (`enum ItemOpacity`)
       → charon/docs/what_charon_translates.md (selection algorithm, patterns)
       Controlled by `--include` / `--opaque` / `--exclude` / `--extract-opaque-bodies`;
       `#[charon::opaque]` can only make items more opaque.

[FACT] An untranslated body is explicit in the LLBC: `Body::Opaque`
       (also `Missing`, `Extern`, `Intrinsic`, `Error`).
       → charon/charon/src/ast/bodies.rs:40 (`enum Body`), variant at :70

[FACT] Aeneas then checks the name against `builtin_funs_map`, the list generated
       from the Lean library (`aeneas/src/extract/ExtractBuiltinLean.ml`;
       map at ExtractBuiltin.ml:928). On the list → the call targets the Lean
       model, nothing is emitted (aeneas/src/Translate.ml:947-958). Off the
       list → "opaque non-builtin" (llbc/LlbcAstUtils.ml:60-75) and:
       - without `-split-files`: an `axiom` (extract/ExtractBase.ml:1413) plus
         the warning at Main.ml:778 ("extracted external, unknown definitions");
       - with `-split-files`: a `*External_Template.lean` entry to fill in.

[FACT] The axiom only postulates a constant of the signature's type, e.g.
       `axiom U32.Insts.CoreOpsArithMulShared0U32U32.mul : Std.U32 → Std.U32 → Result Std.U32`.
       It is consistent (the type is inhabited) but says nothing about the
       value, so no spec about a caller can be proved past that call, and
       `#print axioms caller` lists it. The file also gets `noncomputable section`.
       Shared borrows vanish from the type (`&u32` → `Std.U32`).

## Why this matters

"Missing context" in the check tool = this path. The fix differs by origin:
`core::`/`alloc::` name → add a Lean model or avoid the API; another crate
→ `--include` it; your own crate → it was made opaque on purpose. Read the
`@[rust_fun "..."]` attribute on the axiom to tell them apart.

## See also

- how-to-translate-a-rust-file-to-lean-and-check-it.md
- ../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
