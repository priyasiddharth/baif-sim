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

## Attempt 2 — check:unsupported_code

Delta from attempt 1:
- resolved: 3
  - unsupported_code: Aeneas: Unimplemented — in `core::str::{str}::rfind` at /rustc/library/core/src/str/mod.rs:1542 (`pub fn rfind<P: Pattern>(&self, pat: P) -> Option<usize>`), used from mbpp_11_remove_Occ.rs:8:15
  - unsupported_code: Aeneas: Unimplemented at /rustc/library/core/src/str/pattern.rs:99 (`pub trait Pattern: Sized {`)
  - unsupported_code: Aeneas: Aeneas aborted with exception Aeneas.Errors.CFailure(_) in Aeneas__SymbolicToPureTypes.translate_fwd_ty (symbolic/SymbolicToPureTypes.ml:392); no functions were translated
- still failing: 0
- new: 4
  - unsupported_code: Aeneas: Could not match the contexts — in `mbpp_11_remove_Occ::remove_Occ` at mbpp_11_remove_Occ.rs:9, used from mbpp_11_remove_Occ.rs:9:4
  - missing_context: no Lean model for standard-library item: alloc::string::{alloc::string::String}::new
  - missing_context: no Lean model for standard-library item: alloc::string::{alloc::string::String}::push
  - missing_context: no Lean model for standard-library item: alloc::string::{impl core::ops::deref::Deref<str> for alloc::string::String}::deref

Functions: remove_Occ sorry
Axioms: alloc::string::{alloc::string::String}::new, alloc::string::{alloc::string::String}::push, alloc::string::{impl core::ops::deref::Deref<str> for alloc::string::String}::deref

Code diff from attempt 1:
```diff
--- attempt-1
+++ attempt-2
@@ -4,10 +4,24 @@
         Some(c) => c,
         None => return s,
     };
-    let first = s.find(c);
-    let last = s.rfind(c);
-    s.char_indices()
-        .filter(|&(i, _)| Some(i) != first && Some(i) != last)
-        .map(|(_, x)| x)
-        .collect()
+    // Count occurrences so we know which one is the last.
+    let mut total = 0;
+    for x in s.chars() {
+        if x == c {
+            total += 1;
+        }
+    }
+    let mut out = String::new();
+    let mut seen = 0;
+    for x in s.chars() {
+        let mut skip = false;
+        if x == c {
+            seen += 1;
+            skip = seen == 1 || seen == total;
+        }
+        if !skip {
+            out.push(x);
+        }
+    }
+    out
 }
```
