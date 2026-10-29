# mbpp_11_remove_Occ: a String problem hits three distinct Aeneas limits

Fourth MBPP problem (`fn remove_Occ(s: String, ch: String) -> String`),
chosen to leave the integer/`Vec<isize>` comfort zone. Stopped at attempt 4:
no code can do better, see the last [OBS].

[OBS 2026-10-28] Attempt 1 (`s.find(c)`/`s.rfind(c)` + `char_indices().filter().collect()`,
tests pass): Aeneas `Unimplemented` while translating the *signature* of
`core::str::{str}::rfind` (`pub fn rfind<P: Pattern>(..)`, core/src/str/mod.rs:1542)
and the `Pattern` trait itself (pattern.rs:99), then an uncaught
`Aeneas.Errors.CFailure` in `SymbolicToPureTypes.translate_fwd_ty`
(symbolic/SymbolicToPureTypes.ml:392) — nothing translated.
Our reading: `Pattern::Searcher<'a>` is a lifetime-GAT; anything taking a
`P: Pattern` (`find`, `rfind`, `contains`, `split`, `replace`, …) is
unsupported Rust for Aeneas at this version.

[OBS 2026-10-28] Attempt 2 (`for x in s.chars()` loops, `String::new`/`push`):
"Could not match the contexts" at the `for` loop (lines 9–13).
Attempt 3 (loops rewritten over a collected `Vec<char>`): same error, now at
`chars[i] == c` inside a plain `while`. Scratch variant with `c` taken from a
collected `Vec<char>` instead of `ch.chars().next()`: error gone. A minimal
`count(s, c: char)` with the same `Vec<char>`/`while`/`==` loop translates.
[HYP → confirmed 2026-10-29, see 2026-10-29-dataset-pinned-and-square-nums.md]
The `Option<char>` returned by `Chars::next` keeps the borrow
abstraction of `ch` alive in the symbolic environment, and the loop join
cannot match it; the `Vec<char>` route owns its values. Confirmed with
`-log InterpJoin,InterpMatchCtxs`: it is the `Chars::next` call's
abstraction, and the precise failure is a missing matcher case for an
ended loan projector, not the borrow of `ch` as such (abs@0/abs@1, the
`Deref` and `chars()` abstractions, match fine).

[OBS 2026-10-28] With the join problem gone, Aeneas emits ill-typed Lean for
`skip = seen == 1 || seen == total` inside the loop body:
`let b ← if seen2 = 1#i32 then ok true else ok (seen2 = total)` — the else
branch is a `Prop` where `Bool` is expected ("Application type mismatch").
The same statement standalone, inside an `if`, or returned in a tuple
translates; it needs the loop. Fixture: `tests/unsupported/or_in_loop_bool.rs`
(verdict 4 `toolchain_problem`, the first real one). Workaround:
`if seen == 1 || seen == total { skip = true; }`. [OPEN] report upstream.

[OBS 2026-10-28] Attempt 4 (Vec<char> for both strings, branch instead of
stored `||`): `remove_Occ translated`, Lean type-checks, exactly three
axioms — `String::new`, `String::push`, `Deref<str> for String`. That is the
ceiling: the Lean library models only the `String` type, `str::chars`,
`Chars::next` and `Chars::collect` (into `Vec<char>`) — grep
`aeneas/src/extract/ExtractBuiltinLean.ml` for `string` — so every function
that *builds* a `String` carries at least `new`+`push` as axioms. Verdict
`missing_context`, problem recorded as unresolved after 4 attempts.

[OBS 2026-10-28] check.py changes this forced: Aeneas errors now carry the
item name and user-code use site (folded in from the "because of previous
error" warning), the `/rustc/library/...` path is resolved to the
toolchain's rust-src and the source line quoted, an uncaught exception is
its own error, and Lean multi-line diagnostics are captured whole.
`result.json` dropped (duplicate of `check.json`; user's call).

## Why this matters

Strings are where MBPP-style code stops being translatable at all, and the
failure mode is not "missing model" but three different ones (type
translation crash, loop-join failure, codegen bug) — each needing a
different rewrite. A first-attempt guide must say: no `Pattern` methods, no
borrowing iterators across loop iterations, no stored `||`/`&&` in loops,
and expect `String` construction to be axiomatic.

## See also

- 2026-10-28-mbpp-loop-first-three-problems.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
- ../../durable/opaque-functions-become-axioms-or-lean-lib-models.md
