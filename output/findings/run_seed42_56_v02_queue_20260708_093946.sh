#!/bin/zsh
repo="/Users/douglasclark/iota"
log="/Users/douglasclark/iota/output/findings/run_seed42_56_v02_queue_20260708_093946.log"
cd "$repo" || exit 2
exec >> "$log" 2>&1
echo "=== $(date) queue pid=$$ start ==="
echo "=== $(date) golden replay start ==="
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python src/parallel_replay.py golden --seeds 42 56 --jobs 4 --output output/findings/parallel_golden_replay.json
echo "=== $(date) golden replay exit=$? ==="
echo "=== $(date) targeted committor start ==="
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python src/parallel_replay.py committor --jobs 3 --targets output/findings/targeted_seed42_56_replay_targets.csv --output-dir output/findings/parallel_committor_seed42_56_targets --refresh
echo "=== $(date) targeted committor exit=$? ==="
echo "=== $(date) v0.2 parameter search start ==="
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python src/v02_parameter_search.py --jobs 6 --ticks 1024 --stagnation-window 256 --output-prefix output/findings/finding_025_v02_parameter_search --flush-every 8 --top-n 20
echo "=== $(date) v0.2 parameter search exit=$? ==="
echo "=== $(date) queue complete ==="
