#!/usr/bin/env bash
# Generate the per-job Lernziele goal sheets (Betrieb, Berufsschule, überbetriebliche
# Kurse) and compile them to PDF. The job list and file names come from data/jobs.json.
set -euo pipefail
cd "$(dirname "$0")"

# Read "CODE shortname" pairs from data/jobs.json (order preserved).
JOBS=$(python3 - <<'PY'
import json
jobs = json.load(open("../data/jobs.json", encoding="utf-8"))
for code, job in jobs.items():
    print(code, job["short"])
PY
)

while read -r CODE SHORT; do
  [ -z "$CODE" ] && continue
  INPUT="../data/lehrplan_${CODE}.json"
  [ -f "$INPUT" ] || { echo "skip $CODE (no $INPUT)"; continue; }
  python3 generate_lehrplan_typ.py "$INPUT" --lernort BE \
    -o "output/Lernziele_${SHORT}_Betrieb.typ"
  python3 generate_lehrplan_typ.py "$INPUT" --lernort BFS --by-semester \
    -o "output/Lernziele_${SHORT}_Berufsschule.typ"
  python3 generate_lehrplan_typ.py "$INPUT" --lernort üK --by-semester \
    -o "output/Lernziele_${SHORT}_Ueberbetriebliche_Kurse.typ"
done <<< "$JOBS"

for f in output/*.typ; do
  echo "Compiling $f"
  typst compile "$f"
done
echo "Done. PDFs are in output/"
