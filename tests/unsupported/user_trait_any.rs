//! Unsupported by the Aeneas Lean library's trait encoding (exit 1).
//!
//! `Iterator` is a *builtin* trait: Aeneas does not declare it in the output
//! but maps it to the hand-written structure in
//! aeneas/backends/lean/Aeneas/Std/Core/Iter.lean, which has fields only for
//! `next`, `step_by`, `enumerate`, `take` ("adding more fields like rev leads
//! to a circularity"). The generated `impl_def` lists one field per method the
//! program used, so calling `any` makes Lean fail with
//! "`any` is not a field of structure `core.iter.traits.iterator.Iterator`".
//! No Lean model can be added from outside Aeneas; the call must go.
//! Sibling tests/user_trait_next.rs uses only `next` and translates.

pub struct Up(pub u32);

impl Iterator for Up {
    type Item = u32;
    fn next(&mut self) -> Option<u32> {
        self.0 += 1;
        Some(self.0)
    }
}

pub fn past_three(mut u: Up) -> bool {
    u.any(|x| x > 3)
}
