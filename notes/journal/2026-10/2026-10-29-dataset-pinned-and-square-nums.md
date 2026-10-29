# Dataset pinned to a revision; mbpp_8_square_nums passes at attempt 2

[OBS 2026-10-29] Pushed the repo to `github.com/priyasiddharth/baif-sim`.
GitHub had pre-created `main` with a one-line README; merged it with
`--allow-unrelated-histories` rather than force-push, renamed local
`master` → `main`, deleted remote `master`. README is still a stub.

[OBS 2026-10-29] User asked whether to submodule "the MBPP project".
Answer: no — what we use is not the `google-research/mbpp` repo
(Python-only) nor the `nuprl/MultiPL-E` GitHub repo (translation tooling)
but one 354-row split of the HF *dataset* `nuprl/MultiPL-E`, which is
parquet behind LFS for ~20 languages × 2 benchmarks. The real gap was
pinning: `fetch` read the rows API unpinned, so a dataset update could
silently change prompts/tests behind a recorded attempt. Done instead:
`data/mbpp-rs.json` = all rows + HF revision `28441b6` (lastModified
2025-07-15) + snapshot date; `mbpp.py fetch` reads it (`--remote` for
the API), `mbpp.py snapshot` refreshes it; every `status.json` source
now carries the revision. The five recorded problems were byte-identical
to the snapshot before re-stamping.
Verify: `python3 -c "import json;print(json.load(open('data/mbpp-rs.json'))['revision'])"`.

[OBS 2026-10-29] mbpp_8_square_nums (`Vec<isize> -> Vec<isize>`, offset 3):
attempt 1 `nums.iter().map(|x| x * x).collect()` → `missing_context`,
axioms `Iterator::map`, `Map::next`, `Mul<&isize> for &isize`; Lean also
reports `map`/`collect` "is not a field of structure
core.iter.traits.iterator.Iterator". Attempt 2 index `while` + `Vec::new`
/`push` + `x * x` on the owned element → `translates`, no axioms. Exactly
the pattern of problems 3/4/6/12; predicted before running.

[OBS 2026-10-29] Tally: 6 problems, 0/6 first attempt, 5/6 at attempt 2,
`mbpp_11_remove_Occ` unresolved at 4. The non-string repair is now
routine enough that attempt 1 is only measuring the generator's default
style, which is the point of the part-3 allowlist experiment.

## See also

- 2026-10-28-remove-occ-strings-expose-three-aeneas-limits.md
- 2026-10-28-mbpp-loop-first-three-problems.md
- ../../empirical/idiomatic-rust-fails-on-missing-stdlib-models.md
