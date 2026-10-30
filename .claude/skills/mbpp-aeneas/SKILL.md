---
name: mbpp-aeneas
description: Generate Rust for MBPP problems, run the supplied unit tests, check translation to Lean with tools/check.py, and iterate on the check report until it translates. Use when asked to run the MBPP/Aeneas loop, e.g. "/mbpp-aeneas 3" or "/mbpp-aeneas mbpp_3_is_not_prime".
---

# MBPP → Rust → Aeneas loop

Argument: a count (`3` = the first 3 problems, `--offset K` to start later) or
problem names. All commands run from the repo root.

Aeneas checkouts: every `attempt` is checked under both the pristine upstream
pin (`aeneas/`) and the patched fork (`aeneas_mod/`), and recorded as the
same attempt number in two trees, `mbpp/aeneas_pristine/<name>/` and
`mbpp/aeneas_mod/<name>/` (each has its own `status.json`, `failures.md`,
`attempt-N/check.json`). `--aeneas pristine` or `--aeneas mod` (or `AENEAS=`)
restricts a command to one tree. The attempt output and commit message give
the outcome per checkout; a problem **passes** when the pristine tree passes
(the fork only shows what a candidate Aeneas fix would buy). Report both
outcomes in the final summary and point out any attempt where they differ.

## Steps per problem

1. **Fetch** (skip if `mbpp/aeneas_pristine/<name>/prompt.rs` exists):
   `tools/mbpp.py fetch 3` or `tools/mbpp.py fetch <name>`.
   Read `mbpp/aeneas_pristine/<name>/prompt.rs` (doc comment + signature) and
   `tests.rs`. If `failures.md` exists there, read it too: it is the history of
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
   type-check → `#print axioms`) under each checkout, stores the program and
   reports under `mbpp/aeneas_<checkout>/<name>/attempt-N/`, appends a section
   to that tree's `failures.md` (check reasons, the delta from the previous
   attempt — resolved / still failing / new — and the code diff), and commits
   the new program together with the updated failure logs.
   - `"outcome": "pass"` under `pristine` (exit 0 means both trees passed):
     report **passed on attempt N** (attempt 1 = first-attempt pass) and move
     to the next problem. If only `mod` passed, say so and keep going.
   - Otherwise read the printed `pristine` `check` block (`verdict`,
     `reasons`, `functions`, and the `axioms` entries with their `origin`
     and `note`) and
     `mbpp/aeneas_pristine/<name>/failures.md`. Revise the code to
     circumvent those failures, then go back to step 3. Keep the same
     signature and behaviour. Do not hide code behind stubs, `unsafe`, or by
     deleting functionality.
   - Stop after 5 attempts and report the problem as unresolved.

## What the verdicts mean, and what to do

`check.json` → `verdict` (also check.py's exit code), with `reasons`,
`functions` and `axioms`. One verdict can have several causes; read the
reasons and act per cause. Never fix a verdict by stubbing, `unsafe`, or
deleting functionality, and keep the signature from `prompt.rs`.

- `translates` (0): every function translated, the Lean type-checks, and
  `#print axioms` shows only `propext`, `Classical.choice`, `Quot.sound`.
  This is "no holes in the model", not a correctness proof.

- `unsupported_code` (1): the Rust must change. Two causes, both in `reasons`:
  - Charon or Aeneas rejected a construct (message + file:line). Typical:
    iterator chains and closures, trait-dispatched ops on references
    (`&a * &b`), a `&mut self` library call on a temporary before a loop
    (`s.chars().next()`), nested loops with `break`/`continue` to an outer
    label. Rewrite that construct: index `while` loops, `*r` for arithmetic
    on references, owned values, flags instead of labelled breaks.
  - "library trait structure lacks the method … `map` is not a field of
    structure `core.…Iterator`": the method belongs to a trait the Aeneas
    library models by hand, and its structure has no slot for it (`map`,
    `collect`, `take_while`, `any`, `sum`, `rev`, …). Nothing outside Aeneas
    can add it, so do not look for a model: replace the adapter chain with a
    `while` loop over indices.

- `missing_model` (5): everything translated and type-checks, but the Lean
  depends on an `axiom` — an item whose body Aeneas did not translate and the
  library does not model. Each `axioms` entry has `rust`, `origin`,
  `used_by` and sometimes `note`. Act by entry:
  - `origin: stdlib`, no note (`Vec::truncate`, `slice::sort_unstable_by`,
    `isize::count_ones`, `Mul for &isize`, `Iterator::sum`): a model is
    missing, not impossible. Preferred fix: write a **local shim** in the
    solution file — a safe Rust function with the same behaviour and a plain
    signature (`fn vec_truncate<T>(v: &mut Vec<T>, n: usize)`,
    `fn count_ones(x: isize) -> u32`, an in-place selection sort) using only
    `while`, indexing, `push`, integer ops — and call it instead. The shim is
    translated and checked with the program and shows up in `functions`. If
    the shim would itself need closures, iterator traits or generics over
    traits, fall back to rewriting the call site inline. Either way, name
    the item in the attempt notes: it is a candidate for a library model.
  - `origin: stdlib` with `note: type may not carry the effect` (`ptr::swap`,
    `ptr::write`, `*mut T::add`, `Vec::as_mut_ptr`): the axiom's type has no
    output for the memory that was changed, so even a model could not make
    the translation correct — the Lean function is wrong, not incomplete.
    Treat as must-rewrite: drop raw pointers and `unsafe`, mutate the owned
    `Vec` by index. The note is a hint from the signature; `Cell`/`RefCell`
    and `static mut` have the same problem without a note — avoid them too.
  - `origin: local`: a function of the solution itself was left opaque or
    `sorry`; the matching `functions` entry's `reason`/`error_ref` points at
    the Charon/Aeneas message. Rewrite that function as under
    `unsupported_code`.
  - `origin: library` (an axiom declared inside the Aeneas Lean library:
    `Pin`, atomics, `PanicInfo`) or `origin: dependency`: avoid the feature;
    MBPP solutions have no dependencies.

- `missing_context` (2): rustc could not resolve a name (E0405/E0412/E0425/…)
  or Charon asked for `--include`. For MBPP this means the solution refers to
  something it did not define (a helper, a `use` of an external crate). Make
  the file self-contained; never add crates. (For non-MBPP inputs this is the
  verdict that says "supply surrounding code", not "change the code".)

- `invalid_rust` (3): rustc rejected the code; the unit tests should have
  caught it first (`attempt` refuses to record a failing version).

- `toolchain_problem` (4): Charon panicked, Aeneas hit an internal error, or
  the generated Lean failed to type-check for a reason other than a missing
  field. Known case: a `bool` stored from `a || b` inside a loop body comes
  out as `Prop` — branch (`if a { true } else { b }`) instead of storing the
  `||`. Anything else: stop, report the reason verbatim, do not rewrite
  blindly.

## Finish

`tools/mbpp.py report` prints, per problem and per checkout (`pristine`,
`mod`), whether it passed, the number of attempts, and whether attempt 1
passed. Summarize that table to the user, note which constructs caused
failures, and name any problem where the two checkouts disagree.
