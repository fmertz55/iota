#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
rows=(
  "42 high protected_vector 26"
  "56 high protected_vector 48"
  "56 high protected_vector 41"
  "56 high absorber_vector 16"
)
for row in "${rows[@]}"; do
  read -r seed law condition sample_index <<< "$row"
  echo "=== $(date -Iseconds) seed=$seed law=$law condition=$condition sample=$sample_index ==="
  .venv/bin/python -u src/payload_coupling_committor_analysis.py \
    --samples 50 \
    --seeds "$seed" \
    --laws "$law" \
    --conditions "$condition" \
    --sample-indexes "$sample_index" \
    --early-absorber \
    --refresh-missing
  echo "=== $(date -Iseconds) done seed=$seed law=$law condition=$condition sample=$sample_index ==="
done
