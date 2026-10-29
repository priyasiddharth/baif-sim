// FAILS with pristine Aeneas (399081f): "Could not match the contexts" at the `while`.
//
// The only thing that matters is the line marked (*): `next` takes `&mut self`
// on a temporary `Chars`. The mutable borrow ends right after the call, and the
// region abstraction left behind for that call holds an *ended* loan projector.
// The loop-context matcher has no case for ended loan projectors, so when it
// checks the loop fixed point against itself, that abstraction cannot be paired
// with its own copy. See README.md.
fn count_first(s: Vec<char>, ch: String) -> i32 {
    let c = match ch.chars().next() {   // (*) &mut self on a temporary
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
