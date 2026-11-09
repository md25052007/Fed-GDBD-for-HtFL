# Protocol for the multi-seed extension runs

This file fixes how the extra runs for the paper are done and analysed. It is committed before any of these runs start, so the git history shows that none of it was changed after seeing results.

## Where we start from

We already have two seeds (0 and 1) of the control (FedGDBD-S), AGC and AGS on CIFAR-10 and CIFAR-100, 20 rounds each. We have seen those results:

| Gap to control, best round (pt) | CIFAR-10 | CIFAR-100 |
|---|---|---|
| AGC | -0.04, +0.45 | +0.86, +0.52 |
| AGS | +0.40, +0.37 | +0.17, -0.14 |

The hypotheses below come from these two seeds. They are therefore exploratory, and seeds 2 and 3 are the real test.

## Hypotheses

- **H1.** AGC beats the control on CIFAR-100.
- **H2.** AGC beats the matched-alpha control on CIFAR-100, so the gain comes from giving different clients different weights and not only from a lower average alpha.
- **H3.** AGS beats the control on CIFAR-10.

All other method and dataset pairs are reported as well; they are not hypotheses.

## The new control: matched alpha

FedGDBD-S with one fixed alpha for every client, equal to the average alpha that AGC actually used. It is the mean of the per-client alpha (0.7 x accuracy of g on the client's training features) over all 20 clients and all 21 rounds (0 to 20), pooled over the seed 0 and seed 1 AGC logs (`python analysis/alpha_matched.py`):

| | pooled mean | alpha used |
|---|---|---|
| CIFAR-10 | 0.5795 | **0.58** |
| CIFAR-100 | 0.4865 | **0.49** |

These two values are final and are not tuned further.

## Runs

| Seeds | Control | AGC | AGS | Matched alpha |
|---|---|---|---|---|
| 0, 1 | done | done | done | new |
| 2, 3 | new | new | new | new |
| 4 | optional | optional | optional | optional |

Everything else is exactly as in the existing extension runs: 20 clients, HtFE-img-4, Dirichlet 0.1 split (fixed), batch 10, lr 0.01, 5 local epochs, 20 rounds, T = 20, IKD teacher picked on the 10% validation slice, `--seed` controlling model initialisation, client order and k-means seeding.

**Seed 4.** Seed 4 is run only if there is time. The decision is made on time alone, before the analysis script is run on seeds 2 and 3, and the decision and its date are added to the bottom of this file. If seed 4 is run, all of its runs are reported and included in the main analysis, whatever they show.

**Crashes.** A run that crashes is rerun with the same command and seed. The rerun replaces it, and the crash is mentioned in the paper. No run is dropped for any other reason.

## Analysis

All numbers come from `python analysis/multiseed_summary.py`, which reads the logs in `experiments/novelty/`.

- **Metric:** HtFLlib's averaged test accuracy at the best round (as in the paper). Last-round accuracy (round 20) is reported next to it.
- **Per method:** mean and standard deviation over seeds.
- **Per comparison** (AGC vs control, AGC vs matched alpha, AGS vs control), paired by seed:
  - the gap for every seed;
  - the mean gap with its 95% confidence interval (t distribution);
  - a paired t-test, one-sided for H1 to H3 and two-sided for everything else;
  - the number of seeds in which the first method wins.
- **Main analysis:** all seeds run (0 to 3, or 0 to 4).
- **Out-of-sample check:** the same tests on the new seeds only (`--seeds 2 3`, or `--seeds 2 3 4`), since seeds 0 and 1 were used to form the hypotheses.
- With 4 seeds a sign test cannot go below p = 0.0625, so the win count is reported as support only and not used as the test.
- The success criterion from the course report (a gate improves on the control by at least 0.5 pt on both datasets) stays as it was. We report against it and do not change it.

## Reading the results

| Outcome on CIFAR-100 | What we will claim |
|---|---|
| AGC > matched alpha and AGC > control | The per-client gate itself helps |
| AGC > control, matched alpha <= control | Lowering alpha for everyone does not help; the gain comes from gating |
| AGC about equal to matched alpha, both > control | The gain is mostly from a lower average alpha; the paper's alpha = 0.7 is too high for mixed architectures |
| AGC not above control | H1 is not supported; reported as such |

## Decision log

(Add the seed 4 decision here, with the date, before running the analysis on seeds 2 and 3.)
