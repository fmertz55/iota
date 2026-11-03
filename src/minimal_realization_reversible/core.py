"""MIR-REVERSIBLE-CORE-001: bounded persistent core detector (v0.4)."""
from minimal_realization_reversible.engine import step

N, H, G, W, K, T0MAX = 256, 120, 3, 8, 64, 29
SEEDS = ['1', '11', '101', '111', '1001', '1011', '1101', '1111']  # x[0] at loci 0..; x[-1]=0


def run(w, seed, n=N, h=H):
    prev, cur = [0] * n, [0] * n
    for k, ch in enumerate(seed):
        cur[k] = int(ch)
    cp, cc = [0] * n, [0] * n
    diffs = [[a ^ b for a, b in zip(cur, cc)]]
    for _ in range(h):
        prev, cur = step(w, prev, cur, 2)
        cp, cc = step(w, cp, cc, 2)
        diffs.append([a ^ b for a, b in zip(cur, cc)])
    return diffs


def clusters(d):
    """Maximal groups of difference sites with internal zero gaps < G, in signed
    coordinates (support never wraps for t <= H on N=256)."""
    n = len(d)
    s = sorted(i if i <= n // 2 else i - n for i in range(n) if d[i])
    out, lo, hi = [], None, None
    for i in s:
        if lo is None:
            lo = hi = i
        elif i - hi - 1 < G:
            hi = i
        else:
            out.append((lo, hi)); lo = hi = i
    if lo is not None:
        out.append((lo, hi))
    return out


def track(diffs):
    """First (t0, leftmost) start with a bounded core persisting K ticks.
    Returns dict or None."""
    cl = [clusters(d) for d in diffs]
    for t0 in range(1, T0MAX + 1):
        for c in cl[t0]:
            if c[1] - c[0] + 1 > W:
                continue
            path, cur, ok = [c], c, True
            for t in range(t0 + 1, t0 + K + 1):
                nxt = [e for e in cl[t] if e[1] - e[0] + 1 <= W
                       and e[0] <= cur[1] + 1 and e[1] >= cur[0] - 1]
                if not nxt:
                    ok = False; break
                cur = nxt[0]; path.append(cur)
            if ok:
                isolated = all(len(cl[t0 + j]) == 1 for j in range(K + 1))
                return dict(t0=t0, start=list(c), end=list(path[-1]),
                            drift=path[-1][0] - c[0], kind='isolated_object' if isolated
                            else 'core_with_radiation',
                            total_width_end=(lambda q: q[-1][1] - q[0][0] + 1)(cl[t0 + K]))
    return None
