# Dataset

We used two public image datasets and did not change them:

- **CIFAR-10**: 60,000 colour images of 32 x 32 pixels in 10 classes. https://www.cs.toronto.edu/~kriz/cifar.html
- **CIFAR-100**: 60,000 colour images of 32 x 32 pixels in 100 classes. Same page.

The raw files are not in this repository. `torchvision` downloads them the first time the generator scripts run.

## How the data was split across clients

The split comes from PFLlib's generators, which HtFLlib also uses (`dataset/generate_Cifar10.py`, `dataset/generate_Cifar100.py`, `dataset/utils/dataset_utils.py`). Run from the `dataset/` folder:

```
python generate_Cifar10.py noniid - dir
python generate_Cifar100.py noniid - dir
```

The run scripts in `scripts/` run this command first.

The generator does the following:

1. Merges the official training and test sets (60,000 images) and normalises each channel with mean 0.5 and std 0.5.
2. Splits the images over **20 clients** with a **Dirichlet distribution, β = 0.1** (`alpha = 0.1` in `dataset_utils.py`). This is the paper's "practical" non-IID setting: most clients hold only a few classes, in very unequal amounts.
3. Splits each client's images 75% / 25% into its own training and test set (`train_ratio = 0.75`).

The random seed is fixed in the script (`np.random.seed(1)`), so every run produces the same split. That's why both our laptops trained on identical client data even though they generated it separately. The `--seed` argument of `main.py` doesn't affect the split. It only changes model initialisation, client order and k-means seeding.

## What the generator writes

```
dataset/Cifar10/
  config.json      settings used and the number of images of each class on each client
  train/0.npz ... train/19.npz   one compressed file per client (images and labels)
  test/0.npz  ... test/19.npz
  rawdata/         the downloaded CIFAR files (not needed after the split is made)
dataset/Cifar100/  same layout
```

`config.json` is the quickest way to see how skewed the split is. For each client, it lists how many images of each class that client holds.

If the generated `train/` and `test/` folders are given with this project, copy them into `dataset/Cifar10/` and `dataset/Cifar100/` together with `config.json`. The generator then finds them and doesn't download anything.
