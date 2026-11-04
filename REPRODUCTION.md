# Reproducing our results, step by step

This guide rebuilds every number in the README and the final presentation:

- **Part A, reproduction (mid-evaluation):** FedProto, LG-FedAvg, Fed-GDBD (faithful) and FedGDBD-S, 50 rounds, 1 run.
- **Part B, novelty:** FedGDBD-S (control), FedGDBD-AGC and FedGDBD-AGS, 20 rounds, seeds 0 and 1.

If you only want to **see** our results without training anything, jump to [Step 0](#step-0-see-our-results-without-training-1-minute).

Everything below was run on Windows 11 laptops: an RTX 3050 6 GB (CIFAR-10) and an RTX 5060 8 GB (CIFAR-100), with three runs sharing one GPU. Linux and macOS commands are given at the end of each step.

---

## Step 0: see our results without training (1 minute)

The full logs of every run are in `experiments/`. Two scripts read them and need only plain Python (no PyTorch, no GPU).

```bat
cd Fed-GDBD-for-HtFL

:: reproduction (mid-evaluation) results
python progress.py experiments\cifar10\logs
python progress.py experiments\cifar100\logs

:: novelty results: best/last accuracy, per-architecture accuracy, gate statistics
python analysis\novelty_summary.py experiments\novelty\run1_seed0\cifar10\logs
python analysis\novelty_summary.py experiments\novelty\run2_seed1\cifar10\logs
python analysis\novelty_summary.py experiments\novelty\run1_seed0\cifar100\logs
python analysis\novelty_summary.py experiments\novelty\run2_seed1\cifar100\logs
```

The first command prints, for example:

```
Dataset   Method         Round   Best%   Last%  Paper%  min/rnd  Status
Cifar10   FedGDBD-S    51/51     87.10   87.06   87.90     10.4  FINISHED
Cifar10   FedGDBD       9/51     85.70   75.47   87.90     16.1  STOPPED (no update for 45+ min)
Cifar10   FedProto     51/51     82.52   82.31   82.75      9.6  FINISHED
Cifar10   LG-FedAvg    51/51     86.36   86.36   86.64      7.2  FINISHED
```

`Round 51/51` counts round 0 (the evaluation after pre-training) plus 50 training rounds. The faithful Fed-GDBD was stopped after its collapse, which is why it shows `STOPPED`.

---

## Step 1: requirements

| What | Version we used |
|---|---|
| Windows 10/11 with an NVIDIA GPU | RTX 3050 6 GB, RTX 5060 8 GB |
| NVIDIA driver | recent enough for CUDA 12.8 (check with `nvidia-smi`) |
| Python | 3.13 and 3.14 (64-bit, "Add to PATH" ticked) |
| Free disk space | about 6 GB (PyTorch ~3 GB, data ~1 GB) |

```bat
git clone https://github.com/md25052007/Fed-GDBD-for-HtFL.git
cd Fed-GDBD-for-HtFL
setup.bat
```

`setup.bat` creates `.venv`, installs PyTorch with CUDA (cu128 build, falling back to cu130) and `requirements.txt`, then prints a GPU check. You should see:

```
CUDA available: True
GPU: NVIDIA GeForce RTX ...
```

**Linux / macOS:**

```bash
python -m venv .venv && source .venv/bin/activate
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

---

## Step 2: get the data

The launchers download CIFAR automatically through torchvision. If the download stalls (it did for us), download the archives yourself and drop them in place; the generator will find and use them.

| Dataset | File | Put it in |
|---|---|---|
| CIFAR-10 | [cifar-10-python.tar.gz](https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz) (~163 MB) | `dataset\Cifar10\rawdata\` |
| CIFAR-100 | [cifar-100-python.tar.gz](https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz) (~161 MB) | `dataset\Cifar100\rawdata\` |

Create the `rawdata` folders if they do not exist. If you get CIFAR-100 from Kaggle instead, use a copy of the **original Python version** (the files `train`, `test` and `meta`) and place them in `dataset\Cifar100\rawdata\cifar-100-python\`.

The data is never committed to the repo (`.gitignore`).

---

## Step 3: build the federated split

The launchers do this for you. To do it by hand:

```bat
call .venv\Scripts\activate.bat
cd dataset
python generate_Cifar10.py noniid - dir
python generate_Cifar100.py noniid - dir
cd ..
```

This merges each dataset's train and test images, splits them over **20 clients** with a **Dirichlet(β = 0.1)** label distribution, and then splits each client's data **75 / 25** into train and test. The split uses a fixed seed (`np.random.seed(1)`), so everyone gets the same clients. It prints per-client class counts and writes `dataset\Cifar10\config.json`, `train\` and `test\`. Running it again does nothing if the split already exists.

---

## Step 4 (Part A): reproduction runs, 50 rounds

These are the results presented at the mid-evaluation and in the README's main table.

```bat
:: CIFAR-10: starts Fed-GDBD (faithful), FedProto and LG-FedAvg in parallel
run_cifar10.bat
:: then the stabilised FedGDBD-S (can run at the same time if memory allows)
start_fedgdbd_s_cifar10.bat

:: CIFAR-100: same pattern
run_cifar100.bat
start_fedgdbd_s_cifar100.bat
```

Each run opens in its own minimised window. Do not close them, and keep the laptop plugged in and awake. Logs go to `logs\<Dataset>_<Method>.log`. Check progress at any time:

```bat
check_progress.bat
```

What each run executes (from `system\`):

```bat
python -u main.py -data Cifar10 -ncl 10 -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 50 -t 1 -go practical -did 0 -algo FedGDBD-S
```

| Flag | Meaning |
|---|---|
| `-data Cifar10 -ncl 10` | dataset and number of classes (`Cifar100 -ncl 100`) |
| `-m HtFE-img-4` | the four heterogeneous models: client i gets [CNN, GoogLeNet, MobileNetV2, ResNet18][i mod 4] |
| `-fd 512` | feature dimension before the head |
| `-nc 20 -jr 1` | 20 clients, all join every round |
| `-lbs 10 -lr 0.01 -ls 5` | batch 10, SGD lr 0.01, 5 local epochs |
| `-gr 50` | 50 global rounds |
| `-algo` | `FedGDBD`, `FedGDBD-S`, `FedProto` (add `-lam 10`), `LG-FedAvg` |

Fed-GDBD hyper-parameters default to the paper's (Sec. 5.1): `--gdbd_v 5 --gdbd_alpha 0.7 --gdbd_T 20 --gdbd_cluster_rounds 100 --gdbd_update_epochs 5 --gdbd_server_epochs 5 --gdbd_pretrain_epochs 5`.

**Expected results (best round, %):**

| Method | CIFAR-10 | CIFAR-100 | Time per round (3 runs on one GPU) |
|---|---|---|---|
| FedProto | 82.52 | 39.51 | 8–10 min |
| LG-FedAvg | 86.36 | 42.79 | 5–7 min |
| Fed-GDBD, faithful | 85.70 (round 1) | 40.70 (round 2) | 13–16 min |
| FedGDBD-S | 87.10 | 43.74 | ~10 min |

A 50-round run therefore takes about 5 to 9 hours. The **faithful Fed-GDBD collapses** after round 1–2 (accuracy drops to about 75 % on CIFAR-10 and 28 % on CIFAR-100). We stopped it after 9–10 rounds; you can close its window once the drop is clear.

---

## Step 5 (Part B): novelty runs, 20 rounds × 2 seeds

```bat
:: seed 0
run_novelty_cifar10.bat
run_novelty_cifar100.bat
:: seed 1
run_novelty_cifar10_seed1.bat
run_novelty_cifar100_seed1.bat
```

Each launcher starts three runs in parallel: FedGDBD-S (control), FedGDBD-AGC and FedGDBD-AGS. Logs go to `logs_novelty\` (seed 0) or `logs_novelty_seed1\` (seed 1). Check progress with `check_novelty.bat` or `check_novelty_seed1.bat`.

What each run executes:

```bat
python -u main.py -data Cifar100 -ncl 100 -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 20 -t 1 -go novelty_seed1 -did 0 --gdbd_teacher val --seed 1 -algo FedGDBD-AGC
```

The two flags that differ from Part A:

- `--gdbd_teacher val`: the IKD teacher (the client's best past model) is chosen on a 10 % validation slice of the client's training data instead of its test data, so no test data influences training. These runs therefore train on 90 % of the training data, and their numbers are compared **only with each other**, not with Part A.
- `--seed N`: seeds the model initialisation, the client order and k-means. The data split stays the same.

**Expected results (best round, %):**

| Run | CIFAR-10 seed 0 | CIFAR-10 seed 1 | CIFAR-100 seed 0 | CIFAR-100 seed 1 |
|---|---|---|---|---|
| FedGDBD-S (control) | 86.96 | 86.73 | 42.07 | 42.26 |
| FedGDBD-AGC | 86.92 | 87.18 | 42.93 | 42.78 |
| FedGDBD-AGS | 87.36 | 87.10 | 42.24 | 42.12 |

Each round takes 14–18 minutes with three runs on one GPU, plus about 7 minutes of pre-training, so one launcher finishes in about 5 to 6.5 hours.

Then summarise:

```bat
python analysis\novelty_summary.py logs_novelty_seed1
```

---

## Step 6: check your results

1. Run `python progress.py <log folder>` or `python analysis\novelty_summary.py <log folder>` (Step 0) on your own log folder.
2. Compare with the expected tables above. Expect close but not identical numbers: GPU kernels are not bit-for-bit deterministic, and the Part A runs were made before the client order was seeded. Between our two seeds the control moved by about 0.2 pt.
3. The HtFLlib accuracy curves are saved as `.h5` files in `results\` (copies of ours are in `experiments\...\results\`).

Each log contains, per round: every client's test accuracy and AUC, the sample-weighted average (`Averaged Test Accuracy`), the standard deviation, and for AGC / AGS one gate line per client (`Gate client i: g_acc=… alpha=…` or `Gate sample i: kept=…`). The end of a log shows `Best accuracy.` followed by the number we report.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| CIFAR download stalls or fails | Download the `.tar.gz` yourself (Step 2) and place it in `rawdata\`. |
| `CUDA available: False` | Update the NVIDIA driver, then rerun `setup.bat`. A very new GPU may need the cu130 build, which `setup.bat` tries automatically. |
| `CUDA out of memory` | Run fewer methods at once: start one launcher, or edit it to start one run. A 6 GB GPU fits three CIFAR runs. |
| A window closes immediately | Open the log in `logs\` and read its last lines; usually `.venv` is missing (run `setup.bat`) or the split was not built. |
| `Run setup.bat first` | The launcher could not find `.venv`; run `setup.bat` from the repo folder. |
| A run stops progressing | `check_progress.bat` marks a run `STOPPED` after 45 minutes without a new round. Keep the laptop awake and plugged in (Windows power settings: never sleep). |
| The faithful Fed-GDBD accuracy drops | Expected: this is the Eq. 13 instability we report. Use FedGDBD-S. |

---

## Where our own runs are

| Folder | Contents |
|---|---|
| `experiments/cifar10/logs`, `experiments/cifar100/logs` | Part A logs (50 rounds; faithful Fed-GDBD 9–10 rounds) |
| `experiments/cifar10/results`, `experiments/cifar100/results` | Part A `.h5` accuracy curves |
| `experiments/novelty/run1_seed0/` | Part B, seed 0, both datasets, logs + `.h5` |
| `experiments/novelty/run2_seed1/` | Part B, seed 1, both datasets, logs + `.h5` |
| `experiments/*/logs/old/` | the earlier run with our IKD masking bug (diverged on CIFAR-100) |
