//! Unsupported by Aeneas: dereferencing a raw pointer.
//! Charon translates this fine; Aeneas rejects it.

pub fn second(data: &[u16; 4]) -> u16 {
    unsafe {
        let p = data.as_ptr();
        *p.add(1)
    }
}
