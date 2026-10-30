/// Write a rsthon function to remove first and last occurrence of a given character from the string.
fn remove_Occ(s: String, ch: String) -> String {
    let c = match ch.chars().next() {
        Some(c) => c,
        None => return s,
    };
    // Materialise the characters so the loops index a Vec instead of
    // holding a borrowing iterator across iterations.
    let chars: Vec<char> = s.chars().collect();
    let n = chars.len();
    let mut total = 0;
    let mut i = 0;
    while i < n {
        if chars[i] == c {
            total += 1;
        }
        i += 1;
    }
    let mut out = String::new();
    let mut seen = 0;
    let mut j = 0;
    while j < n {
        let x = chars[j];
        let mut skip = false;
        if x == c {
            seen += 1;
            skip = seen == 1 || seen == total;
        }
        if !skip {
            out.push(x);
        }
        j += 1;
    }
    out
}
