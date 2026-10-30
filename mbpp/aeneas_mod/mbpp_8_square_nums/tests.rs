fn main() {
    let candidate = square_nums;
    assert_eq!(candidate(vec![1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), vec![1, 4, 9, 16, 25, 36, 49, 64, 81, 100]);
    assert_eq!(candidate(vec![10, 20, 30]), vec![100, 400, 900]);
    assert_eq!(candidate(vec![12, 15]), vec![144, 225]);
}
