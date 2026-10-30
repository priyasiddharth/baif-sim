/// Write a rsthon function to remove first and last occurrence of a given character from the string.
fn remove_Occ(s: String, ch: String) -> String {
    let c = match ch.chars().next() {
        Some(c) => c,
        None => return s,
    };
    // Count occurrences so we know which one is the last.
    let mut total = 0;
    for x in s.chars() {
        if x == c {
            total += 1;
        }
    }
    let mut out = String::new();
    let mut seen = 0;
    for x in s.chars() {
        let mut skip = false;
        if x == c {
            seen += 1;
            skip = seen == 1 || seen == total;
        }
        if !skip {
            out.push(x);
        }
    }
    out
}
