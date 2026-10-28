//! Unsupported by Charon: `async fn` desugars to a coroutine.

pub async fn double(x: u32) -> u32 {
    x * 2
}
