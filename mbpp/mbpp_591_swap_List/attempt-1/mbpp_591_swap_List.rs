/// Write a rsthon function to interchange the first and last elements in a vector.
fn swap_List(newList: Vec<isize>) -> Vec<isize> {
    let mut v = newList;
    let n = v.len();
    if n >= 2 {
        let p = v.as_mut_ptr();
        unsafe {
            std::ptr::swap(p, p.add(n - 1));
        }
    }
    v
}
