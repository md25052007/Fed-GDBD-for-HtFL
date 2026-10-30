"""Summarise novelty runs (FedGDBD-S control vs agreement-gated AGC / AGS).

Usage:  python analysis/novelty_summary.py experiments/novelty/run1_seed0/cifar10/logs

For every *.log: best / last accuracy, accuracy per architecture (client id mod 4:
CNN, GoogLeNet, MobileNetV2, ResNet18) at the best round, and the gate statistics:
  AGC -> g's accuracy on each architecture's own training features (alpha = 0.7 x that)
  AGS -> fraction of training images that were distilled (g's top class correct)
"""
import glob
import os
import re
import statistics as st
import sys

ARCH = ['CNN', 'GoogLeNet', 'MobileNetV2', 'ResNet18']


def per_arch(txt):
    rows = []
    for block in txt.split('Evaluate heterogeneous models')[1:]:
        cs = re.findall(r'Client (\d+): Acc: ([\d.]+)', block)
        if len(cs) >= 20:
            rows.append([100 * st.mean(float(a) for c, a in cs if int(c) % 4 == k) for k in range(4)])
    return rows


def main(folder):
    control = None
    for path in sorted(glob.glob(os.path.join(folder, '*.log'))):
        txt = open(path, encoding='utf-8', errors='ignore').read()
        name = os.path.basename(path)[:-4]
        acc = [100 * float(a) for a in re.findall(r'Averaged Test Accuracy: ([\d.]+)', txt)]
        if not acc:
            continue
        best = max(acc)
        i = acc.index(best)
        if name.endswith('FedGDBD-S'):
            control = best
        arch = per_arch(txt)
        print(f'{name:24} best {best:6.2f} (round {i})  last {acc[-1]:6.2f}  rounds {len(acc) - 1}')
        if arch:
            print('   per architecture at best round: ' +
                  ' | '.join(f'{ARCH[k]} {arch[min(i, len(arch) - 1)][k]:.1f}' for k in range(4)))
        gates = re.findall(r'Gate client (\d+): g_acc=([\d.]+)', txt)
        if gates:
            print('   g accuracy on own features (mean over rounds): ' +
                  ' | '.join(f'{ARCH[k]} {st.mean(float(g) for c, g in gates if int(c) % 4 == k):.2f}' for k in range(4)))
        kept = re.findall(r'Gate sample (\d+): kept=([\d.]+)', txt)
        if kept:
            print('   fraction of images distilled (mean over rounds): ' +
                  ' | '.join(f'{ARCH[k]} {st.mean(float(v) for c, v in kept if int(c) % 4 == k):.2f}' for k in range(4)))
    if control is not None:
        print(f'\ncontrol (FedGDBD-S) best = {control:.2f}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'logs_novelty')
