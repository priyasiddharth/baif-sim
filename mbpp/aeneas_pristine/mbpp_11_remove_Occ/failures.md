# mbpp_11_remove_Occ — failure log (aeneas: pristine)

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

## Attempt 3 — check:unsupported_code

Delta from attempt 2:
- resolved: 1
  - unsupported_code: Aeneas: Could not match the contexts — in `mbpp_11_remove_Occ::remove_Occ` at mbpp_11_remove_Occ.rs:9, used from mbpp_11_remove_Occ.rs:9:4
- still failing: 3
  - missing_context: no Lean model for standard-library item: alloc::string::{alloc::string::String}::new
  - missing_context: no Lean model for standard-library item: alloc::string::{alloc::string::String}::push
  - missing_context: no Lean model for standard-library item: alloc::string::{impl core::ops::deref::Deref<str> for alloc::string::String}::deref
- new: 1
  - unsupported_code: Aeneas: Could not match the contexts — in `mbpp_11_remove_Occ::remove_Occ` at mbpp_11_remove_Occ.rs:14, used from mbpp_11_remove_Occ.rs:14:8

Functions: remove_Occ sorry
Axioms: alloc::string::{alloc::string::String}::new, alloc::string::{alloc::string::String}::push, alloc::string::{impl core::ops::deref::Deref<str> for alloc::string::String}::deref

Code diff from attempt 2:
```diff
--- attempt-2
+++ attempt-3
@@ -4,16 +4,23 @@
         Some(c) => c,
         None => return s,
     };
-    // Count occurrences so we know which one is the last.
+    // Materialise the characters so the loops index a Vec instead of
+    // holding a borrowing iterator across iterations.
+    let chars: Vec<char> = s.chars().collect();
+    let n = chars.len();
     let mut total = 0;
-    for x in s.chars() {
-        if x == c {
+    let mut i = 0;
+    while i < n {
+        if chars[i] == c {
             total += 1;
         }
+        i += 1;
     }
     let mut out = String::new();
     let mut seen = 0;
-    for x in s.chars() {
+    let mut j = 0;
+    while j < n {
+        let x = chars[j];
         let mut skip = false;
         if x == c {
             seen += 1;
@@ -22,6 +29,7 @@
         if !skip {
             out.push(x);
         }
+        j += 1;
     }
     out
 }
```

## Attempt 4 — check:missing_context

Delta from attempt 3:
- resolved: 1
  - unsupported_code: Aeneas: Could not match the contexts — in `mbpp_11_remove_Occ::remove_Occ` at mbpp_11_remove_Occ.rs:14, used from mbpp_11_remove_Occ.rs:14:8
- still failing: 3
  - missing_context: no Lean model for standard-library item: alloc::string::{alloc::string::String}::new
  - missing_context: no Lean model for standard-library item: alloc::string::{alloc::string::String}::push
  - missing_context: no Lean model for standard-library item: alloc::string::{impl core::ops::deref::Deref<str> for alloc::string::String}::deref
- new: 0

Functions: remove_Occ translated
Axioms: alloc::string::{alloc::string::String}::new, alloc::string::{alloc::string::String}::push, alloc::string::{impl core::ops::deref::Deref<str> for alloc::string::String}::deref

Code diff from attempt 3:
```diff
--- attempt-3
+++ attempt-4
@@ -1,11 +1,12 @@
 /// Write a rsthon function to remove first and last occurrence of a given character from the string.
 fn remove_Occ(s: String, ch: String) -> String {
-    let c = match ch.chars().next() {
-        Some(c) => c,
-        None => return s,
-    };
-    // Materialise the characters so the loops index a Vec instead of
-    // holding a borrowing iterator across iterations.
+    // Take the character via a materialised Vec<char> rather than a Chars
+    // iterator, so no borrow of `ch` outlives this statement.
+    let chv: Vec<char> = ch.chars().collect();
+    if chv.len() == 0 {
+        return s;
+    }
+    let c = chv[0];
     let chars: Vec<char> = s.chars().collect();
     let n = chars.len();
     let mut total = 0;
@@ -21,10 +22,13 @@
     let mut j = 0;
     while j < n {
         let x = chars[j];
+        // Branch on the condition instead of storing `a || b` in a bool.
         let mut skip = false;
         if x == c {
             seen += 1;
-            skip = seen == 1 || seen == total;
+            if seen == 1 || seen == total {
+                skip = true;
+            }
         }
         if !skip {
             out.push(x);
```
