/// Write a rsthon function to identify non-prime numbers.
fn is_not_prime(n: isize) -> bool {
    if n < 2 {
        return true;
    }
    let mut i: isize = 2;
    while i * i <= n {
        if n % i == 0 {
            return true;
        }
        i += 1;
    }
    false
}
