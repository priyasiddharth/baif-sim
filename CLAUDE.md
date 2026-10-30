# sim — Rust that Aeneas can translate

notes at: notes

Research notebook in `notes/`, managed with the **better-than-fish** skill
(read `notes/CLAUDE.md` first). "btf notes" / "note this" → write there.

Layout:
- `aeneas/`, `charon/` — submodules, pinned (see `aeneas/charon-pin`). Never patch `aeneas/`.
- `aeneas_mod/` — submodule of our fork (priyasiddharth/aeneas), branch `main` = the `aeneas/` pin plus our local patches (rebase them when the pin moves; move `aeneas/` and `charon/` together, per `aeneas/charon-pin`). Select with `--aeneas mod` on `check.py` / `mbpp.py attempt|recheck`, or `AENEAS=mod` in the environment; default is pristine.
- `lakefile.lean` / `lean-toolchain` (root) — shell Lake project so VS Code resolves `import Aeneas` in generated files anywhere in the repo; shares the Aeneas library's built packages.
- `tools/check.py` — Charon → Aeneas → Lean type-check → `#print axioms`, JSON verdict: translates / unsupported_code / missing_context (rustc or Charon could not see a definition) / missing_model (an axiom for an opaque item; raw-pointer signatures get a note) / invalid_rust / toolchain_problem.
- `tools/mbpp.py` + `.claude/skills/mbpp-aeneas/` — generate / test / check / log loop.
- `data/mbpp-rs.json` — pinned snapshot of the MultiPL-E `mbpp-rs` test split (HF revision inside); `fetch` reads it, `snapshot` refreshes it.
- `tests/` — hand-written pass/fail cases. `mbpp/aeneas_pristine/`, `mbpp/aeneas_mod/` — recorded MBPP attempts, one tree per Aeneas checkout (same attempt numbers; `mbpp.py attempt` writes both).
- `tests/expected.json` + `tests/run_expected.py` — expected `check.py` result per input and checkout (pristine, mod): a verdict, or `{verdict, reasons, noted_axioms, axioms}`; the runner exits 1 on any mismatch. Add a row when adding a fixture; `--update` rewrites the verdicts from a run. `tests/test_check.py` — unit tests of the classification functions (no toolchain): `python3 -m unittest discover -s tests -p 'test_*.py'`.
- `.github/workflows/check.yml` — CI: Charon + both Aeneas via Nix (hacl Cachix + a file binary cache of the three result closures, saved with actions/cache keyed on the submodule commits), Lean lib via elan/lake (cached `.lake`), the fork's test suite (`aeneas-tests` flake check = `make test`, plus `lake build` of `aeneas_mod/tests/lean` sharing the pristine `.lake`), then `tests/run_expected.py`. Warm run ~6 min, cold ~30.
- `examples/` — self-contained walkthroughs (`loop_join/run.sh`: the `&mut self`-before-loop failure, pristine vs mod, with the patch and trace).
- `notes.md` — the user's raw working notes (not the notebook).
