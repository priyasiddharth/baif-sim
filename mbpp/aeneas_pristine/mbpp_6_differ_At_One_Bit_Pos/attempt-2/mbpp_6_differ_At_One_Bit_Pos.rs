/// Write a rsthon function to check whether the two numbers differ at one bit position only or not.
fn differ_At_One_Bit_Pos(a: isize, b: isize) -> bool {
    let x = a ^ b;
    if x == 0 {
        return false;
    }
    if x == isize::MIN {
        // Only the sign bit differs; x - 1 would overflow below.
        return true;
    }
    // A single set bit is a power of two: clearing its lowest bit leaves zero.
    (x & (x - 1)) == 0
}
