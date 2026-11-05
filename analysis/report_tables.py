"""LaTeX tables for the project report, generated from report/data.json.

Usage (from the repo root, after analysis/report_assets.py):
    python analysis/report_tables.py

Writes report/tables.tex, one \\newcommand per table, so no number in the
report's results tables is typed by hand.
"""
import json
import os
import statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = json.load(open(os.path.join(ROOT, 'report', 'data.json')))
R, N = D['repro'], D['novelty']
ARCH = ['CNN', 'GoogLeNet', 'MobileNetV2', 'ResNet18']
PAPER = {'Cifar10': {'FedProto': 82.75, 'LG-FedAvg': 86.64, 'FedGDBD': 87.90},
         'Cifar100': {'FedProto': 35.38, 'LG-FedAvg': 43.30, 'FedGDBD': 45.09}}
MIN_ROUND = {'Cifar10_FedProto': 9.6, 'Cifar100_FedProto': 8.4}  # these logs print time in another format (progress.py)
NAME = {'FedProto': 'FedProto', 'LG-FedAvg': 'LG-FedAvg', 'FedGDBD': 'Fed-GDBD (faithful)', 'FedGDBD-S': 'FedGDBD-S (our fix)'}
VNAME = {'FedGDBD-S': 'FedGDBD-S (control)', 'FedGDBD-AGC': 'FedGDBD-AGC', 'FedGDBD-AGS': 'FedGDBD-AGS'}
out = []


def f2(x):
    return f'{x:.2f}'


def sg(x):
    return ('+' if x >= 0 else '$-$') + f'{abs(x):.2f}'


def cmd(name, body):
    out.append(f'\\newcommand{{\\{name}}}{{%\n{body}}}\n')


# ---- reproduction: ours vs paper ----
rows = []
for m in ['FedProto', 'LG-FedAvg', 'FedGDBD', 'FedGDBD-S']:
    cells = [NAME[m] + (' $^\\dagger$' if m == 'FedGDBD' else '')]
    for ds in ['Cifar10', 'Cifar100']:
        ours = R[f'{ds}_{m}']['best']
        p = PAPER[ds]['FedGDBD' if m == 'FedGDBD-S' else m]
        cells += [f2(ours), f2(p), sg(ours - p)]
    row = ' & '.join(cells) + r' \\'
    rows.append(('\\textbf{' + row.replace(' & ', '} & \\textbf{', 1) if False else row))
