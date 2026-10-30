fn main() {
    let candidate = remove_Occ;
    assert_eq!(candidate(String::from("hello"), String::from("l")), String::from("heo"));
    assert_eq!(candidate(String::from("abcda"), String::from("a")), String::from("bcd"));
    assert_eq!(candidate(String::from("PHP"), String::from("P")), String::from("H"));
}
