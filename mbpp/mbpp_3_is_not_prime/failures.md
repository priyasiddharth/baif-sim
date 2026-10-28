# mbpp_3_is_not_prime — failure log

## Attempt 1 — check:missing_context

Initial version.
Reasons:
- missing_context: Lean library lacks a model: `take_while` is not a field of structure `core.iter.traits.iterator.Iterator`
- missing_context: Lean library lacks a model: `any` is not a field of structure `core.iter.traits.iterator.Iterator`
- missing_context: no Lean model for standard-library item: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul
- missing_context: no Lean model for standard-library item: core::iter::adapters::take_while::TakeWhile
- missing_context: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::any
- missing_context: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::take_while
- missing_context: no Lean model for standard-library item: core::iter::range::{impl core::iter::traits::iterator::Iterator<A> for core::ops::range::RangeFrom<A>}::next
- missing_context: no Lean model for standard-library item: core::iter::adapters::take_while::{impl core::iter::traits::iterator::Iterator<Clause0_Item> for core::iter::adapters::take_while::TakeWhile<I, P>}::next

Functions: is_not_prime translated, {closure} translated, {closure} translated
Axioms: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul, core::iter::adapters::take_while::TakeWhile, core::iter::traits::iterator::Iterator::any, core::iter::traits::iterator::Iterator::take_while, core::iter::range::{impl core::iter::traits::iterator::Iterator<A> for core::ops::range::RangeFrom<A>}::next, core::iter::adapters::take_while::{impl core::iter::traits::iterator::Iterator<Clause0_Item> for core::iter::adapters::take_while::TakeWhile<I, P>}::next

Code:
```rust
/// Write a rsthon function to identify non-prime numbers.
fn is_not_prime(n: isize) -> bool {
    if n < 2 {
        return true;
    }
    (2..).take_while(|i| i * i <= n).any(|i| n % i == 0)
}
```

## Attempt 2 — pass

Delta from attempt 1:
- resolved: 8
  - missing_context: Lean library lacks a model: `take_while` is not a field of structure `core.iter.traits.iterator.Iterator`
  - missing_context: Lean library lacks a model: `any` is not a field of structure `core.iter.traits.iterator.Iterator`
  - missing_context: no Lean model for standard-library item: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul
  - missing_context: no Lean model for standard-library item: core::iter::adapters::take_while::TakeWhile
  - missing_context: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::any
  - missing_context: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::take_while
  - missing_context: no Lean model for standard-library item: core::iter::range::{impl core::iter::traits::iterator::Iterator<A> for core::ops::range::RangeFrom<A>}::next
  - missing_context: no Lean model for standard-library item: core::iter::adapters::take_while::{impl core::iter::traits::iterator::Iterator<Clause0_Item> for core::iter::adapters::take_while::TakeWhile<I, P>}::next
- still failing: 0
- new: 0

Functions: is_not_prime translated
Axioms: none

Code diff from attempt 1:
```diff
--- attempt-1
+++ attempt-2
@@ -3,5 +3,12 @@
     if n < 2 {
         return true;
     }
-    (2..).take_while(|i| i * i <= n).any(|i| n % i == 0)
+    let mut i: isize = 2;
+    while i * i <= n {
+        if n % i == 0 {
+            return true;
+        }
+        i += 1;
+    }
+    false
 }
```
