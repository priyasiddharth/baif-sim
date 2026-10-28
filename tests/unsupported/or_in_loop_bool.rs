//! Toolchain problem (Aeneas codegen bug): a short-circuit `||` stored into a
//! bool inside a loop body is emitted as
//!     let b ← if seen2 = 1#i32 then ok true else ok (seen2 = total)
//! where `seen2 = total` is a Lean `Prop`, so the generated file fails to
//! type-check ("Application type mismatch ... Prop ... Bool"). The same
//! statement outside a loop translates fine; branching on the condition
//! (`if a || b { skip = true; }`) instead of storing it avoids the bug.
pub fn count_skips(chars: Vec<char>, c: char, total: i32) -> i32 {
    let mut seen = 0;
    let mut skips = 0;
    let mut j = 0;
    while j < chars.len() {
        let x = chars[j];
        let mut skip = false;
        if x == c {
            seen += 1;
            skip = seen == 1 || seen == total;
        }
        if skip {
            skips += 1;
        }
        j += 1;
    }
    skips
}
