# mbpp_11_remove_Occ — failure log

## Attempt 1 — check:unsupported_code

Initial version.
Reasons:
- unsupported_code: Aeneas: Unimplemented — in `core::str::{str}::rfind` at /rustc/library/core/src/str/mod.rs:1542 (`pub fn rfind<P: Pattern>(&self, pat: P) -> Option<usize>`), used from mbpp_11_remove_Occ.rs:8:15
- unsupported_code: Aeneas: Unimplemented at /rustc/library/core/src/str/pattern.rs:99 (`pub trait Pattern: Sized {`)
- unsupported_code: Aeneas: Aeneas aborted with exception Aeneas.Errors.CFailure(_) in Aeneas__SymbolicToPureTypes.translate_fwd_ty (symbolic/SymbolicToPureTypes.ml:392); no functions were translated

Functions: remove_Occ missing, {closure} missing, {closure} missing, {closure} missing, {closure} missing
Axioms: none

Code:
```rust
/// Write a rsthon function to remove first and last occurrence of a given character from the string.
fn remove_Occ(s: String, ch: String) -> String {
    let c = match ch.chars().next() {
        Some(c) => c,
        None => return s,
    };
    let first = s.find(c);
    let last = s.rfind(c);
    s.char_indices()
        .filter(|&(i, _)| Some(i) != first && Some(i) != last)
        .map(|(_, x)| x)
        .collect()
}
```
