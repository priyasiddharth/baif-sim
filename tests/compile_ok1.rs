//! Small example covering features Aeneas supports: structs, enums,
//! pattern matching, loops, mutable borrows, slices and `Vec`.

pub struct Point {
    pub x: i32,
    pub y: i32,
}

pub enum Shape {
    Circle(u32),
    Rect { w: u32, h: u32 },
}

pub fn area(s: &Shape) -> u32 {
    match s {
        Shape::Circle(r) => 3 * *r * *r,
        Shape::Rect { w, h } => *w * *h,
    }
}

/// Mutable borrow: the Lean translation returns the updated point.
pub fn translate(p: &mut Point, dx: i32, dy: i32) {
    p.x += dx;
    p.y += dy;
}

pub fn sum(v: &[u32]) -> u32 {
    let mut total = 0;
    let mut i = 0;
    while i < v.len() {
        total += v[i];
        i += 1;
    }
    total
}

pub fn evens(n: u32) -> Vec<u32> {
    let mut v = Vec::new();
    let mut i = 0;
    while i < n {
        v.push(2 * i);
        i += 1;
    }
    v
}
