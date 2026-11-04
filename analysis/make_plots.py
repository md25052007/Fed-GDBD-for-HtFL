"""Make the presentation figures from the run logs.

Usage (from the repo root):
    python analysis/make_plots.py

Reads the reproduction logs in experiments/cifar10/logs and experiments/cifar100/logs
and writes, to presentation/figures/ (PNG at 300 dpi + PDF):
  collapse_per_arch  CIFAR-100 accuracy per client architecture: faithful Eq. 13 at its
                     best round and at its last round, and FedGDBD-S at round 50
  convergence        averaged test accuracy vs round for the four methods, both datasets;
                     faithful Fed-GDBD: filled dot = best round, open dot = round it was stopped

Accuracy per architecture = mean test accuracy of the 5 clients that run it
(client id mod 4: CNN, GoogLeNet, MobileNetV2, ResNet18).
"""
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'presentation', 'figures')
ARCH = ['CNN', 'GoogLeNet', 'MobileNetV2', 'ResNet18']

# colours of the slide deck
INK, GREY, LIGHT, GRID = '#26292B', '#6E7377', '#AEB3B6', '#E4E6E5'
GOLD, PURPLE = '#B8892B', '#6250D6'

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Cambria', 'Caladea', 'Liberation Serif', 'DejaVu Serif'],
    'font.size': 11, 'axes.titlesize': 12, 'axes.labelsize': 11,
    'axes.edgecolor': GREY, 'axes.labelcolor': INK, 'axes.titlecolor': INK,
    'xtick.color': GREY, 'ytick.color': GREY, 'text.color': INK,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.8,
    'axes.axisbelow': True, 'legend.frameon': False,
})


def read_log(path):
    """Return (averaged accuracy per round, per-architecture accuracy per round), in %."""
    txt = open(path, encoding='utf-8', errors='ignore').read()
    acc = [100 * float(a) for a in re.findall(r'Averaged Test Accuracy: ([\d.]+)', txt)]
    per = []
    for block in txt.split('Evaluate heterogeneous models')[1:]:
        cs = re.findall(r'Client (\d+): Acc: ([\d.]+)', block)
        if len(cs) >= 20:
            per.append([100 * sum(float(a) for c, a in cs if int(c) % 4 == k) / 5 for k in range(4)])
    return acc, per


def log(ds, algo):
    return read_log(os.path.join(ROOT, 'experiments', ds.lower(), 'logs', f'{ds}_{algo}.log'))


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(OUT, f'{name}.{ext}'), dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('wrote', os.path.join('presentation', 'figures', name + '.png/.pdf'))


def collapse_per_arch():
    facc, fper = log('Cifar100', 'FedGDBD')
    _, sper = log('Cifar100', 'FedGDBD-S')
    b = facc.index(max(facc))
    series = [
        (f'Faithful Eq. 13, best round ({b})', fper[b], LIGHT),
        (f'Faithful Eq. 13, round {len(fper) - 1}', fper[-1], PURPLE),
        (f'FedGDBD-S, round {len(sper) - 1}', sper[-1], GOLD),
    ]
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    w = 0.26
    for j, (label, vals, col) in enumerate(series):
        xs = [i + (j - 1) * w for i in range(4)]
        bars = ax.bar(xs, vals, w * 0.94, color=col, label=label)
        for x, v in zip(xs, vals):
            ax.text(x, v + 0.8, f'{v:.1f}', ha='center', va='bottom', fontsize=9, color=INK)
    ax.set_xticks(range(4), ARCH)
    ax.tick_params(axis='x', length=0)
    ax.set_ylim(0, 60)
    ax.set_ylabel('Test accuracy (%)')
    ax.set_title('CIFAR-100: accuracy by client architecture', loc='left')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.09), ncol=3, fontsize=9, handlelength=1.2)
    save(fig, 'collapse_per_arch')


def convergence():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.0))
    styles = [('FedProto', 'FedProto', LIGHT, 1.6), ('LG-FedAvg', 'LG-FedAvg', GREY, 1.6),
              ('FedGDBD', 'Fed-GDBD (faithful)', PURPLE, 2.0), ('FedGDBD-S', 'FedGDBD-S (our fix)', GOLD, 2.2)]
    for ax, ds, title, ylim in [(axes[0], 'Cifar10', 'CIFAR-10', (50, 90)), (axes[1], 'Cifar100', 'CIFAR-100', (0, 50))]:
        for algo, label, col, lw in styles:
            acc, _ = log(ds, algo)
            ax.plot(range(len(acc)), acc, color=col, lw=lw, label=label)
            if algo == 'FedGDBD':
                # filled dot = best round before the collapse, open dot = round where we stopped the run
                b = acc.index(max(acc))
                ax.plot([b], [acc[b]], 'o', color=PURPLE, ms=5.5, zorder=5)
                ax.plot([len(acc) - 1], [acc[-1]], 'o', color=PURPLE, ms=5.5, mfc='white', zorder=5)
        ax.set_xlim(0, 50)
        ax.set_ylim(*ylim)
        ax.set_xlabel('Communication round')
        ax.set_title(title, loc='left')
    axes[0].set_ylabel('Averaged test accuracy (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.06), fontsize=10)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, 'convergence')


if __name__ == '__main__':
    collapse_per_arch()
    convergence()
