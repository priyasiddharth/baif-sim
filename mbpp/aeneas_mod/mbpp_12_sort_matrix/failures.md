# mbpp_12_sort_matrix — failure log (aeneas: mod)

## Attempt 1 — check:missing_model

Initial version.
Reasons:
- missing_model: no Lean model for standard-library item: core::iter::traits::accum::{impl core::iter::traits::accum::Sum<&'a isize> for isize}::sum
- missing_model: no Lean model for standard-library item: alloc::slice::{[T
- missing_model: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::sum

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

## Attempt 2 — pass

Delta from attempt 1:
- resolved: 3
  - missing_model: no Lean model for standard-library item: core::iter::traits::accum::{impl core::iter::traits::accum::Sum<&'a isize> for isize}::sum
  - missing_model: no Lean model for standard-library item: alloc::slice::{[T
  - missing_model: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::sum
- still failing: 0
- new: 0

Functions: sort_matrix translated
Axioms: none

Code diff from attempt 1:
```diff
--- attempt-1
+++ attempt-2
@@ -1,6 +1,47 @@
 /// Write a function to sort a given matrix in ascending order according to the sum of its rows.
 fn sort_matrix(M: Vec<Vec<isize>>) -> Vec<Vec<isize>> {
-    let mut m = M;
-    m.sort_by_key(|row| row.iter().sum::<isize>());
-    m
+    let n = M.len();
+    // Row sums by index loops (no Iterator::sum).
+    let mut sums: Vec<isize> = Vec::new();
+    let mut i = 0;
+    while i < n {
+        let mut s = 0;
+        let mut j = 0;
+        while j < M[i].len() {
+            s += M[i][j];
+            j += 1;
+        }
+        sums.push(s);
+        i += 1;
+    }
+    // Stable selection: repeatedly take the unused row with the smallest sum
+    // and copy it into the output (no sort/swap/clone).
+    let mut used: Vec<bool> = Vec::new();
+    let mut k = 0;
+    while k < n {
+        used.push(false);
+        k += 1;
+    }
+    let mut out: Vec<Vec<isize>> = Vec::new();
+    let mut taken = 0;
+    while taken < n {
+        let mut best = n;
+        let mut r = 0;
+        while r < n {
+            if !used[r] && (best == n || sums[r] < sums[best]) {
+                best = r;
+            }
+            r += 1;
+        }
+        used[best] = true;
+        let mut row: Vec<isize> = Vec::new();
+        let mut c = 0;
+        while c < M[best].len() {
+            row.push(M[best][c]);
+            c += 1;
+        }
+        out.push(row);
+        taken += 1;
+    }
+    out
 }
```
