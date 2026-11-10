"""Figures, tables and numbers for the IEEE paper draft, all computed from the run logs.

Usage (from the repo root):
    python analysis/paper_figures.py

Reads   experiments/cifar10|cifar100/logs           (reproduction, 50 rounds)
        experiments/novelty/run*_seed*/<dataset>/logs (extension, 20 rounds, every seed found)
Writes  paper/figures/*.pdf           every plot in the paper
        paper/generated.tex           \\newcommand tables and numbers used in the text
        paper/tables_repro.tex        reproduction tables (copied from report/tables.tex)

Only seeds with all four extension runs finished enter the extension results, so adding
seed 4 later means: copy its logs into experiments/novelty/run5_seed4/ and rerun this script.
"""
import glob
import math
import os
import re
import shutil
import statistics as st
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'analysis'))
from report_assets import parse            # noqa: E402  same log parser as the report
from multiseed_summary import paired       # noqa: E402  same paired statistics as PROTOCOL.md

EXP = os.path.join(ROOT, 'experiments')
OUT = os.path.join(ROOT, 'paper')
FIG = os.path.join(OUT, 'figures')
ARCH = ['CNN', 'GoogLeNet', 'MobileNetV2', 'ResNet18']
DS = [('Cifar10', 'CIFAR-10', 'Ten'), ('Cifar100', 'CIFAR-100', 'Hun')]
INK, GREY, LIGHT, GRID = '#26292B', '#6E7377', '#AEB3B6', '#E4E6E5'
GOLD, PURPLE, TEAL, BLUE = '#B8892B', '#6250D6', '#3E8E7E', '#4C78A8'
ARCH_COL = [GREY, BLUE, PURPLE, TEAL]
# extension methods: key in logs -> (label, colour, macro tag)
EXT = {'FedGDBD-S': ('FedGDBD-S (control)', GREY, 'Ctl'),
       'FedGDBD-S-amatch': (r'Matched $\alpha$', TEAL, 'Am'),
       'FedGDBD-AGC': ('AGC', PURPLE, 'Agc'),
       'FedGDBD-AGS': ('AGS', GOLD, 'Ags')}
PAIRS = [('FedGDBD-AGC', 'FedGDBD-S'), ('FedGDBD-AGS', 'FedGDBD-S'), ('FedGDBD-S-amatch', 'FedGDBD-S'),
         ('FedGDBD-AGC', 'FedGDBD-S-amatch'), ('FedGDBD-AGS', 'FedGDBD-S-amatch')]

COL1, COL2 = 3.45, 7.16   # IEEE column and text width (inches)
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'Liberation Serif', 'Nimbus Roman', 'DejaVu Serif'],
    'mathtext.fontset': 'stix', 'font.size': 8, 'axes.titlesize': 8.5, 'axes.labelsize': 8,
    'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'legend.fontsize': 7.5,
    'axes.edgecolor': GREY, 'axes.labelcolor': INK, 'axes.titlecolor': INK,
    'xtick.color': GREY, 'ytick.color': GREY, 'text.color': INK,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': 0.7,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.6,
    'axes.axisbelow': True, 'legend.frameon': False, 'lines.linewidth': 1.3,
})


