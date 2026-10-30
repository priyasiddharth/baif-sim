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


## Stage 1

Part 1 of the assignment: a skill that calls a deterministic script to check whether Rust translates through Charon and Aeneas to Lean. The script is [tools/check.py](tools/check.py). The skill is [mbpp-aeneas](.claude/skills/mbpp-aeneas/SKILL.md): it generates a solution, runs the problem's unit tests, calls the script, and revises on its report. The generator is the Claude Code session itself; the revise loop around the script is what stage 2 starts from.

<img src="check_flow.png" alt="Check flow" width="100%" style="display:block; margin:0 0 0 0;" />

### Usage

```
tools/check.py FILE.rs [-o DIR] [--charon-arg=ARG]... [--aeneas pristine|mod|PATH] [--human]
```

* A JSON report is output on stdout; `--human` prints a readable summary instead.
* The generated Lean goes to `DIR` (default: a new temp dir).
* The exit code is the verdict (table below).
* `--charon-arg` passes an option through to Charon, e.g. `--charon-arg=--include=core::ptr::swap`.
* `--aeneas` selects the checkout: the upstream pin (default), the fork, or a path.
* In Claude Code, `/mbpp-aeneas 3` runs the first three MBPP problems and `/mbpp-aeneas mbpp_3_is_not_prime` runs one by name.
* The skill drives [tools/mbpp.py](tools/mbpp.py) (`fetch`, `test`, `attempt`, `recheck`, `report`); `tools/mbpp.py report` prints the per-problem outcome under each checkout.

### What is checked

`translates` is three independent checks, and the report says which ones ran (`stages`). The exit codes of Charon and Aeneas alone are not enough: each stage can exit 0 on code that did not translate ([notes/empirical/exit-codes-do-not-reflect-translation-status.md](notes/empirical/exit-codes-do-not-reflect-translation-status.md)):

1. **Charon** exits 0 *and* its LLBC and warnings carry no `type_error` / "not supported". [tests/unsupported/async_fn.rs](tests/unsupported/async_fn.rs): Charon exits 0 with a `type_error` in the LLBC.
2. **Aeneas** exits 0 *and* every function is `translated`: no `sorry` body, no `axiom`. [tests/unsupported/raw_ptr.rs](tests/unsupported/raw_ptr.rs): Aeneas exits 1 but still writes the file, with the body as `sorry`; [tests/unsupported/or_in_loop_bool.rs](tests/unsupported/or_in_loop_bool.rs): Aeneas exits 0 and the Lean does not type-check.
3. **Lean** type-checks the output *and* `#print axioms` on every function lists only `propext`, `Classical.choice`, `Quot.sound`. [tests/unsupported/ref_mul.rs](tests/unsupported/ref_mul.rs): Aeneas exits 0 with only a warning and an axiom for `Mul<&u32>` remains.

Surrounding code and dependencies: the file is compiled alone as `--crate-type=lib --edition=2021 -Awarnings`, so only `core`/`alloc`/`std` are in scope and nothing else has to be supplied. Standard-library bodies are not translated: Charon keeps their signatures, Aeneas substitutes the model from its Lean library or emits an `axiom` ([notes/durable/opaque-functions-become-axioms-or-lean-lib-models.md](notes/durable/opaque-functions-become-axioms-or-lean-lib-models.md)). The Lean library used is the one built from the checkout that ran (`versions.lean_lib` in the report).

### Check script

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

One fixture per verdict, pinned in [tests/expected.json](tests/expected.json) for both checkouts and run by CI:

| Code | Fixture | What it exercises |
|------|---------|-------------------|
| 0 | [tests/compile_ok1.rs](tests/compile_ok1.rs), [tests/user_trait_next.rs](tests/user_trait_next.rs) | structs, enums, `&mut`, loops, `Vec`; a user-defined `Iterator` called directly |
| 1 | [tests/unsupported/raw_ptr.rs](tests/unsupported/raw_ptr.rs), [tests/unsupported/async_fn.rs](tests/unsupported/async_fn.rs), [tests/unsupported/user_trait_any.rs](tests/unsupported/user_trait_any.rs) | raw-pointer deref; `async fn`; a provided `Iterator` method the library structure lacks |
| 2 | [tests/unsupported/missing_dep.rs](tests/unsupported/missing_dep.rs) | unresolved import (E0432) |
| 3 | [tests/unsupported/invalid.rs](tests/unsupported/invalid.rs) | rustc type error |
| 4 | [tests/unsupported/or_in_loop_bool.rs](tests/unsupported/or_in_loop_bool.rs) | Aeneas emits a `Prop` for a stored `\|\|` in a loop; Lean rejects it |
| 5 | [tests/unsupported/ref_mul.rs](tests/unsupported/ref_mul.rs), [tests/unsupported/raw_ptr_value.rs](tests/unsupported/raw_ptr_value.rs) | `u32 * &u32` axiom; pointer arithmetic without deref (axioms carry the raw-pointer note) |

