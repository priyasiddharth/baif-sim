/// Write a function to find the n largest integers from a given vector of numbers, returned in descending order.
fn heap_queue_largest(nums: Vec<isize>, n: isize) -> Vec<isize> {
    let mut sorted = nums;
    sorted.sort_unstable_by(|a, b| b.cmp(a));
    sorted.truncate(n as usize);
    sorted
}