cmd('TabReproMain', r'''\begin{tabular}{lrrrrrr}
\toprule
 & \multicolumn{3}{c}{CIFAR-10} & \multicolumn{3}{c}{CIFAR-100} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Method & Ours & Paper & $\Delta$ & Ours & Paper & $\Delta$ \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')

# ---- reproduction: run details ----
rows = []
for ds in ['Cifar10', 'Cifar100']:
    for m in ['FedProto', 'LG-FedAvg', 'FedGDBD', 'FedGDBD-S']:
        r = R[f'{ds}_{m}']
        mpr = r['min_per_round'] or MIN_ROUND.get(f'{ds}_{m}')
        pre = f"{r['pretrain_s'] / 60:.1f}" if r['pretrain_s'] else '--'
        rows.append(f"{'CIFAR-10' if ds == 'Cifar10' else 'CIFAR-100'} & {NAME[m]} & {r['n_evals'] - 1} & {r['best_round']} & "
                    f"{f2(r['best'])} & {f2(r['last'])} & {f2(r['std_at_best'])} & {mpr:.1f} & {pre} \\\\")
    if ds == 'Cifar10':
        rows.append('\\midrule')
cmd('TabReproRuns', r'''\begin{tabular}{llrrrrrrr}
\toprule
Dataset & Method & Rounds & Best rd. & Best (\%) & Last (\%) & Client SD & Min/rd. & Pre-train (min) \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')

# ---- reproduction: collapse per architecture ----
rows = []
for ds in ['Cifar10', 'Cifar100']:
    f, s = R[f'{ds}_FedGDBD'], R[f'{ds}_FedGDBD-S']
    lab = 'CIFAR-10' if ds == 'Cifar10' else 'CIFAR-100'
    rows.append(f"{lab} & Faithful, best round ({f['best_round']}) & " + ' & '.join(f'{v:.1f}' for v in f['per_best']) + r' \\')
    rows.append(f" & Faithful, round {f['n_evals'] - 1} & " + ' & '.join(f'{v:.1f}' for v in f['per_last']) + r' \\')
    rows.append(f" & FedGDBD-S, round {s['n_evals'] - 1} & " + ' & '.join(f'{v:.1f}' for v in s['per_last']) + r' \\')
    if ds == 'Cifar10':
        rows.append('\\midrule')
cmd('TabCollapse', r'''\begin{tabular}{llrrrr}
\toprule
Dataset & Model state & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')

# ---- reproduction: per architecture, all methods at best round ----
rows = []
for ds in ['Cifar10', 'Cifar100']:
    lab = 'CIFAR-10' if ds == 'Cifar10' else 'CIFAR-100'
    for i, m in enumerate(['FedProto', 'LG-FedAvg', 'FedGDBD', 'FedGDBD-S']):
        r = R[f'{ds}_{m}']
        rows.append(f"{lab if i == 0 else ''} & {NAME[m]} & " + ' & '.join(f'{v:.1f}' for v in r['per_best']) + r' \\')
    if ds == 'Cifar10':
        rows.append('\\midrule')
cmd('TabArchMethods', r'''\begin{tabular}{llrrrr}
\toprule
Dataset & Method & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')


# ---- novelty: best and last ----
def nov_table(key, name):
    rows = []
    ctrl = {ds: st.mean(N[f'{ds}_FedGDBD-S_s{s}'][key] for s in (0, 1)) for ds in ['Cifar10', 'Cifar100']}
    for v in ['FedGDBD-S', 'FedGDBD-AGC', 'FedGDBD-AGS']:
        cells = [VNAME[v]]
        for ds in ['Cifar10', 'Cifar100']:
            a, b = N[f'{ds}_{v}_s0'][key], N[f'{ds}_{v}_s1'][key]
            m = (a + b) / 2
            cells += [f2(a), f2(b), f2(m) + ('' if v == 'FedGDBD-S' else f' ({sg(m - ctrl[ds])})')]
        rows.append(' & '.join(cells) + r' \\')
    cmd(name, r'''\begin{tabular}{lrrrrrr}
\toprule
 & \multicolumn{3}{c}{CIFAR-10} & \multicolumn{3}{c}{CIFAR-100} \\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}
Run & Seed 0 & Seed 1 & Mean (gap) & Seed 0 & Seed 1 & Mean (gap) \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')


nov_table('best', 'TabNovBest')
nov_table('last', 'TabNovLast')

# per-seed gaps (for the text)
gaps = {}
for ds in ['Cifar10', 'Cifar100']:
    for v in ['FedGDBD-AGC', 'FedGDBD-AGS']:
        gaps[f'{ds}_{v}'] = [N[f'{ds}_{v}_s{s}']['best'] - N[f'{ds}_FedGDBD-S_s{s}']['best'] for s in (0, 1)]

# ---- novelty: per architecture, every run ----
rows = []
for ds in ['Cifar10', 'Cifar100']:
    lab = 'CIFAR-10' if ds == 'Cifar10' else 'CIFAR-100'
    first = True
    for s in (0, 1):
        for v in ['FedGDBD-S', 'FedGDBD-AGC', 'FedGDBD-AGS']:
            r = N[f'{ds}_{v}_s{s}']
            rows.append(f"{lab if first else ''} & {s} & {VNAME[v]} & {r['best_round']} & " + ' & '.join(f'{x:.1f}' for x in r['per_best']) + r' \\')
            first = False
    if ds == 'Cifar10':
        rows.append('\\midrule')
cmd('TabNovArch', r'''\begin{tabular}{llllrrrr}
\toprule
Dataset & Seed & Run & Best rd. & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')

# ---- gate statistics ----
rows = []
for ds in ['Cifar10', 'Cifar100']:
    lab = 'CIFAR-10' if ds == 'Cifar10' else 'CIFAR-100'
    for key, what, v in [('g_acc_mean', 'AGC: $g$ correct, mean over rounds', 'FedGDBD-AGC'),
                         ('g_acc_r0', 'AGC: $g$ correct, round 0', 'FedGDBD-AGC'),
                         ('kept_mean', 'AGS: share distilled, mean over rounds', 'FedGDBD-AGS'),
                         ('kept_r0', 'AGS: share distilled, round 0', 'FedGDBD-AGS')]:
        a, b = N[f'{ds}_{v}_s0'][key], N[f'{ds}_{v}_s1'][key]
        rows.append(f"{lab if key == 'g_acc_mean' else ''} & {what} & " + ' & '.join(f'{x:.2f} / {y:.2f}' for x, y in zip(a, b)) + r' \\')
    if ds == 'Cifar10':
        rows.append('\\midrule')
cmd('TabGate', r'''\begin{tabular}{llrrrr}
\toprule
Dataset & Statistic (seed 0 / seed 1) & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')

# ---- per-architecture gains ----
rows = []
for ds in ['Cifar10', 'Cifar100']:
    lab = 'CIFAR-10' if ds == 'Cifar10' else 'CIFAR-100'
    for v in ['FedGDBD-AGC', 'FedGDBD-AGS']:
        g = D['arch_gains'][f'{ds}_{v}']
        rows.append(f"{lab if v == 'FedGDBD-AGC' else ''} & {VNAME[v]} & " + ' & '.join(sg(x) for x in g) + r' \\')
cmd('TabArchGain', r'''\begin{tabular}{llrrrr}
\toprule
Dataset & Run & CNN & GoogLeNet & MobileNetV2 & ResNet18 \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n')

open(os.path.join(ROOT, 'report', 'tables.tex'), 'w').write('% generated by analysis/report_tables.py\n' + '\n'.join(out))
print('per-seed gaps (best):', {k: [round(x, 2) for x in v] for k, v in gaps.items()})
ctrl_diff = {ds: abs(N[f'{ds}_FedGDBD-S_s0']['best'] - N[f'{ds}_FedGDBD-S_s1']['best']) for ds in ['Cifar10', 'Cifar100']}
print('control seed difference:', {k: round(v, 2) for k, v in ctrl_diff.items()})
print('wrote report/tables.tex')


# ---- appendix: per-client accuracy at the best round, reproduction runs ----
def client_table(ds, name):
    rows = []
    ms = ['FedProto', 'LG-FedAvg', 'FedGDBD', 'FedGDBD-S']
    for c in range(20):
        rows.append(f"{c} & {ARCH[c % 4]} & " + ' & '.join(f"{R[f'{ds}_{m}']['clients_best'][c]:.1f}" for m in ms) + r' \\')
    head = ' & '.join(NAME[m] for m in ms)
    return r'''\begin{tabular}{rlrrrr}
\toprule
Client & Model & ''' + head + r''' \\
\midrule
''' + '\n'.join(rows) + '\n\\bottomrule\n\\end{tabular}\n'


extra = []
for ds, name in [('Cifar10', 'TabClientsTen'), ('Cifar100', 'TabClientsHundred')]:
    extra.append(f'\\newcommand{{\\{name}}}{{%\n{client_table(ds, name)}}}\n')
with open(os.path.join(ROOT, 'report', 'tables.tex'), 'a') as fh:
    fh.write('\n'.join(extra))
print('appended client tables')