Versions: Aeneas `de16f3c` (fork `ee1c669` = pin + loop-matcher patch), Charon `373d840` (= `aeneas/charon-pin`), rustc `nightly-2026-09-17`, Lean `v4.35.0`. Every report records them under `versions` (`aeneas`, `aeneas_checkout`, `charon`, `charon_matches_pin`, `rustc`, `lean`), so a verdict is never separated from the toolchain that produced it.

### Input forms

Implemented: one file, as above. The other two the assignment names, parked in [notes/loose-ends/parked.md](notes/loose-ends/parked.md):

* **A crate.** Run `charon cargo --preset=aeneas` in the crate directory instead of `charon rustc` on one file; it emits one LLBC for the whole crate and the Aeneas and Lean stages are unchanged. Dependencies are translated opaquely, as the standard library is today, and their items surface as `missing_model` axioms unless pulled in with `--charon-arg=--include=<path>`.
* **A few selected lines.** Wrap them in a stub lib crate and run the same pipeline. Names rustc cannot resolve come back as `missing_context` with the error codes, which is the list of surrounding items the user has to paste in; repeat until the verdict is about the lines themselves.

### Results and limits

Seven MBPP problems, same outcome under both checkouts (`tools/mbpp.py report`):

| | |
|---|---|
| first-attempt pass | 0 / 7 |
| pass by attempt 2 | 6 / 7 |
| unresolved | 1 / 7 ([mbpp/aeneas_pristine/mbpp_11_remove_Occ](mbpp/aeneas_pristine/mbpp_11_remove_Occ/failures.md)) |

Every attempt-1 failure was a missing Lean model or the `Iterator` encoding gap, not unsupported syntax ([notes/empirical/idiomatic-rust-fails-on-missing-stdlib-models.md](notes/empirical/idiomatic-rust-fails-on-missing-stdlib-models.md)).

Cases it cannot handle:

* **`mbpp_11_remove_Occ`** (`fn remove_Occ(s: String, ch: String) -> String`). Four attempts under both checkouts. The fork removes the first of its three blockers (the loop-join matcher, see [tests/unsupported/chars_next_before_loop.rs](tests/unsupported/chars_next_before_loop.rs)); under the fork attempts 2–3 then hit the stored-`||` bug (verdict 4). Attempt 4 fails identically under both: `String::new`, `String::push` and `Deref<str>` have no Lean model, and the signature returns a `String`, so no body rewrite can avoid them ([mbpp/aeneas_mod/mbpp_11_remove_Occ/attempt-4/check.json](mbpp/aeneas_mod/mbpp_11_remove_Occ/attempt-4/check.json)). An unmodelled type in the required signature is out of reach for a repair that keeps the signature.
* **`mbpp_591_swap_List` attempt 1** ([check.json](mbpp/aeneas_pristine/mbpp_591_swap_List/attempt-1/check.json)). `ptr::swap` becomes an axiom `MutRawPtr T → MutRawPtr T → Result Unit`: the swapped Vec is neither input nor output, so any Lean model type-checks and the function becomes the identity. The tool cannot tell this from a modellable axiom; it only attaches the raw-pointer note. Attempt 2 (safe swap) translates.
* **[tests/unsupported/or_in_loop_bool.rs](tests/unsupported/or_in_loop_bool.rs).** A toolchain bug the script reports as verdict 4 but cannot work around; the generator has to avoid storing `a || b` inside a loop.

### Adapting to Aeneas changes

* **Pins move as a pair.** `aeneas/` and `charon/` are checked out together (per `charon-pin`), the fork's commits are rebased, all three are rebuilt ([CLAUDE.md § Setup](CLAUDE.md#setup)). CI asserts that Charon matches the pin.
* **Verdict drift is measured, not guessed.** [tests/run_expected.py](tests/run_expected.py) reruns every fixture and recorded attempt under both checkouts and fails on any change; `--update` records the new baseline. The [chars_next_before_loop.rs](tests/unsupported/chars_next_before_loop.rs) rows (pristine `unsupported_code`, fork `missing_model`) are the live example of a fix changing a verdict.
* **Detection is model-driven, not list-driven.** The script never consults a list of supported APIs; it reads `#print axioms`. When upstream adds a Lean model for an item, its `missing_model` rows flip to `translates` with no change to the script.
* **Unsafe Rust.** Today raw pointers are opaque values and pointer-effect axioms carry only a note. When Aeneas gains pointer semantics the note rule retires and the `raw_ptr*.rs` rows move; no verdict depends on guessing what Aeneas will support.
* **Encoding gaps are upstream's.** The `Iterator` structure in the Lean library is what turns `map`/`collect`/`any` into `unsupported_code`; [tests/unsupported/user_trait_any.rs](tests/unsupported/user_trait_any.rs) flips the day it changes.


