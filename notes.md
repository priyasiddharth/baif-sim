# Notes

## 28 Oct 11 AM
We would like coding agents to write Rust that [Aeneas](https://github.com/AeneasVerif/aeneas) can translate.
    


1. A simple starting point is a skill that calls a deterministic script to check whether code translates through Charon and Aeneas to Lean. ** The user might give it a crate, one file, or a few selected lines. 
Start with one case and explain how you would handle the others: 
>Idea is to build a collection of tests that pass/fail translation to lean.
>Also have tests that document options which include/exclude code
what surrounding code and dependencies are needed, and 
>Make sure Aeneas fills up stdlib bodies

what did you actually check? 
>How to actually check that all code is translated?
>When translating a crate which requires external definitions (i.e., definitions coming from external dependencies such as the Rust standard library), we advise using the -split-files option. With -split-files, Aeneas will generate template files listing the missing definitions for which the user will have to provide hand-written models. 

Distinguish unsupported code from missing context or a toolchain problem.

Explain how your approach would adapt as Aeneas develops.

2. The same skill, or a sibling skill, could patch code that fails translation. 
Preserve its behaviour and show the diff. 

Hiding unsupported code behind unchecked stubs does not count as a repair.
>Repair involves transforming unsupported code to supported programming paradigm E.g., unsafe code to safe code

Successful translation alone is not a correctness proof.
>Agreed

3. The harder question is how to get compatible Rust on the first attempt, without a generate/check/patch loop. 

A strategy is enough here; implementation would likely take more than eight hours. 

Fine-tuning and other techniques for local inference with open-source models are welcome. 

Also suggest a way to bring the benefits to existing personal or enterprise subscriptions, such as Claude Code, Codex or subscription-backed open models, without requiring custom weights or per-token API access. Check what your chosen plan allows.
>Use normal AI interface
## 28 Oct — progress

### Setup (pinned versions)
- aeneas submodule @ 399081f (nightly-2026.10.28), charon submodule @ 2ec7e96 (= `aeneas/charon-pin`)
- rustc nightly-2026-09-17 (charon `rust-toolchain`), Lean v4.35.0 + Mathlib v4.35.0 (`aeneas/backends/lean`)
- Built: `charon/bin/charon`, `aeneas/bin/aeneas`, Aeneas Lean lib (`lake build` in `aeneas/backends/lean`)
- `aeneas/charon` is a symlink to `../charon` (gitignored by aeneas) — aeneas then skips the pin check, so keep them matched by hand

### Check tool: `tools/check.py <file.rs> [-o DIR] [--charon-arg=...] [--human]`
- Stages: Charon → Aeneas → Lean type-check (`lake env lean`) → `#print axioms` per function
- JSON report on stdout: versions, per-stage status, per-function status (translated / sorry / missing), axioms (origin stdlib / dependency / local / library, used_by), verdict, reasons
- Exit code = verdict: 0 translates, 1 unsupported_code, 2 missing_context, 3 invalid_rust, 4 toolchain_problem
- Handles one file (as a lib crate) for now; crate / selected lines still to do

### Test cases (`tests/`)
| file | verdict | why |
|---|---|---|
| `compile_ok1.rs` | translates | structs, enums, match, &mut, loops, slices, Vec; only standard Lean axioms |
| `unsupported/raw_ptr.rs` | unsupported_code | Charon ok; Aeneas: "does not yet support dereferencing raw pointers" → body `sorry` |
| `unsupported/async_fn.rs` | unsupported_code | Charon **exits 0** with warnings, puts `type_error(...)` in LLBC; Aeneas then "Internal error" |
| `unsupported/ref_mul.rs` | missing_context | `u32 * &u32` → `Mul` impl not modelled in Lean lib → `axiom`; `*r` fixes it |
| `unsupported/missing_dep.rs` | missing_context | rustc E0432 unresolved import |
| `unsupported/invalid.rs` | invalid_rust | rustc type error |

### Findings
- Exit codes lie: Charon exits 0 on unsupported code; Aeneas exits 0 while leaving axioms. Need LLBC/warnings + Lean `#print axioms`.
- Opaque functions: Charon keeps only signatures for non-local items (Foreign/Opaque). Aeneas uses the Lean lib model if the name is in `ExtractBuiltinLean.ml`, else emits an `axiom` (or a `-split-files` template). An axiom only asserts the function exists with that type — consistent, but nothing about it is provable.
- Generated Lean can fail to parse: crate named `example` (Lean keyword) → pass `-namespace`; source path containing `/-` opens a nested Lean comment → run Charon with a relative path.
- Existing unsupported-feature tests are thin: Aeneas `tests/src` has 7 `//@ known-failure` (raw pointers, GAT/mutually-recursive traits, higher-ranked lifetime bounds, borrow-check negatives); Charon `tests/ui` has 18, only ~7 real unsupported features (coroutines, GATs with lifted assoc types, some `dyn` cases, opaque enum match).

### Next
- Crate input (`charon cargo`) and selected-lines input (wrap in a stub crate)
- More failing cases (unions, inline asm, `dyn`, closures returning refs, ...)
- Part 2: repair skill using `error_ref` locations; part 3: first-attempt strategy

## 28 Oct — MBPP loop (skill `mbpp-aeneas`)

### Pieces
- Dataset: MultiPL-E `mbpp-rs` (HF `nuprl/MultiPL-E`, 354 problems). Each = doc comment + signature (`prompt`) and a `main` of `assert_eq!`s (`tests`). Fetched via the HF datasets-server rows API.
- `tools/mbpp.py fetch N | NAME`, `test NAME file.rs` (compiles solution+tests with Charon's pinned nightly, runs), `attempt NAME file.rs --commit` (tests → check.py → `mbpp/<name>/attempt-N/` → `status.json` → git commit), `recheck NAME` (rerun check.py on recorded attempts after a tool fix), `report`.
- Skill: `.claude/skills/mbpp-aeneas/SKILL.md` — the LLM (Claude in the session) generates, runs tests, records, reads `check` reasons, revises, max 5 attempts. Attempt 1 is written "normally" so it measures first-attempt translation.
- Problem fn signatures are non-`pub` and MBPP keeps odd names (`differ_At_One_Bit_Pos`): rustc lints fire. check.py now passes `-Awarnings` (lints off; Charon's own "not supported" warnings are not lints and still show).

### Results (first 3 problems)
| problem | attempt 1 | why | attempt 2 |
|---|---|---|---|
| mbpp_3_is_not_prime | missing_context | `(2..).take_while(..).any(..)`: `Iterator::take_while/any`, `RangeFrom::next` have no Lean model; closures took `&isize` so `&isize * &isize` → axiom; Lean type-check failed with "`take_while` is not a field of structure Iterator" | pass (while loop) |
| mbpp_4_heap_queue_largest | missing_context | `sort_unstable_by`, `Vec::truncate` unmodelled | pass (selection sort via indexing + push) |
| mbpp_6_differ_At_One_Bit_Pos | missing_context | `isize::count_ones` unmodelled | pass (`x & (x-1) == 0`) |

0/3 first-attempt; 3/3 after one round with the check report as input. All failures were **missing stdlib models**, not unsupported Rust: idiomatic Rust leans on iterator adapters / slice sort / int intrinsics that `aeneas/backends/lean` doesn't model. Supported core: `while` + indexing, `Vec::new/push/len`, index assignment, integer ops, `as` casts, bit ops.

### check.py fixes found by this run
- rustc lints (dead_code, non_snake_case) were classified as Charon unsupported_code → `-Awarnings`.
- Lean errors "`x` is not a field of structure …" / unknown constant = Aeneas emitted a call the Lean lib lacks → now `missing_context` ("Lean library lacks a model"), not toolchain_problem.
- Doc-header regex: type axioms have no `:` after `]`, attrs can span lines, `axiom` may be followed by a newline → axioms were showing as origin "library" with no Rust name.
- Closure `call_once`/`call_mut` share a span → duplicate function entries; deduped.

### Open
- Attempt 1 verdicts were re-derived with `recheck` after the fixes (committed as "recheck after check.py change"); the original wrong verdicts stay in history.
- A "supported stdlib API" list (from `ExtractBuiltinLean.ml`) fed to the LLM up front would likely turn these into first-attempt passes — that's the part-3 lever.

### TODO: split the skill into generic loop + dataset adapter
The flow (generate → unit tests immediately → check.py → delta into failures.md → commit program+log → revise, ≤5 attempts) is generic. Only these parts are MBPP-specific and should move to an adapter: `fetch` (HF MultiPL-E rows API, field names), `split_tests` (MultiPL-E's leading `}`), the harness assumption "solution.rs + tests.rs with a `main`", and the `mbpp/` layout/names. Target shape: generic skill (`aeneas-loop`) + `tools/loop.py` taking a problem dir with `prompt.rs`, `tests.rs` and a test command; `tools/sources/mbpp.py` as the first adapter. Not doing it yet.
