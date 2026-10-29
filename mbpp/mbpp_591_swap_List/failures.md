# mbpp_591_swap_List — failure log

## Attempt 1 — check:missing_context

Initial version.
Reasons:
- missing_context: no Lean model for standard-library item: core::ptr::swap
- missing_context: no Lean model for standard-library item: alloc::vec::{alloc::vec::Vec<T>}::as_mut_ptr
- missing_context: no Lean model for standard-library item: core::ptr::mut_ptr::{*mut T}::add

Functions: swap_List translated
Axioms: core::ptr::swap, alloc::vec::{alloc::vec::Vec<T>}::as_mut_ptr, core::ptr::mut_ptr::{*mut T}::add

Code:
```rust
/// Write a rsthon function to interchange the first and last elements in a vector.
fn swap_List(newList: Vec<isize>) -> Vec<isize> {
    let mut v = newList;
    let n = v.len();
    if n >= 2 {
        let p = v.as_mut_ptr();
        unsafe {
            std::ptr::swap(p, p.add(n - 1));
        }
    }
    v
}
```
