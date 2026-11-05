"""Numbers and figures for the project report, computed from the run logs only.

Usage (from the repo root):
    python analysis/report_assets.py

Writes report/figures/*.pdf (+ .png) and report/data.json. Every value in the
report's tables comes from data.json, and data.json comes from experiments/.
"""
import json
import os
import re
import statistics as st

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, 'experiments')
OUT = os.path.join(ROOT, 'report', 'figures')
ARCH = ['CNN', 'GoogLeNet', 'MobileNetV2', 'ResNet18']
INK, GREY, LIGHT, GRID = '#26292B', '#6E7377', '#AEB3B6', '#E4E6E5'
GOLD, PURPLE, TEAL = '#B8892B', '#6250D6', '#3E8E7E'
ARCH_COL = [GREY, '#4C78A8', PURPLE, TEAL]

plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Cambria', 'Caladea', 'Liberation Serif', 'DejaVu Serif'],
    'mathtext.fontset': 'dejavuserif', 'font.size': 10, 'axes.titlesize': 10.5, 'axes.labelsize': 10,
    'axes.edgecolor': GREY, 'axes.labelcolor': INK, 'axes.titlecolor': INK,
    'xtick.color': GREY, 'ytick.color': GREY, 'text.color': INK,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.7,
    'axes.axisbelow': True, 'legend.frameon': False,
})


def parse(path):
    txt = open(path, encoding='utf-8', errors='ignore').read()
    acc = [100 * float(a) for a in re.findall(r'Averaged Test Accuracy: ([\d.]+)', txt)]
    std = [100 * float(a) for a in re.findall(r'Std Test Accuracy: ([\d.]+)', txt)]
    per, clients = [], []
    for block in txt.split('Evaluate heterogeneous models')[1:]:
        cs = re.findall(r'Client (\d+): Acc: ([\d.]+)', block)
        if len(cs) >= 20:
            d = {int(c): 100 * float(a) for c, a in cs}
            clients.append([d[k] for k in range(20)])
            per.append([st.mean(d[k] for k in range(20) if k % 4 == a) for a in range(4)])
    times = [float(t) for t in re.findall(r'-{10,} time cost -{10,} ([\d.]+)', txt)]
    pre = re.search(r'Pre-training done in ([\d.]+)s', txt)
    # gate lines appear after the evaluation of round i, so split by round blocks
    g_acc, kept = [], []
    for block in txt.split('-------------Round number:')[1:]:
        ga = re.findall(r'Gate client (\d+): g_acc=([\d.]+)', block)
        kp = re.findall(r'Gate sample (\d+): kept=([\d.]+)', block)
        if ga:
            g_acc.append([st.mean(float(v) for c, v in ga if int(c) % 4 == a) for a in range(4)])
        if kp:
            kept.append([st.mean(float(v) for c, v in kp if int(c) % 4 == a) for a in range(4)])
    b = acc.index(max(acc)) if acc else None
    return dict(acc=acc, std=std, per=per, clients=clients, best=max(acc) if acc else None, best_round=b,
                last=acc[-1] if acc else None, std_at_best=std[b] if acc else None,
                min_per_round=(st.mean(times[1:]) / 60 if len(times) > 1 else None),
                pretrain_s=float(pre.group(1)) if pre else None, g_acc=g_acc, kept=kept,
                nan_crash='Input contains NaN' in txt)


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + '.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(OUT, name + '.png'), dpi=200, bbox_inches='tight')
    plt.close(fig)


