//! Translates (exit 0): the index-arena encoding of a cyclic structure.
//! Two nodes point at each other through `usize` handles into a `Vec`, which
//! `Box` ownership cannot express and `Rc<RefCell<_>>` cannot translate.
pub struct Node {
    pub value: u32,
    pub next: usize, // handle = index into Arena::nodes
}

pub struct Arena {
    pub nodes: Vec<Node>,
}

pub fn add(a: &mut Arena, value: u32, next: usize) -> usize {
    a.nodes.push(Node { value, next });
    a.nodes.len() - 1
}

/// Sum the values seen while following `next` for `steps` hops.
pub fn walk(a: &Arena, start: usize, steps: u32) -> u32 {
    let mut i = start;
    let mut sum = 0;
    let mut k = 0;
    while k < steps {
        sum += a.nodes[i].value;
        i = a.nodes[i].next;
        k += 1;
    }
    sum
}

/// A two-node cycle: 1 -> 2 -> 1 -> ...; five hops sum to 7.
pub fn two_cycle() -> u32 {
    let mut a = Arena { nodes: Vec::new() };
    let x = add(&mut a, 1, 1);
    add(&mut a, 2, x);
    walk(&a, x, 5)
}
