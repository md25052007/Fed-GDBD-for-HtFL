"""
Fed-GDBD client (Zhang et al., 2025, JKSU-CIS 37:75):
"Federated learning with heterogeneous data and models based on
 global decision boundary distillation".

Re-implemented from the paper (no official code was released).

Per round, a client:
  1. trains locally with  L_local = CE + T^2 * L_IKD          (Eq. 11)
     where L_IKD is the irrelevant-class (non-target) KD from the best
     previous local model (the "teacher").                    (Sec. 3.4)
  2. clusters its features per class with k-means++ into v
     prototypes and uploads them.                             (Eq. 3-4)
  3. after the server has trained the global decision boundary
     learner g on all prototypes, updates its local model with
     L_col = (1-a) * CE + a * T^2 * L_GDBD                    (Eq. 7, 13)

Novelty (FedGDBD-AGC / FedGDBD-AGS, agreement-gated distillation):
  g only gets as much influence as it has earned on THIS client's data.
  AGC: alpha_i = alpha * (accuracy of g on client i's training features)
  AGS: per image, distil only where g's top prediction is correct
  Both sit on top of FedGDBD-S. With --gdbd_teacher val the IKD teacher is
  chosen on a held-out 10 % validation slice instead of the test set.
"""
import copy
import time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from flcore.clients.clientbase import Client, load_item, save_item
from utils.data_utils import read_client_data