def save(fig, name):
    os.makedirs(FIG, exist_ok=True)
    fig.savefig(os.path.join(FIG, name + '.pdf'), bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


# ===================================================================== load
def load():
    R = {}
    for ds, _, _ in DS:
        for m in ['FedProto', 'LG-FedAvg', 'FedGDBD', 'FedGDBD-S']:
            R[(ds, m)] = parse(os.path.join(EXP, ds.lower(), 'logs', f'{ds}_{m}.log'))
        R[(ds, 'bug')] = parse(os.path.join(EXP, ds.lower(), 'logs', 'old', f'{ds}_FedGDBD_v1_buggy_IKD.log'))
    N = {}
    for path in glob.glob(os.path.join(EXP, 'novelty', 'run*_seed*', '*', 'logs', '*.log')):
        seed = int(re.search(r'_seed(\d+)', path).group(1))
        ds, algo = os.path.basename(path)[:-4].split('_', 1)
        if algo in EXT:
            r = parse(path)
            if len(r['acc']) >= 21:          # rounds 0..20 all evaluated
                N[(ds, algo, seed)] = r
    seeds = sorted({s for (_, _, s) in N if all((ds, a, s) in N for ds, _, _ in DS for a in EXT)})
    return R, N, seeds


# ===================================================================== reproduction figures
def fig_repro(R):
    # convergence over 50 rounds
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.35))
    style = [('FedProto', LIGHT, 'FedProto'), ('LG-FedAvg', GREY, 'LG-FedAvg'),
             ('FedGDBD', PURPLE, 'Fed-GDBD (faithful)'), ('FedGDBD-S', GOLD, 'FedGDBD-S (our fix)')]
    for ax, (ds, name, _) in zip(axes, DS):
        for m, col, lab in style:
            a = R[(ds, m)]['acc']
            ax.plot(range(len(a)), a, color=col, label=lab, lw=1.4 if m.startswith('FedGDBD') else 1.1)
            if m == 'FedGDBD':
                b = a.index(max(a))
                ax.plot(b, a[b], 'o', color=PURPLE, ms=3.5)
                ax.plot(len(a) - 1, a[-1], 'o', mfc='white', mec=PURPLE, ms=3.5)
        ax.set_title(name, loc='left')
        ax.set_xlabel('Communication round')
        ax.set_xlim(0, 50)
        ax.set_ylim((50, 90) if ds == 'Cifar10' else (0, 50))
    axes[0].set_ylabel('Averaged test accuracy (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.5)
    save(fig, 'repro_convergence')

    # collapse per architecture
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.3))
    for ax, (ds, name, _) in zip(axes, DS):
        f, s = R[(ds, 'FedGDBD')], R[(ds, 'FedGDBD-S')]
        b = f['best_round']
        ser = [(f'Faithful, best round', f['per'][b], LIGHT), ('Faithful, last round', f['per'][-1], PURPLE),
               ('FedGDBD-S, round 50', s['per'][-1], GOLD)]
        w = 0.26
        for j, (lab, vals, col) in enumerate(ser):
            xs = [i + (j - 1) * w for i in range(4)]
            ax.bar(xs, vals, w * 0.92, color=col, label=lab)
            for x, v in zip(xs, vals):
                ax.text(x, v + 0.8, f'{v:.1f}', ha='center', va='bottom', fontsize=5.8)
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_ylim(0, 100 if ds == 'Cifar10' else 60)
        ax.set_title(f'({"a" if ds == "Cifar10" else "b"}) {name}: best round {b}, last round {len(f["per"]) - 1}', loc='left')
    axes[0].set_ylabel('Test accuracy (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.5)
    save(fig, 'repro_collapse')

    # IKD bug, CIFAR-100
    fig, ax = plt.subplots(figsize=(COL1, 1.9))
    bug, fix = R[('Cifar100', 'bug')], R[('Cifar100', 'FedGDBD')]
    ax.plot(range(len(bug['acc'])), bug['acc'], color=GREY, marker='o', ms=2.5, label='first IKD loss (bug)')
    ax.plot(range(len(fix['acc'])), fix['acc'], color=PURPLE, marker='o', ms=2.5, label='fixed IKD loss')
    ax.plot([len(bug['acc']) - 1], [bug['acc'][-1]], 'x', color=INK, ms=6, mew=1.3)
    ax.annotate('NaN loss, run stops', (len(bug['acc']) - 1, bug['acc'][-1]), xytext=(6, -12),
                textcoords='offset points', fontsize=7)
    ax.set_xlabel('Communication round')
    ax.set_ylabel('Averaged test acc. (%)')
    ax.set_ylim(20, 45)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(loc='lower left')
    save(fig, 'repro_ikd_bug')

    # per-architecture accuracy of all methods
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.3))
    for ax, (ds, name, _) in zip(axes, DS):
        w = 0.2
        for j, (m, col, lab) in enumerate(style):
            r = R[(ds, m)]
            ax.bar([i + (j - 1.5) * w for i in range(4)], r['per'][r['best_round']], w * 0.92, color=col, label=lab)
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_title(name, loc='left')
        ax.set_ylim(0, 100 if ds == 'Cifar10' else 60)
    axes[0].set_ylabel('Accuracy at best round (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.5)
    save(fig, 'repro_arch_methods')


# ===================================================================== extension figures
def fig_ext(N, seeds):
    # convergence: mean +- SD band over seeds
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.4))
    for ax, (ds, name, _) in zip(axes, DS):
        for algo, (lab, col, _) in EXT.items():
            curves = [N[(ds, algo, s)]['acc'][:21] for s in seeds]
            mu = [st.mean(c[r] for c in curves) for r in range(21)]
            sd = [st.stdev(c[r] for c in curves) if len(curves) > 1 else 0 for r in range(21)]
            ax.plot(range(21), mu, color=col, label=lab, lw=1.3)
            ax.fill_between(range(21), [m - s for m, s in zip(mu, sd)], [m + s for m, s in zip(mu, sd)], color=col, alpha=0.13, lw=0)
        ax.set_title(name, loc='left')
        ax.set_xlabel('Communication round')
        ax.set_xlim(0, 20)
        ax.set_ylim((82, 88) if ds == 'Cifar10' else (34, 44))
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ins = ax.inset_axes([0.45, 0.08, 0.52, 0.45])
        for algo, (lab, col, _) in EXT.items():
            curves = [N[(ds, algo, s)]['acc'][:21] for s in seeds]
            mu = [st.mean(c[r] for c in curves) for r in range(21)]
            ins.plot(range(10, 21), mu[10:], color=col, lw=1.1)
        ins.set_title('rounds 10 to 20', fontsize=6.5, loc='left', pad=2)
        ins.tick_params(labelsize=6)
        ins.grid(True, axis='y')
    axes[0].set_ylabel('Averaged test accuracy (%)')
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.5)
    save(fig, 'ext_convergence')

    # per-seed paired gaps (best round)
    lab_pair = {('FedGDBD-AGC', 'FedGDBD-S'): 'AGC $-$ control', ('FedGDBD-AGS', 'FedGDBD-S'): 'AGS $-$ control',
                ('FedGDBD-S-amatch', 'FedGDBD-S'): r'matched $\alpha$ $-$ control',
                ('FedGDBD-AGC', 'FedGDBD-S-amatch'): r'AGC $-$ matched $\alpha$', ('FedGDBD-AGS', 'FedGDBD-S-amatch'): r'AGS $-$ matched $\alpha$'}
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.2), sharey=True)
    markers = ['o', 's', '^', 'D', 'v', 'P']
    for ax, (ds, name, _) in zip(axes, DS):
        for i, (a, b) in enumerate(PAIRS):
            gaps = [N[(ds, a, s)]['best'] - N[(ds, b, s)]['best'] for s in seeds]
            y = len(PAIRS) - 1 - i
            for k, (s, g) in enumerate(zip(seeds, gaps)):
                ax.plot(g, y + (k - (len(seeds) - 1) / 2) * 0.09, markers[k % 6], color=GREY, ms=3.2, mfc='white', mew=0.8,
                        label=f'seed {s}' if i == 0 else None)
            m = st.mean(gaps)
            ax.plot([m, m], [y - 0.3, y + 0.3], color=EXT[a][1], lw=2.0)
        ax.axvline(0, color=INK, lw=0.7)
        ax.set_yticks(range(len(PAIRS)), [lab_pair[p] for p in PAIRS][::-1])
        ax.set_xlabel('Gap in best-round accuracy (pt)')
        ax.set_title(name, loc='left')
        ax.grid(True, axis='x')
        ax.grid(False, axis='y')
        ax.set_xlim(-1.0, 1.2)
    h, l = axes[0].get_legend_handles_labels()
    h.append(plt.Line2D([], [], color=INK, lw=2.0))
    l.append('mean over seeds')
    fig.legend(h, l, loc='lower center', ncol=len(l), bbox_to_anchor=(0.55, -0.08))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.0)
    save(fig, 'ext_gaps')

    # per-architecture gain over the control, mean over seeds
    gains = {}
    fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.2), sharey=True)
    for ax, (ds, name, _) in zip(axes, DS):
        w = 0.26
        for j, algo in enumerate(['FedGDBD-AGC', 'FedGDBD-AGS', 'FedGDBD-S-amatch']):
            g = [st.mean(N[(ds, algo, s)]['per'][N[(ds, algo, s)]['best_round']][a] -
                         N[(ds, 'FedGDBD-S', s)]['per'][N[(ds, 'FedGDBD-S', s)]['best_round']][a] for s in seeds) for a in range(4)]
            gains[(ds, algo)] = g
            xs = [i + (j - 1) * w for i in range(4)]
            ax.bar(xs, g, w * 0.92, color=EXT[algo][1], label=EXT[algo][0])
            for x, v in zip(xs, g):
                ax.text(x, v + (0.04 if v >= 0 else -0.04), f'{v:+.2f}', ha='center', va='bottom' if v >= 0 else 'top', fontsize=5.5)
        ax.axhline(0, color=GREY, lw=0.7)
        ax.set_xticks(range(4), ARCH)
        ax.tick_params(axis='x', length=0)
        ax.set_title(name, loc='left')
    axes[0].set_ylabel('Gain over control (pt)')
    lo = min(min(v) for v in gains.values())
    hi = max(max(v) for v in gains.values())
    axes[0].set_ylim(min(-0.5, lo - 0.3), hi + 0.35)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc='lower center', ncol=3, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.0)
    save(fig, 'ext_arch_gains')

    # gate statistics over rounds, mean over seeds (thin lines: single seeds)
    for key, algo, fname, ylab in [('g_acc', 'FedGDBD-AGC', 'gate_gacc', 'accuracy of $g$ on own features'),
                                   ('kept', 'FedGDBD-AGS', 'gate_kept', 'share of images distilled')]:
        fig, axes = plt.subplots(1, 2, figsize=(COL2, 2.2), sharey=True)
        for ax, (ds, name, _) in zip(axes, DS):
            for a in range(4):
                per_seed = [[r[a] for r in N[(ds, algo, s)][key]] for s in seeds]
                n = min(len(p) for p in per_seed)
                for p in per_seed:
                    ax.plot(range(n), p[:n], color=ARCH_COL[a], lw=0.5, alpha=0.35)
                ax.plot(range(n), [st.mean(p[r] for p in per_seed) for r in range(n)], color=ARCH_COL[a], lw=1.5, label=ARCH[a])
            ax.set_title(name, loc='left')
            ax.set_xlabel('Communication round')
            ax.set_ylim(0, 1.02)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        axes[0].set_ylabel(ylab)
        h, l = axes[0].get_legend_handles_labels()
        fig.legend(h, l, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.07))
        fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.0)
        save(fig, fname)
    return gains


