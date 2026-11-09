"""Compute the matched alpha for the fixed-alpha control (see PROTOCOL.md).

alpha_matched = mean of the per-client alpha that FedGDBD-AGC actually used
(0.7 x accuracy of g on the client's own training features), over all 20 clients
and all rounds, pooled over the existing AGC runs of seeds 0 and 1.

Usage:  python analysis/alpha_matched.py
"""
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = ['run1_seed0', 'run2_seed1']

for ds, name in (('cifar10', 'Cifar10'), ('cifar100', 'Cifar100')):
    pooled = []
    for run in RUNS:
        path = os.path.join(HERE, 'experiments', 'novelty', run, ds, 'logs', f'{name}_FedGDBD-AGC.log')
        txt = open(path, encoding='utf-8', errors='ignore').read()
        a = [float(x) for x in re.findall(r'Gate client \d+: g_acc=[\d.]+ alpha=([\d.]+)', txt)]
        print(f'{name:9} {run}: {len(a)} values, mean alpha {st.mean(a):.4f}')
        pooled += a
    print(f'{name:9} pooled mean alpha = {st.mean(pooled):.4f}  ->  alpha_matched = {round(st.mean(pooled), 2):.2f}\n')
