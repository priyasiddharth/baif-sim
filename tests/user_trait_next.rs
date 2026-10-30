//! Translates (exit 0): a user type implementing the builtin `Iterator`
//! trait, using only `next`, which the Aeneas library's `Iterator` structure
//! has a field for. Contrast tests/unsupported/user_trait_any.rs.

pub struct Up(pub u32);

impl Iterator for Up {
    type Item = u32;
    fn next(&mut self) -> Option<u32> {
        self.0 += 1;
        Some(self.0)
    }
}

pub fn step(mut u: Up) -> Option<u32> {
    u.next()
}
