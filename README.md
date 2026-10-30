# baif-sim

## Setup

Build and tool setup (clone with submodules, pins, Nix or source builds, Lean library, verification) is in [CLAUDE.md § Setup](CLAUDE.md#setup). CI is the executable usage of `check.py`: [.github/workflows/check.yml](.github/workflows/check.yml) builds Charon, both Aeneas checkouts and the Lean library, then runs [tests/run_expected.py](tests/run_expected.py) over [tests/expected.json](tests/expected.json) under both checkouts.

Policy and configuration we work under:

* **Single `.rs` files**, compiled as a lib crate. Crate and selected-lines input are parked ([notes/loose-ends/parked.md](notes/loose-ends/parked.md)). Example input: [tests/compile_ok1.rs](tests/compile_ok1.rs).
* **Pristine Aeneas is the reference; the fork is an experiment.** `aeneas/` is never patched; fixes go to `aeneas_mod/` and are selected with `--aeneas mod` (or `AENEAS=mod`). Every MBPP attempt is recorded under both: [mbpp/aeneas_pristine/](mbpp/aeneas_pristine), [mbpp/aeneas_mod/](mbpp/aeneas_mod). Where the two disagree: the [tests/unsupported/chars_next_before_loop.rs](tests/unsupported/chars_next_before_loop.rs) rows in `tests/expected.json`; walkthrough [examples/loop_join/run.sh](examples/loop_join/run.sh).
* **No `-split-files`.** Opaque items stay as reported axioms (verdict `missing_model`) instead of hand-written Lean stubs. Example: the three noted axioms in [mbpp/aeneas_pristine/mbpp_591_swap_List/attempt-1/check.json](mbpp/aeneas_pristine/mbpp_591_swap_List/attempt-1/check.json).
* **No `--extract-opaque-bodies`.** Translating `core` bodies makes every input fail inside the standard library and loses the verdict distinction the brief asks for. Evidence: [notes/journal/2026-10/2026-10-30-missing-context-is-four-things.md](notes/journal/2026-10/2026-10-30-missing-context-is-four-things.md).
* **Missing models are repaired in Rust, not Lean.** A local safe shim with the same behaviour goes in the solution file, else the call site is rewritten inline; raw pointers are rewritten away. Rule text: [.claude/skills/mbpp-aeneas/SKILL.md](.claude/skills/mbpp-aeneas/SKILL.md) ("What the verdicts mean, and what to do"); worked diff: [mbpp/aeneas_pristine/mbpp_4_heap_queue_largest/failures.md](mbpp/aeneas_pristine/mbpp_4_heap_queue_largest/failures.md).
* **Pinned dataset.** [data/mbpp-rs.json](data/mbpp-rs.json) (HF revision inside); `mbpp.py fetch` reads it and only touches the network with `--remote`.
* **Axiom policy.** Only `propext`, `Classical.choice`, `Quot.sound` are accepted; every other axiom is reported with its Rust origin (row 5 of the table below).


### Check script

This (`tools/check.py`) is a deterministic script that checks Rust to Lean translation.

`tools/check.py` runs the pipeline Charon → Aeneas → Lean type-check → `#print axioms` on a single `.rs` file and prints one JSON report on stdout (`--human` for a readable summary). The exit code mirrors the verdict; when several problems are found, the most severe one wins (severity order: `toolchain_problem` > `invalid_rust` > `unsupported_code` > `missing_context` > `missing_model`).

| Code | Verdict | Meaning |
|------|---------|---------|
| 0 | `translates` | Lean generated, type-checks, and depends only on standard axioms (`propext`, `Classical.choice`, `Quot.sound`) |
| 1 | `unsupported_code` | Charon or Aeneas rejected a construct; also a method of a hand-modelled library trait whose Lean structure lacks the field (no model can be added from outside) |
| 2 | `missing_context` | rustc/Charon could not see a definition (rustc E0405/E0412/E0422/E0425/E0432/E0433/E0463, or Charon asking for `--include`); supply the code or pass `--charon-arg=--include=...` |
| 3 | `invalid_rust` | rustc rejected the code for other reasons |
| 4 | `toolchain_problem` | Charon/Aeneas crashed or produced nothing without a diagnostic, generated Lean does not type-check, or the Lean check was skipped (library not built / `lake` missing) |
| 5 | `missing_model` | Everything translated, but the Lean depends on an axiom for an opaque item — write a Lean model or avoid the item; raw-pointer signatures get a note since the type may not carry the effect |
| 64 | usage error | bad arguments, not a `.rs` file, or Charon/Aeneas not built (still prints a JSON report) |

The JSON report contains `verdict`, `reasons` (human-readable strings), per-`stage` status (`charon`/`aeneas`/`lean`: `ok` / `partial` / `failed` / `skipped`), per-function translation status (`translated` / `sorry` / `axiom` / `missing`), the `axioms` each function depends on (with origin: stdlib / dependency / local / library), and tool `versions`.

Example report: [mbpp/aeneas_pristine/mbpp_3_is_not_prime/attempt-1/check.json](mbpp/aeneas_pristine/mbpp_3_is_not_prime/attempt-1/check.json)
