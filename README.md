# Fed-GDBD for Heterogeneous Federated Learning: a reproduction

An independent re-implementation and partial reproduction of

> K. Zhang, J. Wang, W. Wang, T. Zeng, P. Li, X. Wang, T. Zhang. **Federated learning with heterogeneous data and models based on global decision boundary distillation.** *Journal of King Saud University – Computer and Information Sciences* 37, 75 (2025). [doi:10.1007/s44443-025-00097-0](https://doi.org/10.1007/s44443-025-00097-0)

The authors did not release code. Fed-GDBD is written from the paper's equations on top of [HtFLlib](https://github.com/TsingZ0/HtFLlib) (Apache-2.0), whose heterogeneous-model setup, Dirichlet partitioning and baselines match the paper's experiments.

IT307 Machine Learning project, NIT Karnataka.

## Results

Practical setting, Dir(β = 0.1), 20 clients, four heterogeneous models (4-layer CNN, GoogLeNet, MobileNetV2, ResNet18), 50 rounds, 1 seed. The metric is the mean of the 20 clients' local test accuracies at the best round, the paper's protocol.

| Method | CIFAR-10 (ours) | CIFAR-10 (paper) | CIFAR-100 (ours) | CIFAR-100 (paper) |
|---|---|---|---|---|
| FedProto | 82.52 | 82.75 | 39.51 | 35.38 |
| LG-FedAvg | 86.36 | 86.64 | 42.79 | 43.30 |
| Fed-GDBD, faithful to Eq. 13 \* | 85.70 | 87.90 | 40.70 | 45.09 |
| **FedGDBD-S (ours)** | **87.10** | 87.90 | **43.74** | 45.09 |

\* Best round before the collapse (round 1 on CIFAR-10, round 2 on CIFAR-100). These runs were stopped after 9–10 rounds.

- Both baselines land within 0.5 pt of the paper, except FedProto on CIFAR-100, which is 4.1 pt above it.
- FedGDBD-S is the best method in our runs: +0.74 / +0.95 pt over LG-FedAvg, and 0.80 / 1.35 pt below the paper's Fed-GDBD, with half the rounds and one seed.
- The faithful Fed-GDBD reaches its best accuracy within 1–2 rounds, then degrades for specific architectures (see below).

Hardware: CIFAR-10 on an RTX 3050 6 GB laptop, CIFAR-100 on an RTX 5060 8 GB laptop, with three runs sharing each GPU.

## What we found

1. **IKD masking bug (ours, fixed).** The first version removed the target class *after* a full softmax. That gives the target logit a positive gradient, so every step pushes the correct class down. On CIFAR-100 this diverged to NaN at round 8. The fix removes the target logit *before* the softmax (non-target KD, as in Zhao et al., 2022), which gives exactly zero gradient on the target class, as the paper's Eq. 10 requires. The logs of the buggy run are in `experiments/*/logs/old/`.
2. **Eq. 13 implemented literally is unstable.** Even with IKD fixed, specific architectures collapse after round 2:
   - CIFAR-100, 4-layer CNN clients: 48.0 → 3.9 %
   - CIFAR-10, ResNet18 clients: 78.7 → 53.3 %

   Our explanation: g is a single linear layer shared by four very different feature spaces. On some architectures its logits are far larger than the client head's, and the α·T² = 280 weight lets the distillation term swamp cross-entropy. This fits the per-client logs but is a hypothesis, not a proof.
3. **FedGDBD-S, our stabilised variant**, adds two changes to the distillation step (`update()` in `clientgdbd.py`):
   - rescale g's logits per sample to the student's logit standard deviation;
   - let the distillation term update only the head (`head(rep.detach())`); cross-entropy still trains the full model.

   It stays within ±0.5 pt of its best for all 50 rounds and restores the collapsed clients (CIFAR-100 CNN: 3.9 → 45.6 %). It adds no communication.

## Repository layout

```
system/flcore/clients/clientgdbd.py   Fed-GDBD client (IKD, k-means++ prototypes, GDBD update, FedGDBD-S)
system/flcore/servers/servergdbd.py   Fed-GDBD server (g init by Eq. 5, training by Eq. 12)
system/main.py                        HtFLlib entry point, + FedGDBD / FedGDBD-S and --gdbd_* flags
dataset/generate_Cifar10.py, ..100    Dirichlet split from PFLlib (data itself is NOT in the repo)
experiments/cifar10|cifar100/logs     full per-round, per-client logs of every run
experiments/cifar10|cifar100/results  HtFLlib .h5 accuracy curves
analysis/summarize_logs.py            parses logs → best/last accuracy, per-architecture curves (JSON)
presentation/                         final slides (.pptx) and the pptxgenjs script that builds them
*.bat, progress.py                    Windows setup / launch / progress-monitor scripts
```

## How to run (Windows)

1. `setup.bat`: creates `.venv` and installs PyTorch (CUDA 12.8 build) and the requirements.
2. `run_cifar10.bat` or `run_cifar100.bat`: downloads CIFAR, builds the 20-client Dir(0.1) split, and starts FedGDBD, FedProto and LG-FedAvg in parallel.
3. `start_fedgdbd_s_cifar10.bat` / `..._cifar100.bat`: runs the stabilised FedGDBD-S.
4. `check_progress.bat`: shows rounds done, best and last accuracy, and time left for every run.

On Linux or macOS, from `dataset/`, run `python generate_Cifar10.py noniid - dir`. Then from `system/`:

```bash
python main.py -data Cifar10 -ncl 10 -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 50 -go practical -algo FedGDBD-S
```

`-algo` can be `FedGDBD`, `FedGDBD-S`, `FedProto` (add `-lam 10`) or `LG-FedAvg`. The Fed-GDBD defaults follow the paper (Sec. 5.1): `--gdbd_v 5 --gdbd_alpha 0.7 --gdbd_T 20 --gdbd_cluster_rounds 100`, with 5 update and 5 server epochs.

## Reproduction scope vs the paper

| | Paper | Here |
|---|---|---|
| Methods | Fed-GDBD, FedProto, FedTGP, LG-FedAvg, FedGH | Fed-GDBD, FedProto, LG-FedAvg (+ FedGDBD-S) |
| Datasets | CIFAR-10, CIFAR-100, Tiny-ImageNet, Flowers102 | CIFAR-10, CIFAR-100 |
| Settings | practical + pathological | practical only |
| Rounds × seeds | 100 × 3 | 50 × 1 |
| Ablations / sweeps | yes | no |

**Assumptions** (details the paper leaves out):

- 5 epochs of cross-entropy pre-training before round 0.
- The IKD teacher is the client's past model with the best test accuracy.
- g is a frozen teacher during distillation.
- g is trained with SGD (lr 0.01, batch 10, 5 epochs) on the current round's prototypes, warm-started from the previous round.
- FedProto uses λ = 10 (HtFLlib default).

## License and credits

The base code is HtFLlib by Jianqing Zhang et al., under the Apache License 2.0 (see `LICENSE`), with CIFAR generators from PFLlib. The Fed-GDBD / FedGDBD-S implementation, scripts, logs and slides were added for this project.
