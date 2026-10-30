# mbpp_3_is_not_prime — failure log (aeneas: mod)

## Attempt 1 — check:unsupported_code

Initial version.
Reasons:
- unsupported_code: library trait structure lacks the method (no model can be added from outside): `take_while` is not a field of structure `core.iter.traits.iterator.Iterator`
- unsupported_code: library trait structure lacks the method (no model can be added from outside): `any` is not a field of structure `core.iter.traits.iterator.Iterator`
- unsupported_code: library trait structure lacks the method (no model can be added from outside): `any` is not a field of structure `core.iter.traits.iterator.Iterator` 'Mbpp3IsNotPrime.is_not_prime' depends on axioms: [propext, Classical.choice, Quot.sound, Mbpp3IsNotPrime.Shared1Isize.Insts.CoreOpsArithMulShared0IsizeIsize.mul, Mbpp3IsNotPrime.core.iter.adapters.take_while.TakeWhile, Mbpp3IsNotPrime.core.iter.traits.iterator.Iterator.any.default, Mbpp3IsNotPrime.core.iter.traits.iterator.Iterator.take_while.default, Mbpp3IsNotPrime.core.ops.range.RangeFrom.Insts.CoreIterTraitsIteratorIterator.next, Mbpp3IsNotPrime.core.iter.adapters.take_while.TakeWhile.Insts.CoreIterTraitsIteratorIterat
- missing_model: no Lean model for standard-library item: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul
- missing_model: no Lean model for standard-library item: core::iter::adapters::take_while::TakeWhile
- missing_model: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::any
- missing_model: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::take_while
- missing_model: no Lean model for standard-library item: core::iter::range::{impl core::iter::traits::iterator::Iterator<A> for core::ops::range::RangeFrom<A>}::next
- missing_model: no Lean model for standard-library item: core::iter::adapters::take_while::{impl core::iter::traits::iterator::Iterator<Clause0_Item> for core::iter::adapters::take_while::TakeWhile<I, P>}::next

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
- resolved: 9
  - unsupported_code: library trait structure lacks the method (no model can be added from outside): `take_while` is not a field of structure `core.iter.traits.iterator.Iterator`
  - unsupported_code: library trait structure lacks the method (no model can be added from outside): `any` is not a field of structure `core.iter.traits.iterator.Iterator`
  - unsupported_code: library trait structure lacks the method (no model can be added from outside): `any` is not a field of structure `core.iter.traits.iterator.Iterator` 'Mbpp3IsNotPrime.is_not_prime' depends on axioms: [propext, Classical.choice, Quot.sound, Mbpp3IsNotPrime.Shared1Isize.Insts.CoreOpsArithMulShared0IsizeIsize.mul, Mbpp3IsNotPrime.core.iter.adapters.take_while.TakeWhile, Mbpp3IsNotPrime.core.iter.traits.iterator.Iterator.any.default, Mbpp3IsNotPrime.core.iter.traits.iterator.Iterator.take_while.default, Mbpp3IsNotPrime.core.ops.range.RangeFrom.Insts.CoreIterTraitsIteratorIterator.next, Mbpp3IsNotPrime.core.iter.adapters.take_while.TakeWhile.Insts.CoreIterTraitsIteratorIterat
  - missing_model: no Lean model for standard-library item: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul
  - missing_model: no Lean model for standard-library item: core::iter::adapters::take_while::TakeWhile
  - missing_model: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::any
  - missing_model: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::take_while
  - missing_model: no Lean model for standard-library item: core::iter::range::{impl core::iter::traits::iterator::Iterator<A> for core::ops::range::RangeFrom<A>}::next
  - missing_model: no Lean model for standard-library item: core::iter::adapters::take_while::{impl core::iter::traits::iterator::Iterator<Clause0_Item> for core::iter::adapters::take_while::TakeWhile<I, P>}::next
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
