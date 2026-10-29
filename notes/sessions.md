# Sessions

## 2026-10-28
- **Session:** (unnamed)
- **Theme:** Bootstrap the repo (aeneas + charon submodules, builds, Lean lib), build `tools/check.py`, run the MBPP generate/test/check loop on three problems, bootstrap this notebook.
- **Key outputs:**
  - `durable/how-to-translate-a-rust-file-to-lean-and-check-it.md`, `durable/opaque-functions-become-axioms-or-lean-lib-models.md`, `durable/where-the-upstream-unsupported-feature-tests-are.md`
  - `empirical/exit-codes-do-not-reflect-translation-status.md`, `empirical/idiomatic-rust-fails-on-missing-stdlib-models.md`
  - `journal/2026-10/2026-10-28-check-tool-verdicts-and-bugs.md`, `journal/2026-10/2026-10-28-mbpp-loop-first-three-problems.md`, `journal/2026-10/2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md`, `journal/2026-10/2026-10-28-sort-matrix-nested-vec-passes-without-swap-clone.md`
  - Root `lakefile.lean` shell project (VS Code resolves `import Aeneas`; toolchain-by-workspace-folder gotcha recorded in the durable how-to).
  - Code: `tools/check.py`, `tools/mbpp.py`, `.claude/skills/mbpp-aeneas/SKILL.md`, `tests/` (incl. the first verdict-4 fixture `or_in_loop_bool.rs`), `mbpp/` (attempts committed per problem; `mbpp_11_remove_Occ` unresolved at 4 attempts, ceiling `missing_context`).
  - `loose-ends/parked.md` — 6 entries (verdict-4 fixture resolved; Aeneas `||` bug to report upstream).
- **Critical corrections:**
  - User asked "are you using better-than-fish notes?" — I was not; the plugin is installed but its skill was never surfaced in the session's skill list, and I had read "btf notes" as the repo's `notes.md`. Misled by not checking the plugin cache. Notebook bootstrapped at `notes/` on the user's choice.
  - First MBPP attempt-1 verdicts were wrong (`toolchain_problem`/`unsupported_code`) because `check.py` treated rustc lints as Charon warnings; fixed, rechecked, originals left in git history.
  - User rejected `example.rs` as a test name (also a Lean keyword) → `compile_ok1.rs`.
  - User: "why are you creating result.json, it should be created by check.py" — it duplicated `check.json`; removed, `status.json` now only indexes attempts.
  - User asked for a clear unsupported reason instead of a bare "Unimplemented" — the parser had been discarding the item name, use site, stdlib source line and the crash; all now reported.
  - User: "why did you need to create problem.json" — raw dataset row, unused by the loop; dropped, provenance moved to `status.json`.
  - User asked whether the axioms check works when Aeneas can't be found — it silently passed with the Lean stage skipped; fixed.
- **Status:** complete (part 1 tooling; 5 MBPP problems: 4 pass @2, 1 unresolved); parts 2–3 parked. All committed (`ac5fcae`, `8f5ad1a`, `ed0ce53` + per-attempt mbpp commits).
- **Next-session pickup candidates:**
  - loose-ends: "Split mbpp-aeneas skill into generic loop + dataset adapter" (user flagged).
  - loose-ends: "Brief parts 2 and 3" — stdlib-allowlist guide experiment; 5 attempt-2 diffs are the worked repair examples.
  - loose-ends: report the stored-`||`-in-loop Prop/Bool bug upstream (fixture ready).

## 2026-10-29
- **Session:** (unnamed, continuation)
- **Theme:** Publish repo to GitHub; pin the MBPP dataset; sixth problem; trace the loop-join failure with Aeneas logging; try fixing it in Aeneas.
- **Key outputs:**
  - `journal/2026-10/2026-10-29-dataset-pinned-and-square-nums.md`
  - `data/mbpp-rs.json` (354 rows, HF revision 28441b6) + `mbpp.py fetch`/`snapshot` reading/writing it; revision stamped into every `status.json`.
  - `mbpp/mbpp_8_square_nums`: pass at attempt 2 (iterator `map`/`collect` → index loop).
  - Remote: `origin/main` (merged GitHub's README initial commit; `master` removed).
  - `journal/2026-10/2026-10-29-aeneas-loop-matcher-fix-experiment.md` — guard patch regresses upstream tests; one matcher arm fixes all our cases and passes the full Aeneas suite (116/116, no expected-output changes). Patch now lives in the fork submodule `aeneas_mod/` (branch `loop-matcher-ended-proj-loans`, pushed); `aeneas/` restored pristine; `check.py --aeneas pristine|mod` + `mbpp.py --aeneas` select the checkout and record it.
  - `tests/unsupported/chars_next_before_loop.rs` (14-line repro of "Could not match the contexts"); the 2026-10-28 [HYP] on remove_Occ attempts 2–3 confirmed and sharpened: missing `AEndedProjLoans` arm in the loop-context matcher.
- **Critical corrections:** none from the user. User interrupted an unasked "fetch the next row" to ask about submoduling the dataset first; answer was "pin, don't submodule" and they took it.
  - `journal/2026-10/2026-10-29-pins-moved-to-de16f3c-fork-main-carries-fix.md` — pins moved to aeneas de16f3c / charon 373d840, fork `main` = pin + fix, all verdicts unchanged.
  - `journal/2026-10/2026-10-29-swap-list-raw-pointers-become-opaque-values.md` — raw-pointer probe: `missing_context` but the write is lost; reclassification parked.
  - Aeneas fork: second matcher arm (ended shared loans) + upstream-style regression test `tests/src/loop-ended-loans.rs` (fork `main` ee1c669, `make test` 117/117).
  - CI: `.github/workflows/check.yml` + `tests/expected.json`/`tests/run_expected.py` (38 verdicts locally). Five runs: cold 30 min; whole-store caching failed (GC + broken tar restore); replaced by a file binary cache of the result closures with `trusted=1`; warm run 5.5 min (Nix step 70 s).
- **Status:** complete. Tally 0/6 first attempt (+1 deliberate pointer probe), 6/7 at attempt 2, remove_Occ unresolved.
- **Next-session pickup candidates:** unchanged from 2026-10-28 (skill split; part-3 allowlist experiment; `||`-in-loop upstream report) plus the new ended-loan-projector upstream report. Next untried rows: offset 4 `mbpp_9_find_Rotations`, offset 7 `mbpp_14_find_Volume`.
