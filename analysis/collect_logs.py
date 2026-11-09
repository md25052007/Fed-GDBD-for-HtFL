"""Copy finished novelty logs and result files into experiments/novelty/ so they can be committed.

Usage:  python analysis/collect_logs.py 2          (seed 2)
        python analysis/collect_logs.py 0 1 2 3    (several seeds, e.g. after the fixed-alpha runs)

Layout:  experiments/novelty/run<seed+1>_seed<seed>/<cifar10|cifar100>/{logs,results}/
Existing files are overwritten with the newer copy; nothing is deleted.
"""
import glob
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def collect(seed):
    logdir = os.path.join(ROOT, 'logs_novelty' if seed == 0 else f'logs_novelty_seed{seed}')
    goal = 'novelty' if seed == 0 else f'novelty_seed{seed}'
    dest = os.path.join(ROOT, 'experiments', 'novelty', f'run{seed + 1}_seed{seed}')
    n = 0
    for data in ('Cifar10', 'Cifar100'):
        sub = os.path.join(dest, data.lower())
        for path in glob.glob(os.path.join(logdir, f'{data}_*.log')):
            os.makedirs(os.path.join(sub, 'logs'), exist_ok=True)
            shutil.copy2(path, os.path.join(sub, 'logs'))
            n += 1
        for path in glob.glob(os.path.join(ROOT, 'results', f'{data}_*.h5')):
            if not re.search(rf'_{goal}(_amatch)?_\d+\.h5$', path):
                continue
            os.makedirs(os.path.join(sub, 'results'), exist_ok=True)
            shutil.copy2(path, os.path.join(sub, 'results'))
            n += 1
    print(f'seed {seed}: copied {n} files into {os.path.relpath(dest, ROOT)}')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    for s in sys.argv[1:]:
        collect(int(s))
