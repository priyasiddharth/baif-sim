# sim — Rust that Aeneas can translate

notes at: notes

Research notebook in `notes/`, managed with the **better-than-fish** skill
(read `notes/CLAUDE.md` first). "btf notes" / "note this" → write there.

Layout:
- `aeneas/`, `charon/` — submodules, pinned (see `aeneas/charon-pin`). Never patch `aeneas/`.
- `aeneas_mod/` — submodule of our fork (priyasiddharth/aeneas), branch `main` = the `aeneas/` pin plus our local patches (rebase them when the pin moves; move `aeneas/` and `charon/` together, per `aeneas/charon-pin`). Select with `--aeneas mod` on `check.py` / `mbpp.py attempt|recheck`, or `AENEAS=mod` in the environment; default is pristine.
- `lakefile.lean` / `lean-toolchain` (root) — shell Lake project so VS Code resolves `import Aeneas` in generated files anywhere in the repo; shares the Aeneas library's built packages.
- `tools/check.py` — Charon → Aeneas → Lean type-check → `#print axioms`, JSON verdict.
- `tools/mbpp.py` + `.claude/skills/mbpp-aeneas/` — generate / test / check / log loop.
- `data/mbpp-rs.json` — pinned snapshot of the MultiPL-E `mbpp-rs` test split (HF revision inside); `fetch` reads it, `snapshot` refreshes it.
- `tests/` — hand-written pass/fail cases. `mbpp/` — recorded attempts.
- `tests/expected.json` + `tests/run_expected.py` — expected `check.py` verdict per input and checkout (pristine, mod); the runner exits 1 on any mismatch. Add a row when adding a fixture; `--update` rewrites it from a run.
- `.github/workflows/check.yml` — CI: Charon + both Aeneas via Nix (hacl Cachix + cached Nix store), Lean lib via elan/lake (cached `.lake`), then `tests/run_expected.py`.
- `examples/` — self-contained walkthroughs (`loop_join/run.sh`: the `&mut self`-before-loop failure, pristine vs mod, with the patch and trace).
- `notes.md` — the user's raw working notes (not the notebook).
