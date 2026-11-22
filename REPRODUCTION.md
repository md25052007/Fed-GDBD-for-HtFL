# Reproducing our results, step by step

This guide rebuilds every number in the README, the paper and the final presentation:

- **Part A, reproduction (mid-evaluation):** FedProto, LG-FedAvg, Fed-GDBD (faithful) and FedGDBD-S, 50 rounds, 1 run.
- **Part B, novelty:** FedGDBD-S (control), FedGDBD-AGC, FedGDBD-AGS and the matched-α control, 20 rounds, seeds 0 to 4, with the analysis fixed in [PROTOCOL.md](PROTOCOL.md).

If you only want to **see** our results without training anything, jump to [Step 0](#step-0-see-our-results-without-training-1-minute).

Everything below was run on Windows laptops: an RTX 3050 6 GB (CIFAR-10) and an RTX 5060 8 GB (CIFAR-100), with three runs sharing one GPU. All commands are run from the repo folder; in PowerShell, start a script name with `.\` (for example `.\scripts\run_novelty.bat Cifar10 0`). On Linux or macOS, set up as in Step 1 and run the `python` commands shown under "What each run executes" from the `system/` folder.

---

## Step 0: see our results without training (1 minute)

The full logs of every run are in `experiments/`. These scripts read them and need only plain Python (no PyTorch, no GPU; the figures need matplotlib).

```bat
cd Fed-GDBD-for-HtFL

:: reproduction (mid-evaluation) results
python scripts\progress.py experiments\cifar10\logs
python scripts\progress.py experiments\cifar100\logs

:: novelty results: best/last accuracy, per-architecture accuracy, gate statistics
python analysis\novelty_summary.py experiments\novelty\run1_seed0\cifar10\logs
python analysis\novelty_summary.py experiments\novelty\run2_seed1\cifar10\logs
python analysis\novelty_summary.py experiments\novelty\run1_seed0\cifar100\logs
python analysis\novelty_summary.py experiments\novelty\run2_seed1\cifar100\logs

:: all seeds: mean ± SD and the paired tests of PROTOCOL.md
python analysis\multiseed_summary.py
python analysis\multiseed_summary.py --seeds 2 3 4

:: every figure and results table of the paper (needs matplotlib)
python analysis\paper_figures.py
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

The run scripts download CIFAR automatically through torchvision. If the download stalls (it did for us), download the archives yourself and drop them in place; the generator will find and use them.

| Dataset | File | Put it in |
|---|---|---|
| CIFAR-10 | [cifar-10-python.tar.gz](https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz) (~163 MB) | `dataset\Cifar10\rawdata\` |
| CIFAR-100 | [cifar-100-python.tar.gz](https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz) (~161 MB) | `dataset\Cifar100\rawdata\` |

Create the `rawdata` folders if they do not exist. If you get CIFAR-100 from Kaggle instead, use a copy of the **original Python version** (the files `train`, `test` and `meta`) and place them in `dataset\Cifar100\rawdata\cifar-100-python\`.

The data is never committed to the repo (`.gitignore`).

---

## Step 3: build the federated split

The run scripts in `scripts\` do this for you. To do it by hand:

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
scripts\run_reproduction.bat Cifar10
:: then the stabilised FedGDBD-S (can run at the same time if memory allows)
scripts\run_reproduction.bat Cifar10 FedGDBD-S

:: CIFAR-100: same pattern
scripts\run_reproduction.bat Cifar100
scripts\run_reproduction.bat Cifar100 FedGDBD-S
```

Naming one method as the second argument runs only that method, which is also how to restart a single run; its old log is moved to `logs\old\` first.

Each run opens in its own minimised window. Do not close them, and keep the laptop plugged in and awake. Logs go to `logs\<Dataset>_<Method>.log`. Check progress at any time:

```bat
scripts\check_progress.bat
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

## Step 5 (Part B): novelty runs, 20 rounds × 5 seeds

Each dataset needs two scripts per seed. These are all the runs behind the paper's extension results:

```bat
:: control, AGC and AGS (three runs in parallel, one window each)
scripts\run_novelty.bat Cifar10 0
scripts\run_novelty.bat Cifar10 1
scripts\run_novelty.bat Cifar10 2
scripts\run_novelty.bat Cifar10 3
scripts\run_novelty.bat Cifar10 4
scripts\run_novelty.bat Cifar100 0
scripts\run_novelty.bat Cifar100 1
scripts\run_novelty.bat Cifar100 2
scripts\run_novelty.bat Cifar100 3
scripts\run_novelty.bat Cifar100 4

:: matched-alpha control (one run)
scripts\run_amatch.bat Cifar10 0
scripts\run_amatch.bat Cifar10 1
scripts\run_amatch.bat Cifar10 2
scripts\run_amatch.bat Cifar10 3
scripts\run_amatch.bat Cifar10 4
scripts\run_amatch.bat Cifar100 0
scripts\run_amatch.bat Cifar100 1
scripts\run_amatch.bat Cifar100 2
scripts\run_amatch.bat Cifar100 3
scripts\run_amatch.bat Cifar100 4
```

On one GPU, start one script at a time and wait until it finishes before starting the next: the three runs of a `run_novelty.bat` call already fill a 6 GB GPU. We ran CIFAR-10 on one laptop and CIFAR-100 on the other. Without a seed, `scripts\run_amatch.bat Cifar10` runs seeds 0 to 3 in two windows (0 then 2, and 1 then 3), which is how we ran them; seed 4 came later.

Each `run_novelty.bat` call starts FedGDBD-S (control), FedGDBD-AGC and FedGDBD-AGS. `run_amatch.bat` runs FedGDBD-S with one `--gdbd_alpha` for every client: 0.58 on CIFAR-10 and 0.49 on CIFAR-100 (see [PROTOCOL.md](PROTOCOL.md)). Logs go to `logs_novelty\` for seed 0 and `logs_novelty_seed<N>\` for the others, as `<Data>_FedGDBD-S.log`, `_FedGDBD-AGC.log`, `_FedGDBD-AGS.log` and `_FedGDBD-S-amatch.log`. Check progress with `scripts\check_progress.bat novelty <N>`.

What each run executes (from `system\`), for example AGC and the matched-α control on CIFAR-100, seed 1:

```bat
python -u main.py -data Cifar100 -ncl 100 -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 20 -t 1 -go novelty_seed1 -did 0 --gdbd_teacher val --seed 1 -algo FedGDBD-AGC
python -u main.py -data Cifar100 -ncl 100 -m HtFE-img-4 -fd 512 -nc 20 -jr 1 -lbs 10 -lr 0.01 -ls 5 -gr 20 -t 1 -did 0 --gdbd_teacher val --gdbd_alpha 0.49 -algo FedGDBD-S -go novelty_seed1_amatch --seed 1
```

The flags that differ from Part A:

- `--gdbd_teacher val`: the IKD teacher (the client's best past model) is chosen on a 10 % validation slice of the client's training data instead of its test data, so no test data influences training. These runs therefore train on 90 % of the training data, and their numbers are compared **only with each other**, not with Part A.
- `--seed N`: seeds the model initialisation, the client order and k-means. The data split stays the same.
- `--gdbd_alpha A` (matched-α control only): one distillation weight for every client.

**Expected results (best round, %):**

| Run | CIFAR-10 seeds 0 / 1 / 2 / 3 / 4 | CIFAR-100 seeds 0 / 1 / 2 / 3 / 4 |
|---|---|---|
| FedGDBD-S (control) | 86.96 / 86.73 / 86.84 / 86.77 / 86.62 | 42.07 / 42.26 / 41.85 / 42.20 / 41.98 |
| Matched α | 86.80 / 86.46 / 87.06 / 87.23 / 86.90 | 42.04 / 42.59 / 42.12 / 42.52 / 42.32 |
| FedGDBD-AGC | 86.92 / 87.18 / 86.98 / 86.98 / 86.84 | 42.93 / 42.78 / 41.94 / 42.22 / 42.24 |
| FedGDBD-AGS | 87.36 / 87.10 / 86.82 / 87.18 / 87.11 | 42.24 / 42.12 / 41.60 / 41.87 / 41.35 |

Each round takes 14–18 minutes with three runs on one GPU, plus about 7 minutes of pre-training, so one `run_novelty.bat` call finishes in about 5 to 6.5 hours.

Then copy the logs and `.h5` files into `experiments/novelty/run<N+1>_seed<N>/` and summarise:

```bat
python analysis\collect_logs.py 0 1 2 3 4
python analysis\multiseed_summary.py
```

---

## Step 6: check your results

1. Run `python scripts\progress.py <log folder>` or `python analysis\novelty_summary.py <log folder>` (Step 0) on your own log folder.
2. Compare with the expected tables above. Expect close but not identical numbers: GPU kernels are not bit-for-bit deterministic, and the Part A runs were made before the client order was seeded. Across our five seeds the control's best-round accuracy had a standard deviation of 0.13 pt (CIFAR-10) and 0.17 pt (CIFAR-100).
3. The HtFLlib accuracy curves are saved as `.h5` files in `results\` (copies of ours are in `experiments\...\results\`).

Each log contains, per round: every client's test accuracy and AUC, the sample-weighted average (`Averaged Test Accuracy`), the standard deviation, and for AGC / AGS one gate line per client (`Gate client i: g_acc=… alpha=…` or `Gate sample i: kept=…`). The end of a log shows `Best accuracy.` followed by the number we report.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| CIFAR download stalls or fails | Download the `.tar.gz` yourself (Step 2) and place it in `rawdata\`. |
| `CUDA available: False` | Update the NVIDIA driver, then rerun `setup.bat`. A very new GPU may need the cu130 build, which `setup.bat` tries automatically. |
| `CUDA out of memory` | Run fewer methods at once: `scripts\run_reproduction.bat Cifar10 FedProto` starts a single run. A 6 GB GPU fits three CIFAR runs. |
| A window closes immediately | Open the log in `logs\` and read its last lines; usually `.venv` is missing (run `setup.bat`) or the split was not built. |
| `Run setup.bat first` | The script could not find `.venv`; run `setup.bat` from the repo folder. |
| A run stops progressing | `scripts\check_progress.bat` marks a run `STOPPED` after 45 minutes without a new round. Keep the laptop awake and plugged in (Windows power settings: never sleep). |
| The faithful Fed-GDBD accuracy drops | Expected: this is the Eq. 13 instability we report. Use FedGDBD-S. |

---

## Where our own runs are

| Folder | Contents |
|---|---|
| `experiments/cifar10/logs`, `experiments/cifar100/logs` | Part A logs (50 rounds; faithful Fed-GDBD 9–10 rounds) |
| `experiments/cifar10/results`, `experiments/cifar100/results` | Part A `.h5` accuracy curves |
| `experiments/novelty/run1_seed0/` to `run5_seed4/` | Part B, seeds 0 to 4, both datasets, logs + `.h5` (control, AGC, AGS, matched α) |
| `experiments/novelty/multiseed_summary_*.txt` | output of `analysis/multiseed_summary.py` for seeds 0 to 4 and for seeds 2 to 4 |
| `experiments/*/logs/old/` | the earlier run with our IKD masking bug (diverged on CIFAR-100) |
