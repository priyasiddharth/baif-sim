---
name: mbpp-aeneas
description: Generate Rust for MBPP problems, run the supplied unit tests, check translation to Lean with tools/check.py, and iterate on the check report until it translates. Use when asked to run the MBPP/Aeneas loop, e.g. "/mbpp-aeneas 3" or "/mbpp-aeneas mbpp_3_is_not_prime".
---

# MBPP → Rust → Aeneas loop

Argument: a count (`3` = the first 3 problems, `--offset K` to start later) or
problem names. All commands run from the repo root.

Aeneas checkout: by default `check.py` runs the pristine upstream pin
(`aeneas/`). If the argument includes `--aeneas mod` (or `AENEAS=mod` is set),
pass `--aeneas mod` to every `attempt` / `recheck` call so the patched fork
(`aeneas_mod/`) is used; `check.json` records which one ran under
`versions.aeneas_checkout`, and the attempt commit message carries
`(aeneas: mod)`. Say which checkout was used in the final summary.

## Steps per problem

1. **Fetch** (skip if `mbpp/<name>/prompt.rs` exists):
   `tools/mbpp.py fetch 3` or `tools/mbpp.py fetch <name>`.
   Read `mbpp/<name>/prompt.rs` (doc comment + signature) and `tests.rs`.
   If `mbpp/<name>/failures.md` exists, read it too: it is the history of
   earlier attempts and their failures.

2. **Generate.** Write the complete function to a scratch file, keeping the
   signature from `prompt.rs` exactly. No `main`, no `#[test]`, no extra
   crates. On attempt 1 write it the way you normally would: do not pre-apply
   Aeneas workarounds, so attempt 1 measures first-attempt translation.

3. **Unit tests, immediately.** Right after writing any version of the code,
   run `tools/mbpp.py test <name> <file.rs>`. If it fails, fix the code and
   rerun. Never move on with a version that fails the tests; `attempt` refuses
   to record one anyway (exit 2).

4. **Record + check.** `tools/mbpp.py attempt <name> <file.rs> --commit`.
   This reruns the tests, runs `tools/check.py` (Charon → Aeneas → Lean
   type-check → `#print axioms`), stores the program and reports under
   `mbpp/<name>/attempt-N/`, appends a section to `mbpp/<name>/failures.md`
   (check reasons, the delta from the previous attempt — resolved / still
   failing / new — and the code diff), and commits the new program together
   with the updated failure log.
   - Exit 0 / `"outcome": "pass"`: report **passed on attempt N** (attempt 1 =
     first-attempt pass) and move to the next problem.
   - Otherwise read the printed `check` block (`verdict`, `reasons`,
     `functions`, `axioms`) and `mbpp/<name>/failures.md`. Revise the code to
     circumvent those failures, then go back to step 3. Keep the same
     signature and behaviour. Do not hide code behind stubs, `unsafe`, or by
     deleting functionality.
   - Stop after 5 attempts and report the problem as unresolved.

## What the verdicts mean

- `unsupported_code`: Charon or Aeneas rejected a construct (message + line in
  `reasons`/`check.json`). Rewrite that construct in supported Rust: index
  loops instead of iterator chains/closures, plain integer arithmetic instead
  of trait-dispatched ops on references, `while` loops, owned values.
- `missing_context`: an `axiom` is listed or the Lean library lacks a method,
  usually a `core`/`alloc` item with no model (e.g. `Vec::sort`,
  `Iterator::take_while`, `count_ones`, `u32 * &u32`). Avoid that API; compute
  it by hand. Use `*r` for arithmetic on references.
- `invalid_rust` / `toolchain_problem`: the Rust did not compile or the tools
  broke; `reasons` says which.

## Finish

`tools/mbpp.py report` prints, per problem, whether it passed, the number of
attempts, and whether attempt 1 passed. Summarize that table to the user and
note which constructs caused failures.
