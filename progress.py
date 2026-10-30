"""Summarise all runs in logs/: rounds done, best/last accuracy, speed, ETA.
Works while runs are still going, so partial results are usable."""
import glob
import os
import re
import sys
import time

PAPER = {  # Table 1, practical setting
    ('Cifar10', 'FedGDBD'): 87.90, ('Cifar10', 'FedProto'): 82.75, ('Cifar10', 'LG-FedAvg'): 86.64,
    ('Cifar100', 'FedGDBD'): 45.09, ('Cifar100', 'FedProto'): 35.38, ('Cifar100', 'LG-FedAvg'): 43.30,
    ('Cifar10', 'FedGDBD-S'): 87.90, ('Cifar100', 'FedGDBD-S'): 45.09,
    ('Cifar10', 'FedGDBD-AGC'): 87.90, ('Cifar100', 'FedGDBD-AGC'): 45.09,
    ('Cifar10', 'FedGDBD-AGS'): 87.90, ('Cifar100', 'FedGDBD-AGS'): 45.09,
}

here = os.path.dirname(os.path.abspath(__file__))
logdir = sys.argv[1] if len(sys.argv) > 1 else 'logs'   # e.g. logs_novelty
logs = sorted(glob.glob(os.path.join(here, logdir, '*.log')))
if not logs:
    print(f'No logs in {logdir} yet. Start the run first.')
    sys.exit()

rows = []
for path in logs:
    name = os.path.basename(path)[:-4]
    data, algo = name.split('_', 1)
    txt = open(path, encoding='utf-8', errors='ignore').read()
    accs = [float(a) * 100 for a in re.findall(r'Averaged Test Accuracy: ([\d.]+)', txt)]
    times = [float(t) for t in re.findall(r'^-{20,}[^\n]*?([\d.]+)\s*$', txt, flags=re.M)]
    total = re.search(r'global_rounds = (\d+)', txt)
    total = int(total.group(1)) + 1 if total else 0  # main loop runs rounds 0..gr
    done = len(times)
    if 'Traceback' in txt:
        status = 'CRASHED (open the log)'
    elif 'All done!' in txt:
        status = 'FINISHED'
    elif time.time() - os.path.getmtime(path) > 45 * 60:
        status = 'STOPPED (no update for 45+ min)'
    elif done == 0:
        status = 'starting / pre-training'
    else:
        avg = sum(times[-5:]) / len(times[-5:])
        status = f'running, ~{(total - done) * avg / 3600:.1f} h left'
    spr = f'{sum(times) / done / 60:.1f}' if done else '-'
    rows.append((data, algo, done, total, max(accs) if accs else None,
                 accs[-1] if accs else None, PAPER.get((data, algo)), spr, status))

hdr = f"{'Dataset':9} {'Method':10} {'Round':>9} {'Best%':>7} {'Last%':>7} {'Paper%':>7} {'min/rnd':>8}  Status"
print(hdr)
print('-' * len(hdr))
f = lambda v: f'{v:7.2f}' if v is not None else '      -'
for d, a, done, tot, best, last, pap, spr, st in rows:
    print(f'{d:9} {a:10} {done:>4}/{tot:<4} {f(best)} {f(last)} {f(pap)} {spr:>8}  {st}')
