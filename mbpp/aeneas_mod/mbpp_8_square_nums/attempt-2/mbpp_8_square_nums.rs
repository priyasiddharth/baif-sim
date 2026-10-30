/// Write a function to find squares of individual elements in a vector.
fn square_nums(nums: Vec<isize>) -> Vec<isize> {
    let mut out: Vec<isize> = Vec::new();
    let mut i = 0;
    while i < nums.len() {
        let x = nums[i];
        out.push(x * x);
        i += 1;
    }
    out
}
