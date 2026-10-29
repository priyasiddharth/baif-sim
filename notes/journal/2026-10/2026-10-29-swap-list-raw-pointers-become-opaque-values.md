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
understates this.

[OBS 2026-10-29] Discussed with the user why it might be re-classified.
`missing_context` promises "supply models and it works"; here no model can
work, because the `Vec` is not an input or output of `ptr::swap`, so the
next repair step would be sent to write impossible models. The repair
that works is a rewrite, i.e. what `unsupported_code` says. But flagging
every `MutRawPtr`/`ConstRawPtr` type is too blunt (pointer values only
compared/cast/passed through may translate meaningfully). Narrower
candidate rule: calls to pointer read/write functions (`ptr::swap`,
`ptr::write`, `ptr::read`, `ptr::copy*`, …) → `unsupported_code`, reason
"effect through raw pointer is not modelled"; still a name list, misses
user `unsafe` code. [OPEN] decided: leave `check.py` unchanged until a
second case appears — one data point does not justify a rule.

[OBS 2026-10-29] Attempt 2: temporary + two index assignments →
`translates`, no axioms, pristine and mod. (`Vec::swap` avoided: no
model.) Both attempts added to `tests/expected.json` (36 verdicts).

## See also

- 2026-10-29-dataset-pinned-and-square-nums.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
