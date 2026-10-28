# mbpp_12_sort_matrix — failure log

## Attempt 1 — check:missing_context

Initial version.
Reasons:
- missing_context: no Lean model for standard-library item: core::iter::traits::accum::{impl core::iter::traits::accum::Sum<&'a isize> for isize}::sum
- missing_context: no Lean model for standard-library item: alloc::slice::{[T
- missing_context: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::sum

Functions: sort_matrix translated, {closure} translated
Axioms: core::iter::traits::accum::{impl core::iter::traits::accum::Sum<&'a isize> for isize}::sum, alloc::slice::{[T, core::iter::traits::iterator::Iterator::sum

Code:
```rust
/// Write a function to sort a given matrix in ascending order according to the sum of its rows.
fn sort_matrix(M: Vec<Vec<isize>>) -> Vec<Vec<isize>> {
    let mut m = M;
    m.sort_by_key(|row| row.iter().sum::<isize>());
    m
}
```
