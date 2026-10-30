fn main() {
    let candidate = swap_List;
    assert_eq!(candidate(vec![12, 35, 9, 56, 24]), vec![24, 35, 9, 56, 12]);
    assert_eq!(candidate(vec![1, 2, 3]), vec![3, 2, 1]);
    assert_eq!(candidate(vec![4, 5, 6]), vec![6, 5, 4]);
}
