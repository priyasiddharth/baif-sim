/// Write a rsthon function to remove first and last occurrence of a given character from the string.
fn remove_Occ(s: String, ch: String) -> String {
    // Take the character via a materialised Vec<char> rather than a Chars
    // iterator, so no borrow of `ch` outlives this statement.
    let chv: Vec<char> = ch.chars().collect();
    if chv.len() == 0 {
        return s;
    }
    let c = chv[0];
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
        // Branch on the condition instead of storing `a || b` in a bool.
        let mut skip = false;
        if x == c {
            seen += 1;
            if seen == 1 || seen == total {
                skip = true;
            }
        }
        if !skip {
            out.push(x);
        }
        j += 1;
    }
    out
}