## Stage 2

The harder question of the assignment: compatible Rust on the first attempt, without a generate/check/patch loop. Plan in two parts; what has been tried under each is listed below.

1. Improve Charon+Aeneas tooling to accept a larger subset of Rust
    * Also enhance the source language to make translation/proofs easier
2. Add skills that generate good patterns / the enhanced language

### 1. Widening what Aeneas accepts (the fork `aeneas_mod`)

* **Loop-matcher fix (done).** A value taken via `Chars::next` before a loop leaves an ended-loan projector in a region abstraction; the matcher in `InterpMatchCtxs.ml` had no arm for it, so Aeneas failed with "Could not match the contexts" on identical contexts. The fork adds arms for ended projected loans and ended shared loans plus a regression test (`aeneas_mod` commits 38531ab, ee1c669; upstream `make test` stays green with no expected-output changes). Effect: [tests/unsupported/chars_next_before_loop.rs](tests/unsupported/chars_next_before_loop.rs) moves from `unsupported_code` to `missing_model`; walkthrough in [examples/loop_join/run.sh](examples/loop_join/run.sh). Upstream PR still to open.
* **Stored `||` in a loop becomes a Lean `Prop` (investigated, fix identified).** Fixture: [tests/unsupported/or_in_loop_bool.rs](tests/unsupported/or_in_loop_bool.rs). Upstream PR [#1374](https://github.com/AeneasVerif/aeneas/pull/1374) (open, absent from our pin) prints comparisons as `(a = b : Bool)` and Bool negation as `!`; its source diff applies cleanly to the fork and the resulting output type-checks on our fixture. The maintainer asked for the annotation to come from the type-annotation micro-pass (`PureMicroPassesAnnots.ml`) and only where the comparison is not an `if` condition. To apply: cherry-pick the two source hunks or implement the micro-pass variant, regenerate `tests/lean` with `make test`, commit the regenerated outputs.
* **Raw pointers (design question, parked).** `ptr::swap` becomes an axiom `MutRawPtr T → MutRawPtr T → Result Unit`: the swapped `Vec` is neither input nor output, so any model makes `swap_List` the identity ([attempt-1 report](mbpp/aeneas_pristine/mbpp_591_swap_List/attempt-1/check.json)). Options weighed in [notes/journal/2026-10/2026-10-29-swap-list-raw-pointers-become-opaque-values.md](notes/journal/2026-10/2026-10-29-swap-list-raw-pointers-become-opaque-values.md): a global heap (rejected: taxes safe code); a local heap with ownership handoff (needs region-end information raw pointers do not carry); per-cell linear permission tokens in the Verus `PPtr`/`PointsTo` style, where the pointer stays a plain value and `swap : Ptr T → Ptr T → PointsTo p a → PointsTo q b → (PointsTo p b × PointsTo q a)` makes the effect visible in the type. The token stands in for the lifetime the raw pointer erased: `as_mut_ptr` hands the `Vec`'s contents to the token, and consuming the token is the signal to write the updated value back into the originating `Vec`, the way a borrow's backward function does for `&mut`. Its cost: plain Rust carries no tokens, so annotations or inference are needed. Upstream's unmerged `cezar/loops` branch carries heap-model and separation-logic commits for raw pointers and is the thing to watch.

### 1.1 Enhancing the source language

Untried so far.

### 2. Skills that generate good patterns

* **Evidence.** Seven MBPP problems: 0/7 first attempt, 6/7 by attempt 2, 1 unresolved. Every attempt-1 failure was a missing stdlib model or the `Iterator` encoding gap, never unsupported syntax ([notes/empirical/idiomatic-rust-fails-on-missing-stdlib-models.md](notes/empirical/idiomatic-rust-fails-on-missing-stdlib-models.md)). The core that always translated: `while` with indexing, `Vec::new/push/len`, index assignment, integer and bit ops, `as` casts.
* **Repair rules already in the skill** ([SKILL.md](.claude/skills/mbpp-aeneas/SKILL.md)): a modellable missing item gets a local safe shim in the solution file, else an inline rewrite; a raw-pointer note means rewrite without `unsafe`; an encoding gap means replace the adapter chain with a `while` loop. Worked diffs are the attempt-2 files under [mbpp/aeneas_pristine/](mbpp/aeneas_pristine).
* **First-attempt strategy (parked).** Generate a short guide from `ExtractBuiltinLean.ml` plus the supported-core list, run the loop on held-out problems with and without it, compare first-attempt pass rates with `tools/mbpp.py report` ([notes/loose-ends/parked.md](notes/loose-ends/parked.md), "Brief parts 2 and 3").