class clientGDBD(Client):
    def __init__(self, args, id, train_samples, test_samples, **kwargs):
        super().__init__(args, id, train_samples, test_samples, **kwargs)
        torch.manual_seed(getattr(args, 'seed', 0))  # --seed: model init (default 0 = original runs)

        self.T = args.gdbd_T                      # distillation temperature (paper: 20)
        self.alpha = args.gdbd_alpha              # global decision boundary proportion (paper: 0.7)
        self.num_protos = args.gdbd_v             # prototypes per class (paper: 5)
        self.cluster_iters = args.gdbd_cluster_rounds  # k-means iterations (paper: 100)
        self.update_epochs = args.gdbd_update_epochs   # local model update period (paper: 5)
        self.pretrain_epochs = args.gdbd_pretrain_epochs
        self.best_acc = -1.0
        self.has_teacher = False
        # FedGDBD-S (our stabilised variant): distil g into the head only and
        # rescale g's logits to the student's logit scale (see update()).
        self.stable = getattr(args, 'gdbd_stable', False)
        # Novelty: agreement-gated distillation ('none' | 'client' | 'sample')
        self.gate = getattr(args, 'gdbd_gate', 'none')
        # IKD teacher selection: 'test' (as in our first runs) or 'val'
        # (held-out slice of the client's own training data; no test leakage)
        self.teacher_sel = getattr(args, 'gdbd_teacher', 'test')
        self.val_idx, self.trn_idx = None, None
        if self.teacher_sel == 'val':
            n = train_samples
            n_val = max(1, int(round(n * getattr(args, 'gdbd_val_frac', 0.1))))
            perm = np.random.RandomState(1000 + id).permutation(n)
            self.val_idx, self.trn_idx = sorted(perm[:n_val]), sorted(perm[n_val:])

    # ------------------------------------------------------------------ #
    # Data: with --gdbd_teacher val, 10 % of the training data is held out
    # ------------------------------------------------------------------ #
    def load_train_data(self, batch_size=None):
        if self.trn_idx is None:
            return super().load_train_data(batch_size)
        data = read_client_data(self.dataset, self.id, is_train=True, few_shot=self.few_shot)
        data = [data[i] for i in self.trn_idx]
        return DataLoader(data, batch_size or self.batch_size, drop_last=True, shuffle=False)

    def load_val_data(self):
        data = read_client_data(self.dataset, self.id, is_train=True, few_shot=self.few_shot)
        data = [data[i] for i in self.val_idx]
        return DataLoader(data, self.batch_size, drop_last=False, shuffle=False)

    @torch.no_grad()
    def val_accuracy(self, model):
        model.eval()
        correct, total = 0, 0
        for x, y in self.load_val_data():
            x, y = x.to(self.device), y.to(self.device)
            correct += (model(x).argmax(1) == y).sum().item()
            total += y.shape[0]
        return correct / max(total, 1)

    # ------------------------------------------------------------------ #
    # Losses
    # ------------------------------------------------------------------ #
    def ikd_loss(self, student_logits, teacher_logits, y):
        """Irrelevant-class KD (Sec. 3.4): KL between teacher and student
        distributions over the NON-target classes only, renormalised among
        themselves (as in decoupled KD's NCKD, Zhao et al. 2022, cited by the paper).

        The target logit is removed before the softmax, so this loss has exactly
        zero gradient on the target class (paper Eq. 10) and never fights CE.
        (v1 masked the target term AFTER a full softmax; that version pushed the
        target logit down and made CIFAR-100 training diverge.)
        """
        T = self.T
        target = F.one_hot(y, student_logits.shape[1]).bool()
        s = student_logits.masked_fill(target, -1e4) / T
        t = teacher_logits.masked_fill(target, -1e4) / T
        p_t = F.softmax(t, dim=1)
        kl = p_t * (F.log_softmax(t, dim=1) - F.log_softmax(s, dim=1))
        return kl.sum(dim=1).mean()

    def _step(self, model, optimizer, loss):
        """Backward + SGD step with NaN guard and gradient clipping."""
        if not torch.isfinite(loss):
            optimizer.zero_grad()
            return
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0)
        optimizer.step()

    def gdbd_loss(self, student_logits, g_logits, reduce=True):
        """KL( softmax(g/T) || softmax(h/T) )  (Eq. 7). reduce=False -> per sample."""
        T = self.T
        p_g = F.softmax(g_logits / T, dim=1)
        kl = (p_g * (F.log_softmax(g_logits / T, dim=1)
                     - F.log_softmax(student_logits / T, dim=1))).sum(dim=1)
        return kl.mean() if reduce else kl

    # ------------------------------------------------------------------ #
    # Stage 0: local pre-training (Algorithm 1, line 1)
    # ------------------------------------------------------------------ #
    def pretrain(self):
        trainloader = self.load_train_data()
        model = load_item(self.role, 'model', self.save_folder_name)
        optimizer = torch.optim.SGD(model.parameters(), lr=self.learning_rate)
        model.train()
        for _ in range(self.pretrain_epochs):
            for x, y in trainloader:
                x, y = x.to(self.device), y.to(self.device)
                loss = self.loss(model(x), y)
                self._step(model, optimizer, loss)
        save_item(model, self.role, 'model', self.save_folder_name)

    # ------------------------------------------------------------------ #
    # Stage 1: local supervised learning with IKD (Eq. 11) + clustering
    # ------------------------------------------------------------------ #
    def train(self):
        trainloader = self.load_train_data()
        model = load_item(self.role, 'model', self.save_folder_name)
        teacher = load_item(self.role, 'teacher', self.save_folder_name) if self.has_teacher else None
        if teacher is not None:
            teacher.eval()
        optimizer = torch.optim.SGD(model.parameters(), lr=self.learning_rate)
        model.train()

        start_time = time.time()
        for _ in range(self.local_epochs):
            for x, y in trainloader:
                x, y = x.to(self.device), y.to(self.device)
                output = model(x)
                loss = self.loss(output, y)
                if teacher is not None:
                    with torch.no_grad():
                        t_out = teacher(x)
                    loss = loss + (self.T ** 2) * self.ikd_loss(output, t_out, y)
                self._step(model, optimizer, loss)

        save_item(model, self.role, 'model', self.save_folder_name)
        save_item(self.cluster_prototypes(model), self.role, 'protos', self.save_folder_name)

        self.train_time_cost['num_rounds'] += 1
        self.train_time_cost['total_cost'] += time.time() - start_time

    @torch.no_grad()
    def cluster_prototypes(self, model):
        """Local multi-prototype clustering with k-means++ (Eq. 3-4)."""
        model.eval()
        feats, labels = [], []
        for x, y in self.load_train_data():
            feats.append(model.base(x.to(self.device)))
            labels.append(y.to(self.device))
        feats = torch.cat(feats)
        labels = torch.cat(labels)

        protos, proto_labels = [], []
        for c in labels.unique():
            z = feats[labels == c]
            centers = kmeans_pp(z, self.num_protos, self.cluster_iters)
            protos.append(centers)
            proto_labels.append(torch.full((centers.shape[0],), int(c), device=self.device, dtype=torch.long))
        return torch.cat(protos).cpu(), torch.cat(proto_labels).cpu()

    # ------------------------------------------------------------------ #
    # Stage 2: global decision boundary distillation (Eq. 13)
    # ------------------------------------------------------------------ #
    def update(self):
        trainloader = self.load_train_data()
        model = load_item(self.role, 'model', self.save_folder_name)
        g = load_item('Server', 'g', self.save_folder_name)
        g.eval()
        optimizer = torch.optim.SGD(model.parameters(), lr=self.learning_rate)

        alpha = self.alpha
        if self.gate == 'client':
            # AGC: measure how often g is right on this client's own features
            g_acc = self.g_agreement(model, g, trainloader)
            alpha = self.alpha * g_acc
            print(f'Gate client {self.id}: g_acc={g_acc:.4f} alpha={alpha:.4f}')
        kept, seen = 0, 0
        model.train()

        for _ in range(self.update_epochs):
            for x, y in trainloader:
                x, y = x.to(self.device), y.to(self.device)
                rep = model.base(x)
                output = model.head(rep)
                with torch.no_grad():
                    g_out = g(rep.detach())
                if self.stable:
                    # g is a single linear layer shared by very different feature
                    # spaces; on some architectures its logits are far larger than
                    # the local head's, so T^2*KL swamps CE and the client collapses.
                    # (1) match g's per-sample logit scale to the student's, and
                    # (2) let the KD term update only the head, not the extractor.
                    kd_out = model.head(rep.detach())
                    scale = kd_out.detach().std(dim=1, keepdim=True) / (g_out.std(dim=1, keepdim=True) + 1e-6)
                    g_out = g_out * scale
                else:
                    kd_out = output
                if self.gate == 'sample':
                    # AGS: per image, distil only where g's top class is correct
                    w = (g_out.argmax(dim=1) == y).float()
                    kept += int(w.sum().item()); seen += y.shape[0]
                    ce = F.cross_entropy(output, y, reduction='none')
                    kl = self.gdbd_loss(kd_out, g_out, reduce=False)
                    loss = ((1 - alpha * w) * ce + alpha * w * (self.T ** 2) * kl).mean()
                else:
                    loss = (1 - alpha) * self.loss(output, y) \
                        + alpha * (self.T ** 2) * self.gdbd_loss(kd_out, g_out)
                self._step(model, optimizer, loss)

        if self.gate == 'sample':
            print(f'Gate sample {self.id}: kept={kept / max(seen, 1):.4f}')
        save_item(model, self.role, 'model', self.save_folder_name)

    @torch.no_grad()
    def g_agreement(self, model, g, loader):
        """Fraction of this client's training images that g classifies correctly
        from the client's own features (eval mode, no training)."""
        model.eval()
        correct, total = 0, 0
        for x, y in loader:
            x, y = x.to(self.device), y.to(self.device)
            correct += (g(model.base(x)).argmax(1) == y).sum().item()
            total += y.shape[0]
        return correct / max(total, 1)

    # ------------------------------------------------------------------ #
    # Evaluation + teacher selection ("most optimal model from previous
    # collaborative iterations is selected as the teacher", Sec. 3.5)
    # ------------------------------------------------------------------ #
    def test_metrics(self):
        acc, num, auc = super().test_metrics()
        if self.teacher_sel == 'val':
            cur = self.val_accuracy(load_item(self.role, 'model', self.save_folder_name))
        else:
            cur = acc / max(num, 1e-5)
        if cur > self.best_acc:
            self.best_acc = cur
            model = load_item(self.role, 'model', self.save_folder_name)
            save_item(model, self.role, 'teacher', self.save_folder_name)
            self.has_teacher = True
        return acc, num, auc


@torch.no_grad()
def kmeans_pp(z, k, iters):
    """k-means with k-means++ init on a [n, d] tensor. Returns <=k centers."""
    n = z.shape[0]
    if n <= k:
        return z.clone()
    centers = [z[torch.randint(n, (1,)).item()]]
    for _ in range(1, k):
        d2 = torch.cdist(z, torch.stack(centers)).min(dim=1).values ** 2
        if d2.sum() <= 0:
            break
        idx = torch.multinomial(d2 / d2.sum(), 1).item()
        centers.append(z[idx])
    centers = torch.stack(centers)
    for _ in range(iters):
        assign = torch.cdist(z, centers).argmin(dim=1)
        onehot = F.one_hot(assign, centers.shape[0]).to(z.dtype)   # [n, k]
        counts = onehot.sum(dim=0)                                  # [k]
        sums = onehot.t() @ z                                       # [k, d]
        new_centers = torch.where(counts.unsqueeze(1) > 0,
                                  sums / counts.clamp(min=1).unsqueeze(1), centers)
        if torch.allclose(new_centers, centers):
            break
        centers = new_centers
    return centers
