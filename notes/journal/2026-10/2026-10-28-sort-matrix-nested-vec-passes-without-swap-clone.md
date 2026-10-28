# mbpp_12_sort_matrix: nested Vec<Vec<isize>> passes once sort/sum are hand-rolled

[OBS 2026-10-28] Attempt 1 (`m.sort_by_key(|row| row.iter().sum::<isize>())`,
tests pass): `missing_context` — no Lean model for `Iterator::sum`, the
`Sum<&isize> for isize` impl, or `slice::sort_by_key`. Same failure class as
problems 3/4/6.

[OBS 2026-10-28] Attempt 2 passes with no axioms: row sums by index loops,
stable selection of the unused row with minimum sum, rows copied
element-by-element into a fresh `Vec<Vec<isize>>`. So nested ownership is
fine for Aeneas: `M[i][j]` double indexing, `M[i].len()`, `Vec<bool>` as a
used-set with `used[best] = true`, pushing owned rows. What was deliberately
avoided because unmodelled: `swap`, `clone`, `remove`, moving a row out of
the input by index (not `Copy`).

[OBS 2026-10-28] Running tally: 0/5 first-attempt, 4/5 pass at attempt 2,
1/5 (the `String` problem) unresolved. Every non-string failure was a
missing stdlib model, repaired the same way: index loops over owned values.

## See also

- 2026-10-28-mbpp-loop-first-three-problems.md
- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
