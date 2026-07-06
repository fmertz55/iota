#!/usr/bin/env bash
set -euo pipefail
export PYTHONUNBUFFERED=1
while IFS=$'\t' read -r seed law condition sample_index active lcf; do
  [[ -z "${seed:-}" ]] && continue
  echo "=== $(date -Iseconds) seed=$seed law=$law condition=$condition sample=$sample_index active=$active lcf=$lcf ==="
  .venv/bin/python -u src/payload_coupling_committor_analysis.py \
    --samples 50 \
    --seeds "$seed" \
    --laws "$law" \
    --conditions "$condition" \
    --sample-indexes "$sample_index" \
    --early-absorber \
    --refresh-missing
  echo "=== $(date -Iseconds) done seed=$seed law=$law condition=$condition sample=$sample_index ==="
done < output/findings/logs/high_dominant_remaining_targets.tsv
