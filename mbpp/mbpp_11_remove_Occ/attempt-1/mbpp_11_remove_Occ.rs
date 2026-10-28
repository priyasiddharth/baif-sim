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
