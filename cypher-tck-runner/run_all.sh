#!/bin/bash
# Run every feature, one behave process each (a crash loses one feature, not the run), into <out dir>.
# Usage: run_all.sh <out dir> [python]
OUT=$1
PY=${2:-python}
cd "$(dirname "$0")" || exit 1
rm -rf "$OUT" && mkdir -p "$OUT"
for f in $(find features -name '*.feature' | sort); do
  n=$(echo "$f" | tr '/' '_')
  PYTHONPATH=src "$PY" -m behave "$f" --no-capture -f json -o "$OUT/$n.json" -f null --summary > "$OUT/$n.txt" 2>&1
done
