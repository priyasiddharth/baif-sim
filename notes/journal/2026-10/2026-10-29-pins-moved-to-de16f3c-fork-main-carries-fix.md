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
invocations, no expected-output changes (`git status` in the submodule is clean).

## See also

- 2026-10-29-aeneas-loop-matcher-fix-experiment.md
- ../../durable/how-to-translate-a-rust-file-to-lean-and-check-it.md

[OBS 2026-10-29] CI added: `.github/workflows/check.yml` runs
`tests/run_expected.py` (34 verdicts = 17 inputs × pristine/mod, from
`tests/expected.json`; 18 s locally). Binaries from Nix (`path:` flake refs
into the submodules; Charon via the Aeneas flake, whose flake.lock pins
the same Charon as `charon-pin`), upstream's hacl Cachix as substituter,
Nix store cached with nix-community/cache-nix-action, `~/.elan` and
`aeneas/backends/lean/.lake` cached with actions/cache keyed on the Aeneas
commit + manifest. `aeneas_mod` URL in `.gitmodules` switched to HTTPS so
the CI checkout works without a key (local remote stays SSH). First (cold) run
40850930973: success, 30 min wall: free disk 3 min, Nix builds 15 min
(Charon + pristine from hacl, fork built), Lean lib 5.5 min (`cache get`
+ build), 34 verdicts 46 s, saving caches 6 min.

[OBS 2026-10-29] Second run 40855107668 (only notes changed): success, 14 min,
but not a warm run. Lean cache hit (2.8 GB restored, build skipped: Lean lib
step 0 s). Nix step still 8.7 min: it rebuilt `ocaml5.5.1-aeneas` (both
checkouts), `charon`, `rust-default-1.100.0-nightly-2026-09-17` and
`charon-full-mir-sysroots`, substituting 374 paths from hacl and 205 from
cache.nixos.org. Two causes in the logs: (1) run 1's post step reported the
store at 19.8 GB against the action's `gc-max-store-size-linux: 8G` and ran
`nix store gc`, deleting 572 paths (5.1 GiB) including `charon-0.1.301` and
`charon-deps-0.1.301`, so the saved 3.8 GB cache lacked exactly the expensive
outputs; (2) run 2's restore of that cache ended with
`tar ... failed with exit code 2` / "Failed to restore the cache" after ~460k
"Cannot open: No such file or directory" lines, so even the surviving paths
were not usable. Store-wide caching of /nix/store is the wrong granularity
here: most of the store is substitutable anyway, and the GC limit removed
what was not.

Replaced `cache-nix-action` with a file binary cache: after the builds,
`nix copy --to file:///tmp/nix-cache?compression=zstd` of the three result
closures (Charon + its Rust toolchain and sysroots, both Aeneas binaries);
`actions/cache` saves `/tmp/nix-cache` keyed `nixcache-<os>-<charon>-<aeneas>-
<aeneas_mod>` with prefix fallbacks; the build step adds it as
`--extra-substituters file:///tmp/nix-cache --option require-sigs false`.
Only the build outputs are cached, nothing is GC'd, and a partial hit (one
submodule moved) still substitutes the unchanged two.
[OPEN] third-run timing and cache size — appended after the push.