# ===================================================================== tables and numbers
def fmt(x, nd=2):
    return f'{x:.{nd}f}'


def sgn(x, nd=2):
    return ('+' if x >= 0 else '$-$') + f'{abs(x):.{nd}f}'


def pval(p):
    return '$<$0.001' if p < 0.001 else f'{p:.3f}'


def tables(N, seeds, gains):
    out = ['% generated by analysis/paper_figures.py -- do not edit by hand\n']
    cmd = lambda name, body: out.append(f'\\newcommand{{\\{name}}}{{{body}}}\n')
    tag_seeds = ', '.join(str(s) for s in seeds)
    cmd('NSeeds', str(len(seeds)))
    cmd('SeedList', tag_seeds)
    cmd('SeedLast', str(seeds[-1]))
    new = [s for s in seeds if s >= 2]
    cmd('NNewSeeds', str(len(new)))

    # numbers for the text: means, SDs, gaps, tests
    for ds, _, t in DS:
        for algo, (_, _, a) in EXT.items():
            for k, nm in (('best', 'Best'), ('last', 'Last')):
                v = [N[(ds, algo, s)][k] for s in seeds]
                cmd(f'M{t}{a}{nm}', fmt(st.mean(v)))
                cmd(f'S{t}{a}{nm}', fmt(st.stdev(v) if len(v) > 1 else 0))
        for x, y in PAIRS:
            tx, ty = EXT[x][2], EXT[y][2]
            for k, nm in (('best', 'Best'), ('last', 'Last')):
                gaps = [N[(ds, x, s)][k] - N[(ds, y, s)][k] for s in seeds]
                m, sd, (lo, hi), p2, p1 = paired(gaps)
                base = f'G{t}{tx}{ty}{nm}'
                cmd(base, sgn(m))
                cmd(base + 'Lo', sgn(lo))
                cmd(base + 'Hi', sgn(hi))
                cmd(base + 'Pone', pval(p1))
                cmd(base + 'Ptwo', pval(p2))
                cmd(base + 'Wins', f'{sum(g > 0 for g in gaps)}/{len(gaps)}')
                cmd(base + 'Seeds', ', '.join(sgn(g) for g in gaps))
                if new:
                    gn = [N[(ds, x, s)][k] - N[(ds, y, s)][k] for s in new]
                    cmd(base + 'New', ', '.join(sgn(g) for g in gn))
                    cmd(base + 'NewMean', sgn(st.mean(gn)))

    # main extension table: mean +- SD, best and last round
    rows = []
    for algo, (lab, _, a) in [('FedGDBD-S', EXT['FedGDBD-S']), ('FedGDBD-S-amatch', EXT['FedGDBD-S-amatch']),
                              ('FedGDBD-AGC', EXT['FedGDBD-AGC']), ('FedGDBD-AGS', EXT['FedGDBD-AGS'])]:
        cells = [lab]
        for k in ('best', 'last'):
            for ds, _, _ in DS:
                v = [N[(ds, algo, s)][k] for s in seeds]
                best_algo = max(EXT, key=lambda q: st.mean(N[(ds, q, s)][k] for s in seeds))
                txt = f'{st.mean(v):.2f} $\\pm$ {st.stdev(v):.2f}'
                cells.append(f'\\textbf{{{txt}}}' if algo == best_algo else txt)
        rows.append(' & '.join(cells) + r' \\')
    cmd('TabExtMain', r'''\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{Best round} & \multicolumn{2}{c}{Last round (20)} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Method & CIFAR-10 & CIFAR-100 & CIFAR-10 & CIFAR-100 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}')

    # per-seed values
    rows = []
    for ds, name, _ in DS:
        for i, algo in enumerate(['FedGDBD-S', 'FedGDBD-S-amatch', 'FedGDBD-AGC', 'FedGDBD-AGS']):
            v = [N[(ds, algo, s)]['best'] for s in seeds]
            rows.append(' & '.join([name if i == 0 else '', EXT[algo][0]] + [fmt(x) for x in v]) + r' \\')
        rows.append('\\midrule' if ds == 'Cifar10' else '')
    cmd('TabExtSeeds', r'\begin{tabular}{ll' + 'r' * len(seeds) + '}\n\\toprule\nDataset & Method & ' +
        ' & '.join(f'Seed {s}' for s in seeds) + ' \\\\\n\\midrule\n' + '\n'.join(r for r in rows if r) + '\n\\bottomrule\n\\end{tabular}')

    # paired tests
    hyp = {('Cifar100', 'FedGDBD-AGC', 'FedGDBD-S'): 'H1', ('Cifar100', 'FedGDBD-AGC', 'FedGDBD-S-amatch'): 'H2',
           ('Cifar10', 'FedGDBD-AGS', 'FedGDBD-S'): 'H3'}
    short = {'FedGDBD-S': 'control', 'FedGDBD-S-amatch': r'matched $\alpha$', 'FedGDBD-AGC': 'AGC', 'FedGDBD-AGS': 'AGS'}
    rows = []
    for ds, name, _ in DS:
        for x, y in PAIRS:
            if (x, y) == ('FedGDBD-S-amatch', 'FedGDBD-S'):
                continue   # not in the protocol; reported descriptively in the text
            gaps = [N[(ds, x, s)]['best'] - N[(ds, y, s)]['best'] for s in seeds]
            m, sd, (lo, hi), p2, p1 = paired(gaps)
            h = hyp.get((ds, x, y))
            p = pval(p1) + ' (1s)' if h else pval(p2) + ' (2s)'
            newm = sgn(st.mean([N[(ds, x, s)]['best'] - N[(ds, y, s)]['best'] for s in new])) if new else '--'
            rows.append(' & '.join([name, f'{short[x]} vs {short[y]}', h or '--', sgn(m), f'[{sgn(lo)}, {sgn(hi)}]', p,
                                    f'{sum(g > 0 for g in gaps)}/{len(gaps)}', newm]) + r' \\')
        if ds == 'Cifar10':
            rows.append('\\midrule')
    cmd('TabTests', r'''\begin{tabular}{llcrcccr}
\toprule
Dataset & Comparison & Hyp. & Mean gap & 95\% CI & $p$ & Wins & Seeds $\geq$2 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}')

    # per-architecture gain numbers for the text
    tags = {'FedGDBD-AGC': 'Agc', 'FedGDBD-AGS': 'Ags', 'FedGDBD-S-amatch': 'Am'}
    for ds, _, t in DS:
        for algo, tg in tags.items():
            for a, an in enumerate(['Cnn', 'Goog', 'Mob', 'Res']):
                cmd(f'Gain{t}{tg}{an}', sgn(gains[(ds, algo)][a]))

    # Holm correction over the three pre-registered one-sided tests (best round)
    hp = []
    for name, (ds, x, y) in [('One', ('Cifar100', 'FedGDBD-AGC', 'FedGDBD-S')), ('Two', ('Cifar100', 'FedGDBD-AGC', 'FedGDBD-S-amatch')),
                             ('Three', ('Cifar10', 'FedGDBD-AGS', 'FedGDBD-S'))]:
        gaps = [N[(ds, x, s)]['best'] - N[(ds, y, s)]['best'] for s in seeds]
        hp.append((paired(gaps)[4], name))
    hp.sort()
    adj, run = {}, 0.0
    for i, (p, name) in enumerate(hp):
        run = max(run, min(1.0, p * (len(hp) - i)))
        adj[name] = run
    for name, v in adj.items():
        cmd(f'Holm{name}', pval(v))

    # per-architecture gains
    rows = []
    for ds, name, _ in DS:
        for i, algo in enumerate(['FedGDBD-AGC', 'FedGDBD-AGS', 'FedGDBD-S-amatch']):
            rows.append(' & '.join([name if i == 0 else '', EXT[algo][0]] + [sgn(v) for v in gains[(ds, algo)]]) + r' \\')
        if ds == 'Cifar10':
            rows.append('\\midrule')
    cmd('TabArchGain', r'''\begin{tabular}{llrrrr}
\toprule
Dataset & Method & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}')

    # gate statistics, mean over rounds and seeds, and round 0
    rows = []
    for ds, name, t in DS:
        for i, (key, algo, lab) in enumerate([('g_acc', 'FedGDBD-AGC', 'AGC: $g$ correct, mean'), ('g_acc', 'FedGDBD-AGC', 'AGC: $g$ correct, round 0'),
                                              ('kept', 'FedGDBD-AGS', 'AGS: share distilled, mean'), ('kept', 'FedGDBD-AGS', 'AGS: share distilled, round 0')]):
            vals = []
            for a in range(4):
                if 'round 0' in lab:
                    vals.append(st.mean(N[(ds, algo, s)][key][0][a] for s in seeds))
                else:
                    vals.append(st.mean(st.mean(r[a] for r in N[(ds, algo, s)][key]) for s in seeds))
            rows.append(' & '.join([name if i == 0 else '', lab] + [f'{v:.2f}' for v in vals]) + r' \\')
            if i == 0:
                for a in range(4):
                    cmd(f'Gacc{t}{["Cnn", "Goog", "Mob", "Res"][a]}', f'{vals[a]:.2f}')
            if i == 1:
                for a in range(4):
                    cmd(f'GaccZero{t}{["Cnn", "Goog", "Mob", "Res"][a]}', f'{vals[a]:.2f}')
            if i == 2:
                for a in range(4):
                    cmd(f'Kept{t}{["Cnn", "Goog", "Mob", "Res"][a]}', f'{vals[a]:.2f}')
        if ds == 'Cifar10':
            rows.append('\\midrule')
    cmd('TabGate', r'''\begin{tabular}{llrrrr}
\toprule
Dataset & Statistic & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}')

    # per-architecture accuracy of every extension run (appendix)
    rows = []
    for ds, name, _ in DS:
        first = True
        for s in seeds:
            for algo in ['FedGDBD-S', 'FedGDBD-S-amatch', 'FedGDBD-AGC', 'FedGDBD-AGS']:
                r = N[(ds, algo, s)]
                per = r['per'][r['best_round']]
                rows.append(' & '.join([name if first else '', str(s), EXT[algo][0], str(r['best_round'])] + [f'{v:.1f}' for v in per]) + r' \\')
                first = False
        if ds == 'Cifar10':
            rows.append('\\midrule')
    cmd('TabExtArch', r'''\begin{tabular}{lclrrrrr}
\toprule
Dataset & Seed & Method & Best rd. & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}')

    open(os.path.join(OUT, 'generated.tex'), 'w').write(''.join(out))


def main():
    R, N, seeds = load()
    if not seeds:
        sys.exit('no complete extension seed found')
    print('extension seeds used:', seeds)
    fig_repro(R)
    gains = fig_ext(N, seeds)
    tables(N, seeds, gains)
    src = os.path.join(ROOT, 'report', 'tables.tex')
    if os.path.exists(src):   # keep only the reproduction tables; the extension tables above replace the 2-seed ones
        txt = open(src).read()
        keep = ['TabReproMain', 'TabReproRuns', 'TabCollapse', 'TabArchMethods', 'TabClientsTen', 'TabClientsHundred']
        blocks = re.split(r'(?=\\newcommand\{\\)', txt)
        out = [b for b in blocks if any(b.startswith('\\newcommand{\\' + k + '}') for k in keep)]
        open(os.path.join(OUT, 'tables_repro.tex'), 'w').write('% reproduction tables, copied from report/tables.tex\n' + ''.join(out))
    print('wrote paper/figures/*.pdf, paper/generated.tex, paper/tables_repro.tex')


if __name__ == '__main__':
    main()
