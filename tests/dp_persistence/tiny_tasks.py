"""Spawn-importable synthetic tasks for runner plumbing tests.

They return L0-shaped run records computed from the seed alone; no medium is
drawn and no engine runs.
"""

from __future__ import annotations

import math
import time

import numpy as np


THRESHOLD = 0.31
QUANTILES = 1000


def synthetic_iota_run(task: tuple[float, int, int]) -> dict:
    control, seed, horizon = task
    u = (seed % QUANTILES + 0.5) / QUANTILES
    if control < THRESHOLD:
        absorbed = math.floor(-30.0 * math.log(u)) + 1
    elif u < 0.4:
        absorbed = None
    else:
        absorbed = math.floor(((u - 0.4) / 0.6) ** -2.0) + 1
    if absorbed is not None and absorbed > horizon:
        absorbed = None
    length = horizon if absorbed is None else absorbed - 1
    t = np.arange(1, length + 1, dtype=np.int64)
    S = 1 + length
    record = {
        "n_t": np.full(length, 3, dtype=np.int64),
        "r2_sum_t": 3 * t,
        "absorbed_at": absorbed,
        "censored_at": None,
        "ticks_run": length if absorbed is None else absorbed,
        "S": S,
        "stranded_amplitude": 9 if absorbed is not None else None,
        "ledger_residual": 0,
        "C": S - 1 if absorbed is not None else None,
        "E": 1.0 if absorbed is not None and S > 1 else None,
    }
    return record


def echo(task: int) -> dict:
    return {"value": task}


def slow(task: int) -> dict:
    time.sleep(0.2)
    return {"value": task}
