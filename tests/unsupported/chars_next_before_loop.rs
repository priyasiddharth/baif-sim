// Expected verdict: unsupported_code (exit 1).
//
// Aeneas: "Could not match the contexts" at the `while`. The value `c` is
// obtained through `Chars::next(&mut ch.chars())` before the loop. At loop
// entry the environment still holds the region abstraction for that call,
// containing an *ended* loan projector (`AEndedProjLoans`). The loop-context
// matcher (aeneas/src/interp/InterpMatchCtxs.ml, MakeMatcher.match_tavalues,
// ASymbolic case) has arms only for AProjBorrows / AProjLoans, so matching
// the fixed point against itself fails. Confirmed from `-log InterpMatchCtxs`
// on 2026-10-29 (aeneas 399081f). Taking `c` from a collected Vec<char>
// instead (`let v: Vec<char> = ch.chars().collect(); v[0]`) translates.
fn count_first(s: Vec<char>, ch: String) -> i32 {
    let c = match ch.chars().next() {
        Some(c) => c,
        None => return 0,
    };
    let mut n = 0;
    let mut i = 0;
    while i < s.len() {
        if s[i] == c {
            n += 1;
        }
        i += 1;
    }
    n
}
