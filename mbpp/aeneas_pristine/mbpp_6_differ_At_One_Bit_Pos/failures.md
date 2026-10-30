# mbpp_6_differ_At_One_Bit_Pos — failure log (aeneas: pristine)

## Attempt 1 — check:missing_model

Initial version.
Reasons:
- missing_model: no Lean model for standard-library item: core::num::{isize}::count_ones

Functions: differ_At_One_Bit_Pos translated
Axioms: core::num::{isize}::count_ones

Code:
```rust
/// Write a rsthon function to check whether the two numbers differ at one bit position only or not.
fn differ_At_One_Bit_Pos(a: isize, b: isize) -> bool {
    (a ^ b).count_ones() == 1
}
```

## Attempt 2 — pass

Delta from attempt 1:
- resolved: 1
  - missing_model: no Lean model for standard-library item: core::num::{isize}::count_ones
- still failing: 0
- new: 0

Functions: differ_At_One_Bit_Pos translated
Axioms: none

Code diff from attempt 1:
```diff
--- attempt-1
+++ attempt-2
@@ -1,4 +1,13 @@
 /// Write a rsthon function to check whether the two numbers differ at one bit position only or not.
 fn differ_At_One_Bit_Pos(a: isize, b: isize) -> bool {
-    (a ^ b).count_ones() == 1
+    let x = a ^ b;
+    if x == 0 {
+        return false;
+    }
+    if x == isize::MIN {
+        // Only the sign bit differs; x - 1 would overflow below.
+        return true;
+    }
+    // A single set bit is a power of two: clearing its lowest bit leaves zero.
+    (x & (x - 1)) == 0
 }
```
