#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

DATE_TAG="$(date +%Y%m%d)"
EXP_ARCHIVE="experiments/_archive_${DATE_TAG}"
DATA_ARCHIVE="datasets/_archive_${DATE_TAG}"
APPLY=0

if [[ "${1:-}" == "--apply" ]]; then
  APPLY=1
fi

mkdir -p "$EXP_ARCHIVE" "$DATA_ARCHIVE"

echo "[Plan] archive experiments -> $EXP_ARCHIVE"
echo "[Plan] archive datasets    -> $DATA_ARCHIVE"

EXP_CANDIDATES=()
while IFS= read -r d; do
  EXP_CANDIDATES+=("$d")
done < <(find experiments -maxdepth 1 -mindepth 1 -type d -name 'wm_*' | sort)

DATA_CANDIDATES=()
while IFS= read -r d; do
  DATA_CANDIDATES+=("$d")
done < <(
  {
    find datasets -maxdepth 1 -mindepth 1 -type d -name 'takeoff_*';
    find datasets -maxdepth 1 -mindepth 1 -type d -name 'stable_flight_wm_*';
  } | sort -u
)

echo "[Candidates] experiments: ${#EXP_CANDIDATES[@]}"
for d in "${EXP_CANDIDATES[@]}"; do
  echo "  $d"
done

echo "[Candidates] datasets: ${#DATA_CANDIDATES[@]}"
for d in "${DATA_CANDIDATES[@]}"; do
  echo "  $d"
done

if [[ "$APPLY" -ne 1 ]]; then
  echo
  echo "Dry-run only. Re-run with --apply to move directories."
  exit 0
fi

move_one() {
  local src="$1"
  local dst_root="$2"
  local base
  base="$(basename "$src")"
  local dst="$dst_root/$base"
  if [[ -e "$dst" ]]; then
    echo "[Skip] destination exists: $dst"
    return 0
  fi
  mv "$src" "$dst"
  echo "[Moved] $src -> $dst"
}

for d in "${EXP_CANDIDATES[@]}"; do
  move_one "$d" "$EXP_ARCHIVE"
done

for d in "${DATA_CANDIDATES[@]}"; do
  move_one "$d" "$DATA_ARCHIVE"
done

echo
echo "Isolation complete."
echo "Restore example: mv $EXP_ARCHIVE/<dir> experiments/"
echo "Restore example: mv $DATA_ARCHIVE/<dir> datasets/"
