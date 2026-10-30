fn main() {
    let candidate = sort_matrix;
    assert_eq!(candidate(vec![vec![1, 2, 3], vec![2, 4, 5], vec![1, 1, 1]]), vec![vec![1, 1, 1], vec![1, 2, 3], vec![2, 4, 5]]);
    assert_eq!(candidate(vec![vec![1, 2, 3], vec![-2, 4, -5], vec![1, -1, 1]]), vec![vec![-2, 4, -5], vec![1, -1, 1], vec![1, 2, 3]]);
    assert_eq!(candidate(vec![vec![5, 8, 9], vec![6, 4, 3], vec![2, 1, 4]]), vec![vec![2, 1, 4], vec![6, 4, 3], vec![5, 8, 9]]);
}
