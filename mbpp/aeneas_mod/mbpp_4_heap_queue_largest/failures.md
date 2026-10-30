# mbpp_4_heap_queue_largest — failure log (aeneas: mod)

## Attempt 1 — check:missing_context

Initial version.
Reasons:
- missing_context: no Lean model for standard-library item: alloc::vec::{alloc::vec::Vec<T>}::truncate
- missing_context: no Lean model for standard-library item: core::slice::{[T

Functions: heap_queue_largest translated, {closure} translated
Axioms: alloc::vec::{alloc::vec::Vec<T>}::truncate, core::slice::{[T

Code:
```rust
/// Write a function to find the n largest integers from a given vector of numbers, returned in descending order.
fn heap_queue_largest(nums: Vec<isize>, n: isize) -> Vec<isize> {
    let mut sorted = nums;
    sorted.sort_unstable_by(|a, b| b.cmp(a));
    sorted.truncate(n as usize);
    sorted
}
```

## Attempt 2 — pass

Delta from attempt 1:
- resolved: 2
  - missing_context: no Lean model for standard-library item: alloc::vec::{alloc::vec::Vec<T>}::truncate
  - missing_context: no Lean model for standard-library item: core::slice::{[T
- still failing: 0
- new: 0

Functions: heap_queue_largest translated
Axioms: none

Code diff from attempt 1:
```diff
--- attempt-1
+++ attempt-2
@@ -1,7 +1,32 @@
 /// Write a function to find the n largest integers from a given vector of numbers, returned in descending order.
 fn heap_queue_largest(nums: Vec<isize>, n: isize) -> Vec<isize> {
-    let mut sorted = nums;
-    sorted.sort_unstable_by(|a, b| b.cmp(a));
-    sorted.truncate(n as usize);
-    sorted
+    let mut v = nums;
+    let len = v.len();
+    let mut want = if n < 0 { 0 } else { n as usize };
+    if want > len {
+        want = len;
+    }
+    // Selection sort of the first `want` positions, descending.
+    let mut i = 0;
+    while i < want {
+        let mut best = i;
+        let mut j = i + 1;
+        while j < len {
+            if v[j] > v[best] {
+                best = j;
+            }
+            j += 1;
+        }
+        let tmp = v[i];
+        v[i] = v[best];
+        v[best] = tmp;
+        i += 1;
+    }
+    let mut out = Vec::new();
+    let mut k = 0;
+    while k < want {
+        out.push(v[k]);
+        k += 1;
+    }
+    out
 }
```
