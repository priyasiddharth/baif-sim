#!/usr/bin/env bash
# Reproduce the Aeneas loop-join failure and show the fix.
#
#   examples/loop_join/run.sh            # run everything, write logs to ./out/
#   examples/loop_join/run.sh --trace    # also print the matcher trace excerpt
#
# Needs: charon/bin/charon, aeneas/bin/aeneas (pristine), aeneas_mod/bin/aeneas (patched).
set -u
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../.." && pwd)"
out="$here/out"; mkdir -p "$out"
charon="$root/charon/bin/charon"
pristine="$root/aeneas/bin/aeneas"
mod="$root/aeneas_mod/bin/aeneas"
trace=${1:-}
strip() { sed -e 's/\x1b\[[0-9;?]*[A-Za-z]//g'; }

translate() {   # translate <aeneas-binary> <llbc> <dest-dir> <logfile>  -> prints exit code
  mkdir -p "$3"
  "$1" -backend lean "$2" -dest "$3" -namespace Ex -log InterpJoin -log-debug InterpMatchCtxs 2>&1 | strip > "$4"
  echo "${PIPESTATUS[0]}"
}

for f in fails passes; do
  echo "================================================================ $f.rs"
  grep -n '(\*)' "$here/$f.rs"
  (cd "$here" && "$charon" rustc --preset=aeneas --dest-file="$out/$f.llbc" -- --crate-type=lib --edition=2021 -Awarnings "$f.rs" >/dev/null 2>&1) \
    || { echo "charon failed"; continue; }

  for which in pristine mod; do
    bin=$([ $which = pristine ] && echo "$pristine" || echo "$mod")
    log="$out/$f.$which.log"
    code=$(translate "$bin" "$out/$f.llbc" "$out/$f.$which" "$log")
    printf -- "--- %-8s aeneas exit %s" "$which" "$code"
    if grep -q "Could not match the contexts" "$log"; then
      echo "   ** Could not match the contexts **"
    else
      echo "   ok; loop signature:"
      lean=$(ls "$out/$f.$which"/*.lean | head -1)
      sed -n '/^def count_first_loop$/,/:= do/p' "$lean" | sed 's/^/        /'
    fi
  done

  if [ "$trace" = "--trace" ] && grep -q "Could not match" "$out/$f.pristine.log"; then
    echo "--- matcher trace (pristine): abstractions it paired, then the one it could not"
    grep -A1 "^Found matching abs:" "$out/$f.pristine.log" | grep "^abs@" | sed 's/^/    paired:   /'
    n=$(grep -n "Trying to match abs:" "$out/$f.pristine.log" | tail -1 | cut -d: -f1)
    sed -n "$((n+1)),$((n+4))p" "$out/$f.pristine.log" | sed 's/^/    unpaired: /'
    echo "    ...descends into its avalues; the last pair it reaches before giving up:"
    sed -n "$n,\$p" "$out/$f.pristine.log" | grep -B1 "ended_aproj_loans (_)$" | grep "value[01]:" | tail -2 | sed 's/^/      /'
    grep "^distinct:" "$out/$f.pristine.log" | tail -1 | sed 's/^/    /'
    echo "    (full log: $out/$f.pristine.log)"
  fi
done

echo
echo "================================================================ the fix (aeneas_mod vs pinned 399081f)"
git -C "$root/aeneas_mod" --no-pager diff 399081f -- src/interp/InterpMatchCtxs.ml
echo
echo "logs and generated Lean: $out/"
