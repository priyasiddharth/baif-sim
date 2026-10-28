# Charon and Aeneas exit codes do not tell you whether code translated

**Verified against:** aeneas 399081f (nightly-2026.10.28), charon 2ec7e96, rustc nightly-2026-09-17, Lean v4.35.0
**Last verified:** 2026-10-28
**Status:** repeated (3 cases, same version)

[EMP] Charon exits 0 on code it cannot translate. `async fn` produced only
      `warning: Coroutine types are not supported yet` / `Coroutines are not
      supported`, exit 0, and an LLBC whose function reads
      `pub fn double(_1: u32) -> type_error("...") = error("...")`.
      Aeneas then fails with "Found type error in the output of charon" +
      "Internal error: please file an issue". (tests/unsupported/async_fn.rs)

[EMP] Aeneas exits 0 while emitting axioms. `3 * r * r` with `r: &u32` gave an
      `axiom ... Mul<u32, &u32> ... mul` and only a warning; exit 0.
      Seen again in MBPP attempt 1 (`&isize * &isize` inside closures).
      (tests/unsupported/ref_mul.rs, mbpp/mbpp_3_is_not_prime/attempt-1)

[EMP] Aeneas exits 1 but still writes a partial file: the failed body becomes
      `sorry` (`raw_ptr.rs` → `def second ... := do sorry`), or the function is
      simply absent (async case: empty namespace).

## Reading

Status must come from: rustc/Charon `warning:`/`error:` lines and
`type_error(`/`error(` markers in the LLBC; Aeneas `[Error]` blocks; and the
Lean file itself (`sorry`, `axiom`, missing defs, `#print axioms`). This is
what `tools/check.py` does.

## See also

- ../durable/how-to-translate-a-rust-file-to-lean-and-check-it.md
