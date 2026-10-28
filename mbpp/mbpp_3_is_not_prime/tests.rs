fn main() {
    let candidate = is_not_prime;
    assert_eq!(candidate(2), false);
    assert_eq!(candidate(10), true);
    assert_eq!(candidate(35), true);
    assert_eq!(candidate(37), false);
}
