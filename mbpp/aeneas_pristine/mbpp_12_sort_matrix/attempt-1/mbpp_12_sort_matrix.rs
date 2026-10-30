/// Write a function to sort a given matrix in ascending order according to the sum of its rows.
fn sort_matrix(M: Vec<Vec<isize>>) -> Vec<Vec<isize>> {
    let mut m = M;
    m.sort_by_key(|row| row.iter().sum::<isize>());
    m
}
