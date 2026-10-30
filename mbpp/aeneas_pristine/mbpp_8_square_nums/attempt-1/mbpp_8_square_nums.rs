/// Write a function to find squares of individual elements in a vector.
fn square_nums(nums: Vec<isize>) -> Vec<isize> {
    nums.iter().map(|x| x * x).collect()
}
