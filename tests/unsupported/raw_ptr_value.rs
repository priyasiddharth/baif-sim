//! Missing model (exit 5) with a raw-pointer note: a raw pointer is created
//! and offset but never read or written through, so Aeneas accepts it (only
//! dereferencing is unsupported, see raw_ptr.rs). `Vec::as_mut_ptr` and
//! `*mut T::add` have no Lean model and become axioms; because their
//! signatures mention `MutRawPtr`, check.py adds a note that the axiom's type
//! may not carry an effect. Here nothing was written, so the translation is
//! merely incomplete; in mbpp_591_swap_List attempt 1 (`ptr::swap`) the same
//! note marks a translation that is wrong. The note is a hint, not a verdict:
//! the tool cannot tell the two apart.

pub fn second_slot(v: &mut Vec<u32>) -> usize {
    let p = v.as_mut_ptr();
    let _q = unsafe { p.add(1) };
    v.len()
}
