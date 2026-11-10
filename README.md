# Fed-GDBD for Heterogeneous Federated Learning: a reproduction

An independent re-implementation and partial reproduction of

> K. Zhang, J. Wang, W. Wang, T. Zeng, P. Li, X. Wang, T. Zhang. **Federated learning with heterogeneous data and models based on global decision boundary distillation.** *Journal of King Saud University – Computer and Information Sciences* 37, 75 (2025). [doi:10.1007/s44443-025-00097-0](https://doi.org/10.1007/s44443-025-00097-0)

The authors did not release code. Fed-GDBD is written from the paper's equations on top of [HtFLlib](https://github.com/TsingZ0/HtFLlib) (Apache-2.0), whose heterogeneous-model setup, Dirichlet partitioning and baselines match the paper's experiments.

**TL;DR:** 20 clients, 4 different model architectures, no raw data or feature-extractor weights shared: each client distils a single server-side decision boundary into its model once per round (FedGDBD-S: into its classifier head only). See [Architecture](#architecture) for the diagram.

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

   It shows no downward trend over 50 rounds (from round 3 on it stays within 0.53 pt of its best on CIFAR-10 and 1.1 pt on CIFAR-100) and restores the collapsed clients (CIFAR-100 CNN: 3.9 → 45.6 %). It adds no communication.

## Novelty: agreement-gated distillation (4 seeds)

**Idea.** In FedGDBD-S every client distils the global learner *g* with the same weight α = 0.7, even where *g* reads that client's features badly. Agreement gating lets *g* influence a client only as much as it has earned on that client's own data. Both variants sit on top of FedGDBD-S:

- **FedGDBD-AGC (per client):** α_i = 0.7 × (accuracy of *g* on client *i*'s training features), measured each round before distillation.
- **FedGDBD-AGS (per image):** distil only on images where *g*'s top class is correct; the rest get cross-entropy only.

All runs below pick the IKD teacher on a 10 % validation slice of each client's training data (`--gdbd_teacher val`), train on the remaining 90 % and run 20 rounds, so compare them **only with each other**, not with the 50-round results above. Seeds 0 to 3 (`--seed N`: model initialisation, client order and k-means seeding; same data split). The paper runs 100 rounds and averages 3 runs; we ran 20 rounds per seed because of compute.

**Matched-α control.** AGC lowers the average distillation weight, so a gain could come just from a lower α. The control runs FedGDBD-S with one α for every client equal to the mean α_i that AGC used in seeds 0 and 1: 0.58 (CIFAR-10) and 0.49 (CIFAR-100).

**Fixed in advance.** After seeds 0 and 1, and before seeds 2 and 3 and the matched-α runs, we committed [PROTOCOL.md](PROTOCOL.md): the seeds, the matched α values, three hypotheses and the tests. The success bar from before the first runs stays: ≥ +0.5 pt over the control on **both** datasets.

**Best-round test accuracy, %, mean ± SD over seeds 0 to 3:**

| Method | CIFAR-10 | CIFAR-100 |
|---|---|---|
| FedGDBD-S (control) | 86.82 ± 0.10 | 42.09 ± 0.18 |
| Matched α | 86.89 ± 0.34 | 42.32 ± 0.28 |
| FedGDBD-AGC | 87.02 ± 0.11 | **42.47 ± 0.47** |
| FedGDBD-AGS | **87.11 ± 0.22** | 41.96 ± 0.28 |

- AGC has higher mean accuracy than the control on both datasets, and AGS on CIFAR-10. AGC and AGS both have higher mean accuracy than the matched-α control on CIFAR-10; on CIFAR-100 only AGC does.
- The gaps are small (0.2 to 0.4 pt) and smaller than the spread across seeds.
- Paired tests fixed in advance (one-sided): **H3** AGS > control on CIFAR-10: +0.29 pt, p = 0.034 (Holm-adjusted for 3 hypotheses: 0.10). **H1** AGC > control on CIFAR-100: +0.37 pt, p = 0.077; per seed +0.86, +0.52, +0.09, +0.02. **H2** AGC > matched α on CIFAR-100: +0.15 pt, p = 0.31, not supported.
- On CIFAR-100 the matched-α control alone is +0.22 pt above the control (descriptive, not a protocol test), so much of AGC's gain there comes from a lower α.
- Neither gate meets the +0.5 pt bar on both datasets.

Full output: `experiments/novelty/multiseed_summary_seeds0-3.txt` (all seeds) and `..._seeds2-3.txt` (new seeds only).

**What the gate found.** Accuracy of *g* on each architecture's own training features (AGC, mean over rounds and seeds 0 to 3):

| | CNN | GoogLeNet | MobileNetV2 | ResNet18 |
|---|---|---|---|---|
| CIFAR-10 | 0.96 | 0.90 | **0.53** | 0.93 |
| CIFAR-100 | 0.76 | 0.80 | **0.43** | 0.80 |

Without being told about architectures, the gate singles out MobileNetV2 as the one *g* misreads, in every run of every seed.

Logs and `.h5` curves: `experiments/novelty/run1_seed0/` to `run4_seed3/`. Tests: `python analysis/multiseed_summary.py`. Paper figures and tables: `python analysis/paper_figures.py`. Launch: `run_novelty_cifar10_seed<N>.bat` / `run_novelty_cifar100_seed<N>.bat` and `run_amatch.bat Cifar10|Cifar100`. Seed 4 is running and will be added.

## Architecture

One communication round, with our novelty in step 4. Clients never share raw data or feature-extractor weights: they upload their classifier head once (round 0, to initialise `g`) and class prototypes every round, and the server sends back only `g`, one linear layer. Steps 0 and 3a run once, before the first round.

```mermaid
flowchart TB
    subgraph C["Each client i  (20 clients, Dir β = 0.1, model = arch i mod 4)"]
        direction LR
        P0["0 · Pre-train<br/>5 epochs cross-entropy<br/><i>round 0 only</i>"]
        L["1 · Local training<br/>CE + T²·IKD<br/>teacher = best past self"]
        K["2 · Prototypes<br/>k-means++ on features z<br/>v = 5 per class"]
        P0 --> L --> K
    end

    subgraph S["Server"]
        direction LR
        G0["3a · Init g  (Eq. 5)<br/>sample-weighted avg of heads<br/><i>round 0 only</i>"]
        G["3b · Train g  (Eq. 12)<br/>CE on all clients' prototypes<br/>one linear layer 512 → C"]
        G0 --> G
    end

    subgraph U["4 · Global distillation update on client i  (Eq. 13)"]
        direction LR
        FIX["FedGDBD-S fix<br/>logit-scale matching + head-only KD"]
        GATE{"Gate: does g agree<br/>with the label?"}
        AGC["AGC · per client<br/>α_i = α · acc_i(g)"]
        AGS["AGS · per image<br/>distil only if argmax g(z) = y"]
        LOSS["(1 − a)·CE + a·T²·KL(g ‖ h)<br/>a = α_i (AGC) or α·w (AGS)"]
        FIX --> GATE
        GATE --> AGC --> LOSS
        GATE --> AGS --> LOSS
    end

    E[("5 · Evaluate<br/>test accuracy per client<br/>best model → next IKD teacher<br/><i>then the next round starts at 1</i>")]

    K -- "prototypes ↑<br/>(no data, no weights)" --> G
    G -- "g ↓" --> FIX
    LOSS --> E

    classDef base fill:#ffffff,stroke:#6E7377,color:#26292B
    classDef server fill:#F1F2F0,stroke:#6E7377,color:#26292B
    classDef novel fill:#ffffff,stroke:#B8892B,stroke-width:2px,color:#26292B
    classDef agc fill:#ffffff,stroke:#6250D6,stroke-width:2px,color:#26292B
    class P0,L,K,E,LOSS,FIX base
    class G0,G server
    class GATE,AGS novel
    class AGC agc
    style C fill:#F8F8F7,stroke:#AEB3B6,color:#26292B
    style S fill:#F8F8F7,stroke:#AEB3B6,color:#26292B
    style U fill:#F8F8F7,stroke:#B8892B,stroke-dasharray:4 3,color:#26292B
```

- **Fed-GDBD (paper):** step 4 is the plain loss with a fixed α = 0.7, distilling into the whole model.
- **FedGDBD-S (our fix during reproduction):** adds logit-scale matching and head-only distillation. It keeps Eq. 13 stable.
- **AGC / AGS (our novelty):** on top of FedGDBD-S, a gate checks whether `g` classifies the client's own features correctly. AGC scales α per client by g's accuracy on that client; AGS distils only the images where g's top class equals the label.

## Repository layout

```
system/flcore/clients/clientgdbd.py   Fed-GDBD client (IKD, k-means++ prototypes, GDBD update, FedGDBD-S)
system/flcore/servers/servergdbd.py   Fed-GDBD server (g init by Eq. 5, training by Eq. 12)
system/main.py                        HtFLlib entry point, + FedGDBD / FedGDBD-S and --gdbd_* flags
dataset/generate_Cifar10.py, ..100    Dirichlet split from PFLlib (data itself is NOT in the repo)
experiments/cifar10|cifar100/logs     full per-round, per-client logs of every run
experiments/cifar10|cifar100/results  HtFLlib .h5 accuracy curves
experiments/novelty/run<k>_seed<s>/   novelty runs (control, AGC, AGS, matched α), seeds 0 to 3, both datasets
analysis/summarize_logs.py            parses logs → best/last accuracy, per-architecture curves (JSON)
analysis/novelty_summary.py           novelty runs of one seed → best/last, per-architecture accuracy, gate statistics
analysis/multiseed_summary.py         all seeds → mean ± SD and the paired tests fixed in PROTOCOL.md
analysis/paper_figures.py             every figure and results table of the paper, from the logs
PROTOCOL.md                           seeds, hypotheses and tests fixed before seeds 2 and 3
paper/                                IEEE paper draft (LaTeX source, figures, PDF)
report/                               course project report (LaTeX source, figures, PDF and Word)
REPRODUCTION.md                       step-by-step guide to reproduce every result
presentation/                         final slides (.pptx) and the pptxgenjs script that builds them
*.bat, progress.py                    Windows setup / launch / progress-monitor scripts
```

## How to run (Windows)

For a full step-by-step guide to every run (data download, expected numbers, run times, troubleshooting), see **[REPRODUCTION.md](REPRODUCTION.md)**. To view our results without training, run `python progress.py experiments\cifar10\logs`.


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
