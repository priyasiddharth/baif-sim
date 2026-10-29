# Pins moved to aeneas de16f3c / charon 373d840; fork `main` = pin + fix

[OBS 2026-10-29] User asked why the fix sat on a side branch and then to
"upgrade our main aeneas and charon pin to match aeneas_mod". The fork's
`main` mirrored upstream at de16f3c (4 commits past our pin 399081f,
the last being a Charon bump). Done:
- `aeneas/` → de16f3c (upstream), `charon/` → 373d840 (= new
  `aeneas/charon-pin`; 42 Charon commits). rustc stays
  nightly-2026-09-17, Lean stays v4.35.0 with the same Mathlib rev, so
  the Lean library only needed an incremental `lake build` (1796 jobs,
  the one source change is `Aeneas/Std/SliceIter.lean`).
- Fix commit rebased 399081f→de16f3c as 38531ab (clean; upstream still
  has no `AEndedProjLoans` arm in `MakeMatcher.match_tavalues`). Fork
  `main` fast-forwarded de16f3c→38531ab and pushed, side branch deleted
  locally and remotely, `.gitmodules` `branch = main`.
- Builds: Charon `make build-charon-rust` + CharonVersion.ml + charon-ml
  `dune build` (~several minutes, release); both Aeneas trees `dune build`
  then copy `main.exe` to `bin/aeneas`.
Verify: `tools/check.py tests/compile_ok1.rs | jq .versions` shows
`aeneas de16f3cf`, `charon 373d84044`, `charon_matches_pin true`.

[OBS 2026-10-29] Verdicts at the new pins, pristine vs mod, identical to
the old pins for every input tried: compile_ok1 translates/translates;
raw_ptr, async_fn unsupported/unsupported; ref_mul, missing_dep
missing/missing; invalid invalid/invalid; or_in_loop_bool
toolchain/toolchain; chars_next_before_loop unsupported/**missing**;
remove_Occ attempt-2 unsupported/**toolchain**; remove_Occ attempt-4
missing/missing; square_nums attempt-2 translates/translates. So the 4
upstream commits changed nothing we measure, and the stored-`||`
Prop/Bool bug is still present upstream. Recorded `mbpp/*/check.json`
were *not* regenerated; they still carry the old version stamps.

[OBS 2026-10-29] `make test` in `aeneas_mod` at the new base: exit 0, 116 test
invocations, no expected-output changes (`git status` clean apart from nothing).

## See also

- 2026-10-29-aeneas-loop-matcher-fix-experiment.md
- ../../durable/how-to-translate-a-rust-file-to-lean-and-check-it.md
