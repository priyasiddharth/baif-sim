# Sessions

## 2026-10-28
- **Session:** (unnamed)
- **Theme:** Bootstrap the repo (aeneas + charon submodules, builds, Lean lib), build `tools/check.py`, run the MBPP generate/test/check loop on three problems, bootstrap this notebook.
- **Key outputs:**
  - `durable/how-to-translate-a-rust-file-to-lean-and-check-it.md`, `durable/opaque-functions-become-axioms-or-lean-lib-models.md`, `durable/where-the-upstream-unsupported-feature-tests-are.md`
  - `empirical/exit-codes-do-not-reflect-translation-status.md`, `empirical/idiomatic-rust-fails-on-missing-stdlib-models.md`
  - `journal/2026-10/2026-10-28-check-tool-verdicts-and-bugs.md`, `journal/2026-10/2026-10-28-mbpp-loop-first-three-problems.md`, `journal/2026-10/2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md`
  - Code: `tools/check.py`, `tools/mbpp.py`, `.claude/skills/mbpp-aeneas/SKILL.md`, `tests/` (incl. the first verdict-4 fixture `or_in_loop_bool.rs`), `mbpp/` (attempts committed per problem; `mbpp_11_remove_Occ` unresolved at 4 attempts, ceiling `missing_context`).
  - `loose-ends/parked.md` — 6 entries (verdict-4 fixture resolved; Aeneas `||` bug to report upstream).
- **Critical corrections:**
  - User asked "are you using better-than-fish notes?" — I was not; the plugin is installed but its skill was never surfaced in the session's skill list, and I had read "btf notes" as the repo's `notes.md`. Misled by not checking the plugin cache. Notebook bootstrapped at `notes/` on the user's choice.
  - First MBPP attempt-1 verdicts were wrong (`toolchain_problem`/`unsupported_code`) because `check.py` treated rustc lints as Charon warnings; fixed, rechecked, originals left in git history.
  - User rejected `example.rs` as a test name (also a Lean keyword) → `compile_ok1.rs`.
  - User: "why are you creating result.json, it should be created by check.py" — it duplicated `check.json`; removed, `status.json` now only indexes attempts.
  - User asked for a clear unsupported reason instead of a bare "Unimplemented" — the parser had been discarding the item name, use site, stdlib source line and the crash; all now reported.
- **Status:** complete (part 1 tooling + 3 MBPP problems); parts 2–3 parked.
- **Next-session pickup candidates:**
  - loose-ends: "Split mbpp-aeneas skill into generic loop + dataset adapter" (user flagged).
  - loose-ends: "Brief parts 2 and 3" — stdlib-allowlist guide experiment.
  - Uncommitted at session end: `tools/`, `tests/`, `.claude/`, `CLAUDE.md`, `notes/`, `notes.md` edits.
