/// Write a rsthon function to identify non-prime numbers.
fn is_not_prime(n: isize) -> bool {
    if n < 2 {
        return true;
    }
    (2..).take_while(|i| i * i <= n).any(|i| n % i == 0)
}
