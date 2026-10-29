# sim — Rust that Aeneas can translate

notes at: notes

Research notebook in `notes/`, managed with the **better-than-fish** skill
(read `notes/CLAUDE.md` first). "btf notes" / "note this" → write there.

Layout:
- `aeneas/`, `charon/` — submodules, pinned (see `aeneas/charon-pin`). Never patch `aeneas/`.
- `aeneas_mod/` — submodule of our fork (priyasiddharth/aeneas), same base commit plus local patches, branch `loop-matcher-ended-proj-loans`. Select with `--aeneas mod` on `check.py` / `mbpp.py attempt|recheck`, or `AENEAS=mod` in the environment; default is pristine.
- `lakefile.lean` / `lean-toolchain` (root) — shell Lake project so VS Code resolves `import Aeneas` in generated files anywhere in the repo; shares the Aeneas library's built packages.
- `tools/check.py` — Charon → Aeneas → Lean type-check → `#print axioms`, JSON verdict.
- `tools/mbpp.py` + `.claude/skills/mbpp-aeneas/` — generate / test / check / log loop.
- `data/mbpp-rs.json` — pinned snapshot of the MultiPL-E `mbpp-rs` test split (HF revision inside); `fetch` reads it, `snapshot` refreshes it.
- `tests/` — hand-written pass/fail cases. `mbpp/` — recorded attempts.
- `examples/` — self-contained walkthroughs (`loop_join/run.sh`: the `&mut self`-before-loop failure, pristine vs mod, with the patch and trace).
- `notes.md` — the user's raw working notes (not the notebook).
