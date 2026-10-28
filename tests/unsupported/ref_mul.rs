//! Missing context: `u32 * &u32` uses a `Mul` impl from `core` that the Aeneas
//! Lean library does not model, so it becomes an axiom. Writing `*r` avoids it.
pub fn sq(r: &u32) -> u32 {
    3 * r * r
}
