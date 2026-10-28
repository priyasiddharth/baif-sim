#!/usr/bin/env bash
# Translate a single Rust file to Lean via Charon and Aeneas.
# Usage: tests/translate.sh <file.rs> [out-dir]   (default out-dir: a new temp dir)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CHARON="$ROOT/charon/bin/charon"
AENEAS="$ROOT/aeneas/bin/aeneas"

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo "Usage: $0 <file.rs> [out-dir]" >&2
    exit 1
fi

src="$1"
name="$(basename "$src" .rs)"
out="${2:-$(mktemp -d -t "$name-lean.XXXXXX")}"
mkdir -p "$out"

"$CHARON" rustc --preset=aeneas --dest-file "$out/$name.llbc" -- --crate-type=lib "$src"
"$AENEAS" -backend lean "$out/$name.llbc" -dest "$out"

echo "Lean output: $out"
