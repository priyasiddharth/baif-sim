// PASSES with pristine Aeneas (399081f): same function, one line changed.
//
// `last` takes `self` (by value), so the abstraction left behind for that call
// holds a *live* borrow projector, which the matcher does handle. The loop
// translates with signature `count_first_loop (s c n i)`; the leftover
// abstraction is not part of the loop interface at all.
// (`ch.chars().collect::<Vec<char>>()[0]` behaves the same; `ch.chars().nth(0)`
// fails like `next`, because `nth` also takes `&mut self`.)
fn count_first(s: Vec<char>, ch: String) -> i32 {
    let c = match ch.chars().last() {   // (*) self, by value
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
