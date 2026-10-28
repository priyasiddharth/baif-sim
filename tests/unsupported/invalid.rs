//! Invalid Rust: type error, rejected by rustc before Charon translates anything.
pub fn bad(x: u32) -> u32 {
    x + "one"
}
