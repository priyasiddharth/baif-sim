# sim — Rust that Aeneas can translate

notes at: notes

Research notebook in `notes/`, managed with the **better-than-fish** skill
(read `notes/CLAUDE.md` first). "btf notes" / "note this" → write there.

## Setup

- **Clone:** `git clone --recurse-submodules git@github.com:priyasiddharth/baif-sim.git`. Submodules (`.gitmodules`): `aeneas/` (upstream pin de16f3c, never patched), `charon/` (373d840 = `aeneas/charon-pin`), `aeneas_mod/` (our fork priyasiddharth/aeneas, branch `main` = pin + local patches, ed1312f).
- **Pins:** rustc `nightly-2026-09-17` (`charon/rust-toolchain`), Lean `v4.35.0` (`aeneas/backends/lean/lean-toolchain`). Moving the pin: check out `aeneas/` and `charon/` together (per `charon-pin`), rebase the fork's commits, rebuild all three.
- **Build (Nix, what CI does):** `nix build -L "path:$PWD/aeneas#charon" -o result-charon`, `… "path:$PWD/aeneas#aeneas" -o result-aeneas`, `… "path:$PWD/aeneas_mod#aeneas" -o result-aeneas-mod`; symlink `result-charon/bin/*` into `charon/bin/`, and each `result-*/bin/aeneas` into `aeneas/bin/` and `aeneas_mod/bin/`. The "Build Charon and Aeneas" step of `.github/workflows/check.yml` is the reference.
- **Build (from source):** `make build-dev` in `charon/`, then in `aeneas/` (opam deps; `aeneas/charon` must be a symlink to `../charon`). Fork: `cd aeneas_mod/src && dune build && cp -f _build/default/main.exe ../bin/aeneas` (`aeneas_mod/charon -> ../charon`). Details: `notes/durable/how-to-translate-a-rust-file-to-lean-and-check-it.md`.
- **Lean library:** `cd aeneas/backends/lean && lake exe cache get && lake build` (elan installs the toolchain). The fork shares it: `ln -s ../../../aeneas/backends/lean/.lake aeneas_mod/backends/lean/.lake`.
- **Host tools:** python3 (stdlib only), rustup with the pinned nightly (for `mbpp.py test`), elan/lake; Nix optional.
- **Checkout selection:** `--aeneas pristine|mod|PATH` on `check.py` / `mbpp.py`, or `AENEAS=mod`; default pristine. Every `check.json` records it under `versions.aeneas_checkout`.
- **Verify:** `python3 -m unittest discover -s tests -p 'test_*.py'` (25 tests, no toolchain), then `python3 tests/run_expected.py` (44 expectations, both checkouts). Smoke: `tools/check.py tests/compile_ok1.rs --human`.
- **Editor:** open the repo root in VS Code; the root `lakefile.lean` / `lean-toolchain` form a shell Lake project so `import Aeneas` resolves in generated files anywhere in the repo (shares the library's built packages).

Layout:
- `aeneas/`, `charon/` — pinned submodules (see Setup). Never patch `aeneas/`.
- `aeneas_mod/` — fork submodule carrying our Aeneas patches (see Setup for selection and pin moves).
- `lakefile.lean` / `lean-toolchain` (root) — shell Lake project for the editor (see Setup).
- `tools/check.py` — Charon → Aeneas → Lean type-check → `#print axioms`, JSON verdict: translates / unsupported_code / missing_context (rustc or Charon could not see a definition) / missing_model (an axiom for an opaque item; raw-pointer signatures get a note) / invalid_rust / toolchain_problem.
- `tools/mbpp.py` + `.claude/skills/mbpp-aeneas/` — generate / test / check / log loop.
- `data/mbpp-rs.json` — pinned snapshot of the MultiPL-E `mbpp-rs` test split (HF revision inside); `fetch` reads it, `snapshot` refreshes it.
- `tests/` — hand-written pass/fail cases. `mbpp/aeneas_pristine/`, `mbpp/aeneas_mod/` — recorded MBPP attempts, one tree per Aeneas checkout (same attempt numbers; `mbpp.py attempt` writes both).
- `tests/expected.json` + `tests/run_expected.py` — expected `check.py` result per input and checkout (pristine, mod): a verdict, or `{verdict, reasons, noted_axioms, axioms}`; the runner exits 1 on any mismatch. Add a row when adding a fixture; `--update` rewrites the verdicts from a run. `tests/test_check.py` — unit tests of the classification functions (no toolchain): `python3 -m unittest discover -s tests -p 'test_*.py'`.
- `.github/workflows/check.yml` — CI: Charon + both Aeneas via Nix (hacl Cachix + a file binary cache of the three result closures, saved with actions/cache keyed on the submodule commits), Lean lib via elan/lake (cached `.lake`), the fork's test suite (`aeneas-tests` flake check = `make test`, plus `lake build` of `aeneas_mod/tests/lean` sharing the pristine `.lake`), then `tests/run_expected.py`. Warm run ~6 min, cold ~30.
- `examples/` — self-contained walkthroughs (`loop_join/run.sh`: the `&mut self`-before-loop failure, pristine vs mod, with the patch and trace).
- `notes.md` — the user's raw working notes (not the notebook).
