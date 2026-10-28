# Project: sim — writing Rust that Aeneas can translate to Lean

These notes live at `notes/` in the sim repo (tracked, shared). The
**better-than-fish** skill governs how to add and maintain them. In short:
three tiers by durability, confidence markers on every claim,
supersede-don't-delete on corrections.

## Tiers

- `durable/` — `[FACT]`: source/build/design-grounded, near-time-invariant.
- `empirical/` — `[EMP]`: repeated observations, version-stamped ("Verified against").
- `journal/YYYY-MM/` — `[OBS YYYY-MM-DD]`, `[HYP]`: dated single findings.
- `loose-ends/parked.md` — parked work, five-field format.
- `sessions.md` — chronological index of significant sessions.

Markers: `[FACT] [EMP] [OBS] [HYP] [OPEN] [SUPERSEDED → path]`. What persists is
true — a `[HYP]` that survives earns promotion; a wrong `[FACT]` is superseded,
never deleted.

## Triggers

- "note this" / "save this" / "take btf notes" → journal entry, today's date.
- "wrong, X" / "actually X" → grep the related note, mark `[SUPERSEDED → …]`,
  write the corrected note, add a "why I was misled" line. Never delete silently.
- "park this" → loose-ends/parked.md, five-field format.
- "digest" → weekly/monthly distillation; promote repeated claims upward.
- "what do we know about X" → grep notes first, then answer.

## Evidence standard (project-specific)

This user checks. Label hypotheses `[HYP]`, not `[OBS]`/`[FACT]`. Give a
verification command with every `[FACT]`. "It translated" is three separate
claims — Charon exit, Aeneas exit, Lean type-check + `#print axioms` — say
which were actually checked. An `axiom` in the output is a hole, not a pass.

## Source repos (for citations)

- Aeneas: `aeneas/` (submodule; `src/` OCaml, `backends/lean/` the Lean lib, `tests/src/`).
- Charon: `charon/` (submodule; `charon/src/` Rust, `charon-ml/`, `charon/tests/ui/`).
- Ours: `tools/check.py`, `tools/mbpp.py`, `tests/`, `mbpp/`.
- Version stamps: aeneas commit, charon commit (must equal `aeneas/charon-pin`),
  rustc nightly (`charon toolchain-version`), Lean toolchain (`aeneas/backends/lean/lean-toolchain`).

## Linking

Plain filenames for note↔note links (grep-able). Repo-relative paths only as
source citations, not as note links.
