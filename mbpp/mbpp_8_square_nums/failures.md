# mbpp_8_square_nums — failure log

## Attempt 1 — check:missing_context

Initial version.
Reasons:
- missing_context: Lean library lacks a model: `map` is not a field of structure `core.iter.traits.iterator.Iterator`
- missing_context: Lean library lacks a model: `collect` is not a field of structure `core.iter.traits.iterator.Iterator` 'Mbpp8SquareNums.square_nums' depends on axioms: [propext, Classical.choice, Quot.sound, Mbpp8SquareNums.Shared1Isize.Insts.CoreOpsArithMulShared0IsizeIsize.mul, Mbpp8SquareNums.core.iter.traits.iterator.Iterator.map.default, Mbpp8SquareNums.core.iter.adapters.map.Map.Insts.CoreIterTraitsIteratorIterator.next] 'Mbpp8SquareNums.square_nums.closure.Insts.CoreOpsFunctionFnOnceTupleShared0IsizeIsize.call_once' depends on axioms: [propext, Classical.choice, Quot.sound, Mbpp8SquareNums.Shared1Isize.Insts.CoreOpsArithMulShared
- missing_context: no Lean model for standard-library item: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul
- missing_context: no Lean model for standard-library item: core::iter::traits::iterator::Iterator::map
- missing_context: no Lean model for standard-library item: core::iter::adapters::map::{impl core::iter::traits::iterator::Iterator<B> for core::iter::adapters::map::Map<I, F>}::next

Functions: square_nums translated, {closure} translated
Axioms: core::ops::arith::{impl core::ops::arith::Mul<&'_0 isize, isize> for &'_1 isize}::mul, core::iter::traits::iterator::Iterator::map, core::iter::adapters::map::{impl core::iter::traits::iterator::Iterator<B> for core::iter::adapters::map::Map<I, F>}::next

Code:
```rust
/// Write a function to find squares of individual elements in a vector.
fn square_nums(nums: Vec<isize>) -> Vec<isize> {
    nums.iter().map(|x| x * x).collect()
}
```
