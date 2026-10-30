fn main() {
    let candidate = differ_At_One_Bit_Pos;
    assert_eq!(candidate(13, 9), true);
    assert_eq!(candidate(15, 8), false);
    assert_eq!(candidate(2, 4), false);
    assert_eq!(candidate(2, 3), true);
    assert_eq!(candidate(5, 1), true);
    assert_eq!(candidate(1, 5), true);
}
