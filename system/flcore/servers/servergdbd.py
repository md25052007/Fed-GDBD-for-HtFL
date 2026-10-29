"""
Fed-GDBD server (Algorithm 1 of Zhang et al., 2025).
Maintains the global decision boundary learner g (same structure as the
client classifier head), initialised by sample-weighted head averaging
(Eq. 5) and trained each round on the union of uploaded multi-prototypes
with cross-entropy (Eq. 12).
"""
import copy
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from flcore.clients.clientgdbd import clientGDBD
from flcore.servers.serverbase import Server
from flcore.clients.clientbase import load_item, save_item


class FedGDBD(Server):
    def __init__(self, args, times):
        super().__init__(args, times)
        self.set_slow_clients()
        self.set_clients(clientGDBD)
        print(f"\nJoin ratio / total clients: {self.join_ratio} / {self.num_clients}")
        print("Finished creating server and clients.")
        self.Budget = []
        self.server_epochs = args.gdbd_server_epochs
        self.server_lr = args.server_learning_rate

    def init_global_learner(self):
        """Eq. 5: theta_g = sum_i |D_i|/sum_j |D_j| * theta_i^h."""
        tot = sum(c.train_samples for c in self.clients)
        g = None
        for c in self.clients:
            head = load_item(c.role, 'model', c.save_folder_name).head
            w = c.train_samples / tot
            if g is None:
                g = copy.deepcopy(head)
                for p in g.parameters():
                    p.data.zero_()
            for gp, hp in zip(g.parameters(), head.parameters()):
                gp.data += hp.data.clone() * w
        save_item(g, self.role, 'g', self.save_folder_name)

    def train_global_learner(self):
        """Eq. 12: CE on the global prototype set P^g."""
        P, Y = [], []
        for c in self.selected_clients:
            p, y = load_item(c.role, 'protos', c.save_folder_name)
            P.append(p)
            Y.append(y)
        P, Y = torch.cat(P), torch.cat(Y)
        loader = DataLoader(TensorDataset(P, Y), batch_size=self.batch_size, shuffle=True)

        g = load_item(self.role, 'g', self.save_folder_name)
        g.train()
        opt = torch.optim.SGD(g.parameters(), lr=self.server_lr)
        ce = nn.CrossEntropyLoss()
        for _ in range(self.server_epochs):
            for p, y in loader:
                p, y = p.to(self.device), y.to(self.device)
                loss = ce(g(p), y)
                opt.zero_grad()
                loss.backward()
                opt.step()
        save_item(g, self.role, 'g', self.save_folder_name)

    def train(self):
        print("\nPre-training local models ...")
        t0 = time.time()
        for c in self.clients:
            c.pretrain()
        self.init_global_learner()
        print(f"Pre-training done in {time.time() - t0:.1f}s")

        for i in range(self.global_rounds + 1):
            s_t = time.time()
            self.selected_clients = self.select_clients()

            if i % self.eval_gap == 0:
                print(f"\n-------------Round number: {i}-------------")
                print("\nEvaluate heterogeneous models")
                self.evaluate()

            for client in self.selected_clients:
                client.train()                     # Eq. 11 + clustering

            self.train_global_learner()            # Eq. 12

            for client in self.selected_clients:
                client.update()                    # Eq. 13

            self.Budget.append(time.time() - s_t)
            print('-' * 25, 'time cost', '-' * 25, self.Budget[-1])

            if self.auto_break and self.check_done(acc_lss=[self.rs_test_acc], top_cnt=self.top_cnt):
                break

        print("\nBest accuracy.")
        print(max(self.rs_test_acc))
        print("\nAverage time cost per round.")
        print(sum(self.Budget[1:]) / max(len(self.Budget[1:]), 1))
        self.save_results()
