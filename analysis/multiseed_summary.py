"""Multi-seed analysis of the extension, exactly as fixed in PROTOCOL.md.

Usage:  python analysis/multiseed_summary.py              (all seeds: primary analysis)
        python analysis/multiseed_summary.py --seeds 2 3   (new seeds only: out-of-sample check)

Reads experiments/novelty/run*_seed*/<dataset>/logs/*.log and, for each dataset:
  1. best-round and last-round accuracy of every run, per seed;
  2. mean +- SD over seeds for each method;
  3. the three paired comparisons of PROTOCOL.md:
        AGC vs control, AGC vs matched alpha, AGS vs control
     with per-seed gaps, mean gap, 95% CI, paired t-test (two- and one-sided)
     and the number of seeds won.
Only seeds that have all four runs finished (20 rounds) enter the paired tests;
incomplete seeds are listed and skipped, never partially used.
"""
import glob
import math
import os
import re
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METHODS = {'FedGDBD-S': 'control', 'FedGDBD-AGC': 'AGC', 'FedGDBD-AGS': 'AGS', 'FedGDBD-S-amatch': 'matched-alpha'}
COMPARISONS = [('AGC', 'control'), ('AGC', 'matched-alpha'), ('AGS', 'control')]
ROUNDS = 20


def read(path):
    txt = open(path, encoding='utf-8', errors='ignore').read()
    acc = [100 * float(a) for a in re.findall(r'Averaged Test Accuracy: ([\d.]+)', txt)]
    return acc


# ---------------------------------------------------------------- Student t (no scipy needed)
def t_pdf(x, df):
    return math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi) * (1 + x * x / df) ** (-(df + 1) / 2)


def t_sf(t, df):
    """P(T > t) by Simpson integration from 0 to |t|."""
    a = abs(t)
    n = 2000
    h = a / n
    s = t_pdf(0, df) + t_pdf(a, df) + sum((4 if i % 2 else 2) * t_pdf(i * h, df) for i in range(1, n))
    upper = 0.5 - s * h / 3
    return upper if t >= 0 else 1 - upper


def t_crit(df, conf=0.95):
    lo, hi = 0.0, 50.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if t_sf(mid, df) > (1 - conf) / 2:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def paired(gaps):
    n = len(gaps)
    m = st.mean(gaps)
    if n < 2:
        return m, float('nan'), (float('nan'), float('nan')), float('nan'), float('nan')
    sd = st.stdev(gaps)
    se = sd / math.sqrt(n)
    if se == 0:
        return m, sd, (m, m), 0.0, 0.0
    t = m / se
    ci = t_crit(n - 1) * se
    return m, sd, (m - ci, m + ci), 2 * t_sf(abs(t), n - 1), t_sf(t, n - 1)


def main(only=None):
    for ds in ('cifar10', 'cifar100'):
        runs = {}  # seed -> method -> (best, last, rounds)
        for path in glob.glob(os.path.join(ROOT, 'experiments', 'novelty', 'run*_seed*', ds, 'logs', '*.log')):
            seed = int(re.search(r'_seed(\d+)', path).group(1))
            algo = os.path.basename(path)[:-4].split('_', 1)[1]
            if algo not in METHODS:
                continue
            acc = read(path)
            if acc:
                runs.setdefault(seed, {})[METHODS[algo]] = (max(acc), acc[-1], len(acc) - 1)
        print('=' * 78)
        print(f'{ds.upper()}')
        print('=' * 78)
        seeds = sorted(s for s in runs if only is None or s in only)
        complete = [s for s in seeds if all(m in runs[s] and runs[s][m][2] >= ROUNDS for m in METHODS.values())]
        for s in seeds:
            if s not in complete:
                have = {m: runs[s][m][2] for m in runs[s]}
                print(f'  seed {s}: incomplete, skipped in paired tests  (rounds per method: {have})')
        for kind, k in (('best-round', 0), ('last-round', 1)):
            print(f'\n  {kind} accuracy (%)')
            print('  ' + f"{'method':15}" + ''.join(f'  seed {s:<3}' for s in complete) + '   mean +- SD')
            for m in METHODS.values():
                vals = [runs[s][m][k] for s in complete]
                sd = st.stdev(vals) if len(vals) > 1 else float('nan')
                print('  ' + f'{m:15}' + ''.join(f'  {v:8.2f}' for v in vals) + (f'   {st.mean(vals):.2f} +- {sd:.2f}' if vals else ''))
            print(f'\n  paired comparisons, {kind} (gap = first - second, in pt)')
            for a, b in COMPARISONS:
                gaps = [runs[s][a][k] - runs[s][b][k] for s in complete]
                if not gaps:
                    continue
                m, sd, (lo, hi), p2, p1 = paired(gaps)
                wins = sum(g > 0 for g in gaps)
                print(f'  {a} vs {b}:'.ljust(30) + ' '.join(f'{g:+.2f}' for g in gaps))
                print(f'      mean {m:+.2f}  SD {sd:.2f}  95% CI [{lo:+.2f}, {hi:+.2f}]  '
                      f't-test p (two-sided) {p2:.3f}  p (one-sided, >0) {p1:.3f}  wins {wins}/{len(gaps)}')
        print()


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    main([int(a) for a in args[1:]] if args[:1] == ['--seeds'] else None)
