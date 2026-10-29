# How to translate a Rust file to Lean and actually check the result

[FACT] Translation is two tools: Charon (Rust → LLBC) then Aeneas (LLBC → Lean).
       For one file, run Charon from the file's directory with a relative path:
       → aeneas/documentation/getting-started.md:15-30 (crate form)

       ```bash
       charon/bin/charon rustc --preset=aeneas --dest-file=out/foo.llbc -- --crate-type=lib --edition=2021 -Awarnings foo.rs
       aeneas/bin/aeneas -backend lean out/foo.llbc -dest out -namespace Foo
       ```
       `--preset=aeneas` sets the options Aeneas expects
       → charon/charon/src/options.rs:560 (`Preset::Aeneas` branch).

[FACT] A successful Aeneas run is not a type-checked result. The generated file
       does `public import Aeneas`, so checking needs the Aeneas Lean library
       built (`cd aeneas/backends/lean && lake exe cache get && lake build`;
       Lean + Mathlib pinned at v4.35.0 → aeneas/backends/lean/lean-toolchain,
       lakefile.lean:5). Then:

       ```bash
       printf '\n#print axioms Foo.bar\n' >> out/Foo.lean
       (cd aeneas/backends/lean && lake env lean /abs/path/out/Foo.lean)
       ```
       Only `propext`, `Classical.choice`, `Quot.sound` are standard; anything
       else listed is a hole in the translation.

[FACT] Two ways the generated Lean fails to parse even though Aeneas exited 0:
       - crate name is a Lean keyword (`example.rs` → `namespace example`);
         fix with `-namespace <Capitalised>`.
       - the source path is copied into a `/-- ... -/` doc comment, so a path
         containing `/-` opens a nested comment ("unterminated comment");
         run Charon with a relative path.
       Both observed 2026-10-28; `tools/check.py` applies both workarounds.

[FACT] Generated files outside `aeneas/backends/lean` fail in VS Code with
       "unknown module prefix 'Aeneas'" (and the server falls back to elan's
       default toolchain, v4.28.0 here). The repo-root `lakefile.lean` is a
       shell project that `require`s aeneas from that path with
       `packagesDir := "aeneas/backends/lean/.lake/packages"`, so any `.lean`
       under the repo resolves `import Aeneas` with no second Mathlib fetch.
       Open the repo root as the VS Code workspace: the Lean 4 extension picks
       the *toolchain* by running elan in the workspace folder but finds the
       *lakefile* by walking up from the file, so with a parent folder open it
       ran v4.28.0's `lake` against this workspace and died in proofwidgets'
       lakefile (`Unknown constant Lake.Hash.ofHashable`). Confirmed fixed by
       opening the repo root (2026-10-28). Verify with
       `lake env lean mbpp/<p>/attempt-N/lean/<File>.lean` from the root.
       (Set up 2026-10-28; `lake build` at root reported "Already
       decompressed 9031 file(s)".)

[FACT] `-split-files` (aeneas/src/Main.ml:129, Config.ml:221) writes
       `FunsExternal_Template.lean` / `TypesExternal_Template.lean` for
       external definitions you must model by hand (aeneas/src/Translate.ml:1870ff;
       README.md:155-165). Incompatible with `-borrow-check` (Main.ml:490).

[FACT] Two Aeneas checkouts exist (since 2026-10-29): `aeneas/` is the pristine
       upstream pin and is never patched; `aeneas_mod/` is our fork
       (priyasiddharth/aeneas, branch `loop-matcher-ended-proj-loans`) at the same
       base commit plus local fixes. `tools/check.py --aeneas pristine|mod|PATH`
       picks the binary (default `$AENEAS` or pristine); `mbpp.py attempt|recheck`
       pass `--aeneas` through. Every `check.json` says which ran under
       `versions.aeneas_checkout`. Rebuild the fork after pulling with
       `cd aeneas_mod/src && dune build && cp -f _build/default/main.exe ../bin/aeneas`
       (needs the `aeneas_mod/charon -> ../charon` symlink, gitignored).

## Why this matters

"It translated" is three independent checks (Charon, Aeneas, Lean). The
check tool exists because each of the first two can succeed while the
result is unusable. See opaque-functions-become-axioms-or-lean-lib-models.md.

## See also

- opaque-functions-become-axioms-or-lean-lib-models.md
- ../empirical/exit-codes-do-not-reflect-translation-status.md