def main():
    R = {}
    for ds in ['Cifar10', 'Cifar100']:
        for m in ['FedProto', 'LG-FedAvg', 'FedGDBD', 'FedGDBD-S']:
            R[f'{ds}_{m}'] = parse(os.path.join(EXP, ds.lower(), 'logs', f'{ds}_{m}.log'))
        R[f'{ds}_buggyIKD'] = parse(os.path.join(EXP, ds.lower(), 'logs', 'old', f'{ds}_FedGDBD_v1_buggy_IKD.log'))
    N = {}
    for run, seed in [('run1_seed0', 0), ('run2_seed1', 1)]:
        for ds in ['Cifar10', 'Cifar100']:
            for v in ['FedGDBD-S', 'FedGDBD-AGC', 'FedGDBD-AGS']:
                N[f'{ds}_{v}_s{seed}'] = parse(os.path.join(EXP, 'novelty', run, ds.lower(), 'logs', f'{ds}_{v}.log'))

    # ---- Fig: collapse per architecture, CIFAR-10 (ResNet18) ----
    for ds, name in [('Cifar10', 'collapse_cifar10'), ('Cifar100', 'collapse_cifar100')]:
        f, s = R[f'{ds}_FedGDBD'], R[f'{ds}_FedGDBD-S']
        b = f['best_round']
        ser = [(f'Faithful, best round ({b})', f['per'][b], LIGHT), (f'Faithful, round {len(f["per"]) - 1}', f['per'][-1], PURPLE),
               (f'FedGDBD-S, round {len(s["per"]) - 1}', s['per'][-1], GOLD)]
        fig, ax = plt.subplots(figsize=(6.2, 3.3))
        w = 0.26
        for j, (lab, vals, col) in enumerate(ser):
            xs = [i + (j - 1) * w for i in range(4)]
            ax.bar(xs, vals, w * 0.94, color=col, label=lab)
            for x, v in zip(xs, vals):
                ax.text(x, v + 0.8, f'{v:.1f}', ha='center', va='bottom', fontsize=8)
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_ylim(0, 100 if ds == 'Cifar10' else 60)
        ax.set_ylabel('Test accuracy (%)')
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8.5, handlelength=1.2)
        save(fig, name)

    # ---- Fig: both collapse panels in one figure, (a) CIFAR-10 and (b) CIFAR-100 ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    for ax, ds, title in [(axes[0], 'Cifar10', '(a) CIFAR-10'), (axes[1], 'Cifar100', '(b) CIFAR-100')]:
        f, s = R[f'{ds}_FedGDBD'], R[f'{ds}_FedGDBD-S']
        b = f['best_round']
        ser = [('Faithful, best round', f['per'][b], LIGHT), ('Faithful, last round', f['per'][-1], PURPLE),
               ('FedGDBD-S, round 50', s['per'][-1], GOLD)]
        w = 0.26
        for j, (lab, vals, col) in enumerate(ser):
            xs = [i + (j - 1) * w for i in range(4)]
            ax.bar(xs, vals, w * 0.94, color=col, label=lab)
            for x, v in zip(xs, vals):
                ax.text(x, v + 0.8, f'{v:.1f}', ha='center', va='bottom', fontsize=7.5)
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_ylim(0, 100 if ds == 'Cifar10' else 60)
        ax.set_title(f'{title}: best round {b}, last round {len(f["per"]) - 1}', loc='left')
    axes[0].set_ylabel('Test accuracy (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.06), fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, 'collapse_both')

    # ---- Fig: per-architecture accuracy, all four methods at best round ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))
    meths = [('FedProto', LIGHT), ('LG-FedAvg', GREY), ('FedGDBD', PURPLE), ('FedGDBD-S', GOLD)]
    for ax, ds, title in [(axes[0], 'Cifar10', 'CIFAR-10'), (axes[1], 'Cifar100', 'CIFAR-100')]:
        w = 0.2
        for j, (m, col) in enumerate(meths):
            r = R[f'{ds}_{m}']
            vals = r['per'][r['best_round']]
            ax.bar([i + (j - 1.5) * w for i in range(4)], vals, w * 0.94, color=col,
                   label={'FedGDBD': 'Fed-GDBD (faithful)', 'FedGDBD-S': 'FedGDBD-S'}.get(m, m))
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_title(title, loc='left')
        ax.set_ylim(0, 100 if ds == 'Cifar10' else 60)
    axes[0].set_ylabel('Test accuracy at best round (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.07), fontsize=9)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, 'per_arch_methods')

    # ---- Fig: buggy IKD vs fixed faithful, CIFAR-100 ----
    fig, ax = plt.subplots(figsize=(6.0, 3.0))
    bug, fix = R['Cifar100_buggyIKD'], R['Cifar100_FedGDBD']
    ax.plot(range(len(bug['acc'])), bug['acc'], color=GREY, lw=1.8, marker='o', ms=3, label='IKD bug (target masked after softmax)')
    ax.plot(range(len(fix['acc'])), fix['acc'], color=PURPLE, lw=1.8, marker='o', ms=3, label='IKD fixed (masked before softmax), faithful Eq. 13')
    ax.plot([len(bug['acc']) - 1], [bug['acc'][-1]], 'x', color=INK, ms=8, mew=1.6)
    ax.annotate('loss becomes NaN at round 8', (len(bug['acc']) - 1, bug['acc'][-1]), xytext=(8, -16),
                textcoords='offset points', fontsize=8.5)
    ax.set_xlabel('Communication round')
    ax.set_ylabel('Averaged test accuracy (%)')
    ax.set_ylim(20, 45)
    ax.legend(fontsize=8.5, loc='lower left')
    save(fig, 'ikd_bug')

    # ---- Fig: novelty convergence, 2 datasets x 2 seeds ----
    fig, axes = plt.subplots(2, 2, figsize=(10, 5.8), sharex=True)
    for i, ds in enumerate(['Cifar10', 'Cifar100']):
        for j, seed in enumerate([0, 1]):
            ax = axes[i][j]
            for v, col, lab in [('FedGDBD-S', GREY, 'FedGDBD-S (control)'), ('FedGDBD-AGC', PURPLE, 'AGC'), ('FedGDBD-AGS', GOLD, 'AGS')]:
                a = N[f'{ds}_{v}_s{seed}']['acc']
                ax.plot(range(len(a)), a, color=col, lw=1.6, label=lab)
            lo = 80 if ds == 'Cifar10' else 30
            ax.set_ylim(lo, 89 if ds == 'Cifar10' else 45)
            ax.set_title(f'{"CIFAR-10" if ds == "Cifar10" else "CIFAR-100"}, seed {seed}', loc='left')
            if i == 1:
                ax.set_xlabel('Communication round')
            if j == 0:
                ax.set_ylabel('Averaged test acc. (%)')
            ax.set_xlim(0, 20)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.03), fontsize=9)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    save(fig, 'novelty_convergence')

    # ---- Fig: g accuracy per architecture over rounds (AGC) and AGS kept fraction ----
    for key, fname, ylab in [('g_acc', 'gate_gacc', 'g accuracy on own features'), ('kept', 'gate_kept', 'share of images distilled')]:
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.2), sharey=True)
        v = 'FedGDBD-AGC' if key == 'g_acc' else 'FedGDBD-AGS'
        for ax, ds, title in [(axes[0], 'Cifar10', 'CIFAR-10'), (axes[1], 'Cifar100', 'CIFAR-100')]:
            for a in range(4):
                for seed, ls in [(0, '-'), (1, '--')]:
                    s = N[f'{ds}_{v}_s{seed}'][key]
                    ax.plot(range(len(s)), [r[a] for r in s], color=ARCH_COL[a], lw=1.5, ls=ls,
                            label=f'{ARCH[a]}' if seed == 0 else None)
            ax.set_title(title, loc='left')
            ax.set_xlabel('Communication round')
            ax.set_ylim(0, 1.02)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        axes[0].set_ylabel(ylab)
        h, l = axes[0].get_legend_handles_labels()
        fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.08), fontsize=9)
        fig.tight_layout(rect=(0, 0.06, 1, 1))
        save(fig, fname)

    # ---- Fig: gain per architecture vs control, two-seed means ----
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.0), sharey=True)
    gains = {}
    for ax, ds, title in [(axes[0], 'Cifar10', 'CIFAR-10'), (axes[1], 'Cifar100', 'CIFAR-100')]:
        w = 0.36
        for j, (v, col, lab) in enumerate([('FedGDBD-AGC', PURPLE, 'AGC'), ('FedGDBD-AGS', GOLD, 'AGS')]):
            g = []
            for a in range(4):
                d = [N[f'{ds}_{v}_s{s}']['per'][N[f'{ds}_{v}_s{s}']['best_round']][a] -
                     N[f'{ds}_FedGDBD-S_s{s}']['per'][N[f'{ds}_FedGDBD-S_s{s}']['best_round']][a] for s in (0, 1)]
                g.append(st.mean(d))
            gains[f'{ds}_{v}'] = g
            xs = [i + (j - 0.5) * w for i in range(4)]
            ax.bar(xs, g, w * 0.94, color=col, label=lab)
            for x, val in zip(xs, g):
                ax.text(x, val + (0.05 if val >= 0 else -0.05), f'{val:+.2f}', ha='center',
                        va='bottom' if val >= 0 else 'top', fontsize=8)
        ax.axhline(0, color=GREY, lw=0.8)
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_title(title, loc='left')
    axes[0].set_ylabel('Gain over control (pt)')
    axes[0].set_ylim(-1.2, 1.6)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=2, bbox_to_anchor=(0.5, -0.07), fontsize=9)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save(fig, 'arch_gains')

    # ---- data.json ----
    def slim(d):
        return {k: v for k, v in d.items() if k not in ('acc', 'std', 'clients', 'g_acc', 'kept')} | {
            'per_best': d['per'][d['best_round']] if d['per'] else None, 'per_last': d['per'][-1] if d['per'] else None,
            'clients_best': d['clients'][d['best_round']] if d['clients'] else None,
            'g_acc_mean': [st.mean(r[a] for r in d['g_acc']) for a in range(4)] if d['g_acc'] else None,
            'kept_mean': [st.mean(r[a] for r in d['kept']) for a in range(4)] if d['kept'] else None,
            'g_acc_r0': d['g_acc'][0] if d['g_acc'] else None, 'kept_r0': d['kept'][0] if d['kept'] else None,
            'n_evals': len(d['acc']), 'acc_curve': d['acc']}
    data = {'repro': {k: slim(v) for k, v in R.items()}, 'novelty': {k: slim(v) for k, v in N.items()}, 'arch_gains': gains}
    for k, v in data['repro'].items():
        v.pop('per', None)
    for k, v in data['novelty'].items():
        v.pop('per', None)
    json.dump(data, open(os.path.join(ROOT, 'report', 'data.json'), 'w'), indent=1)
    print('figures in report/figures, numbers in report/data.json')


if __name__ == '__main__':
    main()
