/// Write a function to find the n largest integers from a given vector of numbers, returned in descending order.
fn heap_queue_largest(nums: Vec<isize>, n: isize) -> Vec<isize> {
    let mut v = nums;
    let len = v.len();
    let mut want = if n < 0 { 0 } else { n as usize };
    if want > len {
        want = len;
    }
    // Selection sort of the first `want` positions, descending.
    let mut i = 0;
    while i < want {
        let mut best = i;
        let mut j = i + 1;
        while j < len {
            if v[j] > v[best] {
                best = j;
            }
            j += 1;
        }
        let tmp = v[i];
        v[i] = v[best];
        v[best] = tmp;
        i += 1;
    }
    let mut out = Vec::new();
    let mut k = 0;
    while k < want {
        out.push(v[k]);
        k += 1;
    }
    out
}
