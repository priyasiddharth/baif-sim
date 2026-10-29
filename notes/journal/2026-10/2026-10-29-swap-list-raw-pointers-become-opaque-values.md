# mbpp_591_swap_List: raw pointers translate as opaque values, and lose the write

[OBS 2026-10-29] User asked for an MBPP test using raw pointers. None of
the 354 `mbpp-rs` rows mention `*const`/`*mut`/`unsafe`/`ptr`/`Box`/`Rc`
(MBPP is translated from Python, all safe types). Chose
`mbpp_591_swap_List` (swap first/last of a `Vec<isize>`) and wrote
attempt 1 *deliberately* with pointers, so it is a pointer probe, not a
first-attempt measurement:
`let p = v.as_mut_ptr(); unsafe { std::ptr::swap(p, p.add(n - 1)); }`.

[OBS 2026-10-29] Attempt 1 (tests pass) → `missing_context`, *not*
`unsupported_code` as I predicted. Aeneas has a `MutRawPtr T` type and
translates pointer *values*; it only rejects *dereferencing* one
("Aeneas does not yet support dereferencing raw pointers", the
`tests/unsupported/raw_ptr.rs` fixture). Here there is no deref in user
code, so three axioms: `core::ptr::swap : MutRawPtr T → MutRawPtr T →
Result Unit`, `<*mut T>::add`, `Vec::as_mut_ptr : Vec T → Result (MutRawPtr T × Vec T)`.
The generated `swap_List` returns the `Vec` that came out of
`as_mut_ptr`, before the swap: nothing connects writing through the
pointer to the vector's contents. So even with models for the three
axioms the function's behaviour is unprovable — the pointer write is
lost by construction, not just unmodelled. Verdict `missing_context`
understates this; [OPEN] should `check.py` flag any `MutRawPtr`/`ConstRawPtr`
in a signature as `unsupported_code`?

[OBS 2026-10-29] Attempt 2: temporary + two index assignments →
`translates`, no axioms, pristine and mod. (`Vec::swap` avoided: no
model.) Both attempts added to `tests/expected.json` (36 verdicts).

## See also

- 2026-10-29-dataset-pinned-and-square-nums.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
