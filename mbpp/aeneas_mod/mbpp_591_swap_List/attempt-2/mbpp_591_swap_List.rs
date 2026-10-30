/// Write a rsthon function to interchange the first and last elements in a vector.
fn swap_List(newList: Vec<isize>) -> Vec<isize> {
    let mut v = newList;
    let n = v.len();
    if n >= 2 {
        let first = v[0];
        v[0] = v[n - 1];
        v[n - 1] = first;
    }
    v
}
