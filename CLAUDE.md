# sim — Rust that Aeneas can translate

notes at: notes

Research notebook in `notes/`, managed with the **better-than-fish** skill
(read `notes/CLAUDE.md` first). "btf notes" / "note this" → write there.

Layout:
- `aeneas/`, `charon/` — submodules, pinned (see `aeneas/charon-pin`).
- `lakefile.lean` / `lean-toolchain` (root) — shell Lake project so VS Code resolves `import Aeneas` in generated files anywhere in the repo; shares the Aeneas library's built packages.
- `tools/check.py` — Charon → Aeneas → Lean type-check → `#print axioms`, JSON verdict.
- `tools/mbpp.py` + `.claude/skills/mbpp-aeneas/` — generate / test / check / log loop.
- `tests/` — hand-written pass/fail cases. `mbpp/` — recorded attempts.
- `notes.md` — the user's raw working notes (not the notebook).
