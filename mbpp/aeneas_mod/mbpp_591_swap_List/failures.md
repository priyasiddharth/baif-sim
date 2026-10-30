# mbpp_591_swap_List — failure log (aeneas: mod)

## Attempt 1 — check:missing_model

Initial version.
Reasons:
- missing_model: no Lean model for standard-library item: core::ptr::swap (type may not carry the effect: raw-pointer argument, no output for the pointee)
- missing_model: no Lean model for standard-library item: alloc::vec::{alloc::vec::Vec<T>}::as_mut_ptr (type may not carry the effect: raw-pointer argument, no output for the pointee)
- missing_model: no Lean model for standard-library item: core::ptr::mut_ptr::{*mut T}::add (type may not carry the effect: raw-pointer argument, no output for the pointee)

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

## Attempt 2 — pass

Delta from attempt 1:
- resolved: 3
  - missing_model: no Lean model for standard-library item: core::ptr::swap (type may not carry the effect: raw-pointer argument, no output for the pointee)
  - missing_model: no Lean model for standard-library item: alloc::vec::{alloc::vec::Vec<T>}::as_mut_ptr (type may not carry the effect: raw-pointer argument, no output for the pointee)
  - missing_model: no Lean model for standard-library item: core::ptr::mut_ptr::{*mut T}::add (type may not carry the effect: raw-pointer argument, no output for the pointee)
- still failing: 0
- new: 0

Functions: swap_List translated
Axioms: none

Code diff from attempt 1:
```diff
--- attempt-1
+++ attempt-2
@@ -3,10 +3,9 @@
     let mut v = newList;
     let n = v.len();
     if n >= 2 {
-        let p = v.as_mut_ptr();
-        unsafe {
-            std::ptr::swap(p, p.add(n - 1));
-        }
+        let first = v[0];
+        v[0] = v[n - 1];
+        v[n - 1] = first;
     }
     v
 }
```
