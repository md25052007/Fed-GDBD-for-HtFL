# Progress Log

This file tracks how the repository was built, one entry per commit, in order.
It's a build/development log, not a lab notebook — for the actual experimental
findings (bugs found, results vs. the paper), see `README.md`.

---

### 1 — Initial scaffolding

- Added `.gitignore`, `LICENSE` (Apache-2.0, inherited from HtFLlib), `requirements.txt`, `setup.bat`.
- Added `README.md`: paper reference, results table, what we found (IKD bug, Eq. 13 instability, the FedGDBD-S fix), repo layout, and how to run.
- Started this file.

### 2 — Dataset preparation utilities

- Added `dataset/generate_Cifar10.py` and `generate_Cifar100.py` (Dirichlet / pathological partitioning, adapted from PFLlib) and `dataset/utils/dataset_utils.py`.
- Raw/generated data itself stays out of the repo (`.gitignore`); these scripts build the per-client splits locally before a run.

### 3 — HtFLlib core framework

- Added `system/main.py` (entry point, CLI flags, algorithm dispatch), `system/utils/*` (data loading, memory profiling, result aggregation), `system/clean_temp_files.py` and `system/get_mean_std.py` (small housekeeping/analysis helpers), `system/flcore/clients/clientbase.py` and `system/flcore/servers/serverbase.py` (shared client/server loop), and `system/flcore/trainmodel/*` (the heterogeneous architectures: 4-layer CNN, GoogLeNet-style, MobileNetV2, ResNet18, plus AlexNet/BiLSTM/Transformer kept from HtFLlib).
- This is the shared harness every algorithm below (including Fed-GDBD) builds on.

### 4 — Baseline FL methods

- Added the client/server pairs for the heterogeneous-FL baselines evaluated against Fed-GDBD and kept from HtFLlib: FedProto, LG-FedAvg, FedGH, FedKD, FedTGP, FedGen, FedFD, FedFML, FedMRL, FedKTL, FedL2G (feature and logit variants), and FedLocal.
- Only FedProto and LG-FedAvg are actually run and reported in this reproduction (see README's "reproduction scope" table); the others ship with HtFLlib and are kept for completeness / future comparison.

### 5 — Fed-GDBD reproduction (+ FedGDBD-S)

- Added `system/flcore/clients/clientgdbd.py` and `servers/servergdbd.py`: the paper's method from scratch — local pre-training, k-means++ multi-prototype clustering, the global decision-boundary learner `g` (server init by Eq. 5, training by Eq. 12), irrelevant-class KD (Eq. 9–10), and the GDBD distillation step (Eq. 13).
- Also includes **FedGDBD-S**, our stabilised variant, in the same files (selected via `-algo FedGDBD-S`): per-sample logit-scale matching of `g` to the student, and distilling into the head only instead of the full network. Both the faithful-to-Eq.13 path and the stabilised path are implemented here — see README § "What we found" for why the literal equation needed the fix.

### 6 — Experiment orchestration scripts

- Added the Windows launch/monitoring scripts: `run_cifar10.bat`, `run_cifar100.bat`, `run_experiments.bat`, `run_fedgdbd_only.bat`, `run_fedgdbd_s.bat`, `start_fedgdbd_s_cifar10.bat`, `start_fedgdbd_s_cifar100.bat`, `restart_fedgdbd_cifar10.bat`, `restart_fedgdbd_cifar100.bat`, `check_progress.bat`, and `progress.py` (parses live logs for rounds done / best accuracy / ETA while a run is still in progress).

### 7 — CIFAR-10 experiments: logs + results

- Added `experiments/cifar10/logs/` (full per-round, per-client logs for FedGDBD, FedGDBD-S, FedProto, LG-FedAvg, plus the earlier buggy-IKD run kept under `logs/old/` for reference) and `experiments/cifar10/results/` (HtFLlib `.h5` accuracy curves).
- Run on an RTX 3050 6 GB laptop, practical Dir(0.1), 20 clients, 50 rounds.

### 8 — CIFAR-100 experiments: logs + results

- Same as above for CIFAR-100, run on an RTX 5060 8 GB laptop.

### 9 — Results analysis

- Added `analysis/summarize_logs.py` and its output (`summary_cifar10.json`, `summary_cifar100.json`): parses the raw logs into best/last accuracy and per-architecture breakdowns, which feed the README results table and the final slides.

### 10 — Final presentation deck

- Added `presentation/Fed-GDBD_Final_Presentation.pptx` and `presentation/build_deck.js` (the pptxgenjs script that generates it) — the final results deck for the course submission.
