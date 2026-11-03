import random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from minimal_realization_reversible.engine import step

def test_second_order_is_reversible():
    rng = random.Random(1)
    for w in range(256):
        prev = [rng.randint(0, 1) for _ in range(16)]; cur = [rng.randint(0, 1) for _ in range(16)]
        p, c = prev, cur
        for _ in range(5): p, c = step(w, p, c, 2)
        for _ in range(5):  # backward: x[t-1] = f(x[t]) XOR x[t+1]
            f = step(w, [0] * 16, p, 1)[1]; p, c = [a ^ b for a, b in zip(f, c)], p
        assert (p, c) == (prev, cur)
