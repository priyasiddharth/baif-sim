//! Missing context: refers to a crate and a function that are not provided.
use helper::scale;

pub fn twice(x: u32) -> u32 {
    scale(x, 2)
}
