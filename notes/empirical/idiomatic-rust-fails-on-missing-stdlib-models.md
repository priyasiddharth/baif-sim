# Idiomatic Rust fails translation on missing stdlib models, not unsupported syntax

**Verified against:** aeneas 399081f, charon 2ec7e96, rustc nightly-2026-09-17, Lean v4.35.0 (Aeneas Lean lib at the same aeneas commit)
**Last verified:** 2026-10-29
**Status:** single-benchmark (6 MBPP problems, 1 generator; dataset pinned at HF revision 28441b6)

[EMP] 0/6 first-attempt passes on MBPP problems 3, 4, 6, 8, 11, 12 written as a
      model would normally write them; 5/6 after one revision driven by the
      check report (11, the `String` one, is unreachable — see below). Every
      non-string attempt-1 verdict was `missing_context`; none was
      unsupported Rust. Items with no model in `aeneas/backends/lean`:
      - `Iterator::map`, `Map::next`, `collect` (square_nums).
      - `Iterator::sum`, `Sum<&isize> for isize`, `slice::sort_by_key`
        (sort_matrix).
      - `Iterator::take_while`, `Iterator::any`, `RangeFrom::next`,
        `TakeWhile` (iterator adapters). Lean type-check also failed:
        "`take_while` is not a field of structure `core.iter.traits.iterator.Iterator`".
      - `&isize * &isize` (`Mul` impl on references, from closure args).
      - `[T]::sort_unstable_by`, `Vec::truncate`.
      - `isize::count_ones`.
      (mbpp/*/failures.md has the diffs.)

[EMP] What translated cleanly with no axioms: `while` + indexing, `Vec::new`
      /`push`/`len`, index assignment `v[i] = x`, nested `Vec<Vec<_>>` with
      `M[i][j]` and pushing owned rows, `Vec<bool>` flags, integer
      `+ - * % ^ & << >>`, `as` casts, comparisons, early `return`,
      struct/enum/match, `&mut` params (tests/compile_ok1.rs and the five
      attempt-2 solutions). Avoid `swap`/`clone`/`remove` (unmodelled).

[HYP] Feeding the generator the list of modelled stdlib items
      (`aeneas/src/extract/ExtractBuiltinLean.ml`) up front would turn most of
      these into first-attempt passes. Untested. This is the main lever for
      part 3 of the brief.

[OBS 2026-10-28] Strings are worse than "missing model": `String::new`/`push`
      and `Deref<str> for String` are unmodelled (so any String-building
      function keeps ≥2 axioms), and `Pattern`-bound methods, a value
      pulled through `Chars::next` before a loop (ended loan projector the
      loop matcher lacks a case for; confirmed 2026-10-29), and stored `||`
      in loops each fail for a different reason — see the remove_Occ
      journal entry and tests/unsupported/chars_next_before_loop.rs.

## See also

- ../durable/opaque-functions-become-axioms-or-lean-lib-models.md
- ../journal/2026-10/2026-10-28-mbpp-loop-first-three-problems.md
- ../journal/2026-10/2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- ../journal/2026-10/2026-10-29-dataset-pinned-and-square-nums.md
