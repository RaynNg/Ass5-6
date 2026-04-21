#!/usr/bin/env python3
"""
train_models.py
===============
Trains RNN, LSTM, BiLSTM on user-behavior sequences from data_user500.csv.
Task: given the last SEQ_LEN (product_id, action) pairs predict next action.
Classes: view=0, click=1, add_to_cart=2

Usage:
    python models/train_models.py
Outputs:
    models/model_best.pt          – best model weights
    models/plots/training_curves.png
    models/plots/model_comparison.png
    models/plots/confusion_matrices.png
"""

import os, sys, warnings
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix,
)

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

warnings.filterwarnings("ignore")
torch.manual_seed(42)
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 0.  Paths & hyper-params
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_PATH  = os.path.join(ROOT_DIR, "data_user500.csv")
PLOTS_DIR  = os.path.join(SCRIPT_DIR, "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)

SEQ_LEN     = 3        # window: t-2, t-1, t  →  predict t+1
BATCH_SIZE  = 64
EPOCHS      = 50
LR          = 1e-3
HIDDEN      = 128
NUM_LAYERS  = 2
DROPOUT     = 0.3
NUM_CLASSES = 3
DEVICE      = torch.device("cuda" if torch.cuda.is_available() else "cpu")
COLORS      = {"RNN": "#4C72B0", "LSTM": "#DD8452", "BiLSTM": "#55A868"}

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Load & encode
# ─────────────────────────────────────────────────────────────────────────────
print(f"Loading {DATA_PATH} ...")
df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])
df = df.sort_values(["user_id", "timestamp"]).reset_index(drop=True)

ACTION_MAP = {"view": 0, "click": 1, "add_to_cart": 2}
df["act"] = df["action"].map(ACTION_MAP)

# normalise product_id → [0,1]
prods_sorted = sorted(df["product_id"].unique())
prod_map = {p: i / max(len(prods_sorted) - 1, 1) for i, p in enumerate(prods_sorted)}
df["prod_norm"] = df["product_id"].map(prod_map)

# ─────────────────────────────────────────────────────────────────────────────
# 2.  Build sliding-window sequences
# ─────────────────────────────────────────────────────────────────────────────
print("Building sequences ...")
Xs, ys = [], []
for _, grp in df.groupby("user_id"):
    acts  = grp["act"].values
    prods = grp["prod_norm"].values
    for i in range(len(acts) - SEQ_LEN):
        seq = [[prods[j], acts[j] / 2.0] for j in range(i, i + SEQ_LEN)]
        Xs.append(seq)
        ys.append(acts[i + SEQ_LEN])

X = np.array(Xs, dtype=np.float32)   # (N, SEQ_LEN, 2)
y = np.array(ys, dtype=np.int64)
print(f"  Samples: {len(y)}  |  class counts: {dict(zip(['view','click','add_to_cart'], np.bincount(y)))}")

X_tmp,  X_test,  y_tmp,  y_test  = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)
X_train, X_val,  y_train, y_val  = train_test_split(X_tmp, y_tmp, test_size=0.20, stratify=y_tmp, random_state=42)
print(f"  Train={len(y_train)}, Val={len(y_val)}, Test={len(y_test)}")

# ─────────────────────────────────────────────────────────────────────────────
# 3.  Dataset & DataLoaders
# ─────────────────────────────────────────────────────────────────────────────
class BehaviorDS(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
    def __len__(self):  return len(self.y)
    def __getitem__(self, i): return self.X[i], self.y[i]

kw = dict(batch_size=BATCH_SIZE, drop_last=False)
train_ld = DataLoader(BehaviorDS(X_train, y_train), shuffle=True,  **kw)
val_ld   = DataLoader(BehaviorDS(X_val,   y_val),   shuffle=False, **kw)
test_ld  = DataLoader(BehaviorDS(X_test,  y_test),  shuffle=False, **kw)

# ─────────────────────────────────────────────────────────────────────────────
# 4.  Model definitions
# ─────────────────────────────────────────────────────────────────────────────
def _head(in_dim):
    return nn.Sequential(
        nn.LayerNorm(in_dim),
        nn.Dropout(DROPOUT),
        nn.Linear(in_dim, NUM_CLASSES),
    )

class RNNModel(nn.Module):
    name = "RNN"
    def __init__(self):
        super().__init__()
        self.rnn  = nn.RNN(2, HIDDEN, NUM_LAYERS, batch_first=True,
                           dropout=DROPOUT if NUM_LAYERS > 1 else 0.0)
        self.head = _head(HIDDEN)
    def forward(self, x):
        out, _ = self.rnn(x)
        return self.head(out[:, -1])

class LSTMModel(nn.Module):
    name = "LSTM"
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(2, HIDDEN, NUM_LAYERS, batch_first=True,
                            dropout=DROPOUT if NUM_LAYERS > 1 else 0.0)
        self.head = _head(HIDDEN)
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.head(out[:, -1])

class BiLSTMModel(nn.Module):
    name = "BiLSTM"
    def __init__(self):
        super().__init__()
        self.bilstm = nn.LSTM(2, HIDDEN, NUM_LAYERS, batch_first=True,
                              bidirectional=True,
                              dropout=DROPOUT if NUM_LAYERS > 1 else 0.0)
        self.head = _head(HIDDEN * 2)
    def forward(self, x):
        out, _ = self.bilstm(x)
        return self.head(out[:, -1])

# ─────────────────────────────────────────────────────────────────────────────
# 5.  Training loop
# ─────────────────────────────────────────────────────────────────────────────
def train_one(model):
    model.to(DEVICE)
    opt  = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=EPOCHS)
    crit = nn.CrossEntropyLoss()

    hist = {k: [] for k in ("train_loss", "val_loss", "train_acc", "val_acc")}
    best_val_acc, best_state = 0.0, None

    for ep in range(1, EPOCHS + 1):
        # Train
        model.train()
        tl, tc, tt = 0.0, 0, 0
        for xb, yb in train_ld:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            opt.zero_grad()
            logits = model(xb)
            loss   = crit(logits, yb)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            tl += loss.item() * len(yb)
            tc += (logits.argmax(1) == yb).sum().item()
            tt += len(yb)
        sched.step()

        # Validate
        model.eval()
        vl, vc, vt = 0.0, 0, 0
        with torch.no_grad():
            for xb, yb in val_ld:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                logits = model(xb)
                vl += crit(logits, yb).item() * len(yb)
                vc += (logits.argmax(1) == yb).sum().item()
                vt += len(yb)

        tacc, vacc = tc / tt, vc / vt
        hist["train_loss"].append(tl / tt)
        hist["val_loss"].append(vl / vt)
        hist["train_acc"].append(tacc)
        hist["val_acc"].append(vacc)

        if vacc > best_val_acc:
            best_val_acc = vacc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if ep % 10 == 0:
            print(f"    ep {ep:3d}/{EPOCHS}  train_loss={tl/tt:.4f}  val_acc={vacc:.4f}")

    model.load_state_dict(best_state)
    print(f"  Best val_acc = {best_val_acc:.4f}")
    return hist

# ─────────────────────────────────────────────────────────────────────────────
# 6.  Evaluation helper
# ─────────────────────────────────────────────────────────────────────────────
def evaluate(model, loader):
    model.eval()
    preds_all, true_all = [], []
    with torch.no_grad():
        for xb, yb in loader:
            preds_all.extend(model(xb.to(DEVICE)).argmax(1).cpu().numpy())
            true_all.extend(yb.numpy())
    return np.array(true_all), np.array(preds_all)

# ─────────────────────────────────────────────────────────────────────────────
# 7.  Train all three models
# ─────────────────────────────────────────────────────────────────────────────
model_classes = [RNNModel, LSTMModel, BiLSTMModel]
histories = {}
results   = {}
model_instances = {}

for Cls in model_classes:
    mdl = Cls()
    print(f"\n{'='*55}")
    print(f"  Training {mdl.name}")
    print(f"{'='*55}")
    hist = train_one(mdl)
    histories[mdl.name] = hist

    y_true, y_pred = evaluate(mdl, test_ld)
    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average="weighted", zero_division=0)
    rec  = recall_score(y_true, y_pred, average="weighted", zero_division=0)
    f1   = f1_score(y_true, y_pred, average="weighted", zero_division=0)

    results[mdl.name] = dict(accuracy=acc, precision=prec, recall=rec, f1=f1,
                              y_true=y_true, y_pred=y_pred)
    model_instances[mdl.name] = mdl

    print(f"\n  {mdl.name} – Test metrics")
    print(f"  {'Accuracy':<12}: {acc:.4f}")
    print(f"  {'Precision':<12}: {prec:.4f}")
    print(f"  {'Recall':<12}: {rec:.4f}")
    print(f"  {'F1-Score':<12}: {f1:.4f}")
    print()
    print(classification_report(y_true, y_pred,
                                target_names=["view", "click", "add_to_cart"]))

# ─────────────────────────────────────────────────────────────────────────────
# 8.  Choose & save best model
# ─────────────────────────────────────────────────────────────────────────────
best_name = max(results, key=lambda n: results[n]["f1"])
best_mdl  = model_instances[best_name]

print(f"\n{'*'*55}")
print(f"  BEST MODEL: {best_name}")
print(f"  F1={results[best_name]['f1']:.4f}  "
      f"Acc={results[best_name]['accuracy']:.4f}")
print(f"{'*'*55}")

# Narrative evaluation
lines = [
    "",
    "=== Model Evaluation Summary ===",
    "",
]
for name in ["RNN", "LSTM", "BiLSTM"]:
    r = results[name]
    lines.append(f"{name:8s}  Acc={r['accuracy']:.4f}  Prec={r['precision']:.4f}"
                 f"  Rec={r['recall']:.4f}  F1={r['f1']:.4f}")
lines += [
    "",
    f"Selected: {best_name}",
    "",
    "Reasoning:",
    f"  • RNN  – simplest architecture; may struggle with long-range patterns.",
    f"  • LSTM – gating mechanism captures temporal dependencies better than vanilla RNN.",
    f"  • BiLSTM – processes sequence in both directions; richest representation.",
    f"",
    f"  The {best_name} achieved the highest weighted F1-Score on the held-out test set,",
    f"  indicating the best balance of precision and recall across all three action classes.",
    f"  With user behavior sequences the ordering of past actions matters, making gated",
    f"  architectures (LSTM / BiLSTM) generally superior to vanilla RNN.",
]
eval_text = "\n".join(lines)
print(eval_text)

save_path = os.path.join(SCRIPT_DIR, "model_best.pt")
torch.save({"name": best_name, "state_dict": best_mdl.state_dict(),
            "config": {"hidden": HIDDEN, "num_layers": NUM_LAYERS, "seq_len": SEQ_LEN}},
           save_path)
print(f"\nSaved model_best.pt → {save_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 9.  Plots
# ─────────────────────────────────────────────────────────────────────────────
EPOCH_RANGE = range(1, EPOCHS + 1)
LABELS = ["view", "click", "add_to_cart"]

# ── Plot 1: Training curves (loss + accuracy per model) ──────────────────────
fig, axes = plt.subplots(2, 3, figsize=(16, 8))
fig.suptitle("Training Curves – RNN vs LSTM vs BiLSTM", fontsize=15, fontweight="bold", y=1.02)

for col, name in enumerate(["RNN", "LSTM", "BiLSTM"]):
    h   = histories[name]
    col_color = COLORS[name]
    ax_l, ax_a = axes[0][col], axes[1][col]

    ax_l.plot(EPOCH_RANGE, h["train_loss"], color=col_color,       label="Train",  linewidth=2)
    ax_l.plot(EPOCH_RANGE, h["val_loss"],   color=col_color, ls="--", label="Val", linewidth=2)
    ax_l.set_title(f"{name} – Loss", fontweight="bold")
    ax_l.set_xlabel("Epoch"); ax_l.set_ylabel("Cross-Entropy Loss")
    ax_l.legend(fontsize=9); ax_l.grid(alpha=0.3)

    ax_a.plot(EPOCH_RANGE, h["train_acc"], color=col_color,       label="Train",  linewidth=2)
    ax_a.plot(EPOCH_RANGE, h["val_acc"],   color=col_color, ls="--", label="Val", linewidth=2)
    ax_a.set_title(f"{name} – Accuracy", fontweight="bold")
    ax_a.set_xlabel("Epoch"); ax_a.set_ylabel("Accuracy")
    ax_a.set_ylim(0, 1.05); ax_a.legend(fontsize=9); ax_a.grid(alpha=0.3)

plt.tight_layout()
p1 = os.path.join(PLOTS_DIR, "training_curves.png")
plt.savefig(p1, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {p1}")

# ── Plot 2: Metric comparison bar chart ──────────────────────────────────────
metric_keys   = ["accuracy", "precision", "recall", "f1"]
metric_labels = ["Accuracy", "Precision", "Recall", "F1-Score"]
x = np.arange(len(metric_keys))
width = 0.25

fig, ax = plt.subplots(figsize=(11, 5))
for i, name in enumerate(["RNN", "LSTM", "BiLSTM"]):
    vals = [results[name][k] for k in metric_keys]
    bars = ax.bar(x + i * width, vals, width, label=name,
                  color=COLORS[name], edgecolor="white", linewidth=0.5)
    ax.bar_label(bars, fmt="%.3f", fontsize=8, padding=3)

ax.set_xticks(x + width)
ax.set_xticklabels(metric_labels, fontsize=11)
ax.set_ylim(0, 1.18)
ax.set_title("Model Comparison – Test-Set Metrics", fontsize=14, fontweight="bold")
ax.legend(fontsize=10); ax.grid(axis="y", alpha=0.3)
ax.set_ylabel("Score")

# Mark best model
best_f1 = results[best_name]["f1"]
ax.annotate(f"★ Best: {best_name}", xy=(3 + ["RNN","LSTM","BiLSTM"].index(best_name)*width, best_f1),
            xytext=(2.5, best_f1 + 0.08),
            arrowprops=dict(arrowstyle="->", color="black"),
            fontsize=10, color="black", fontweight="bold")

plt.tight_layout()
p2 = os.path.join(PLOTS_DIR, "model_comparison.png")
plt.savefig(p2, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {p2}")

# ── Plot 3: Confusion matrices ───────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
fig.suptitle("Confusion Matrices – Test Set", fontsize=14, fontweight="bold")

for ax, name in zip(axes, ["RNN", "LSTM", "BiLSTM"]):
    cm  = confusion_matrix(results[name]["y_true"], results[name]["y_pred"])
    im  = ax.imshow(cm, cmap="Blues")
    fig.colorbar(im, ax=ax, shrink=0.7)

    ax.set_xticks(range(3)); ax.set_yticks(range(3))
    ax.set_xticklabels(LABELS, rotation=25, ha="right", fontsize=9)
    ax.set_yticklabels(LABELS, fontsize=9)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True")
    acc = results[name]["accuracy"]
    ax.set_title(f"{name}  (Acc={acc:.3f})", fontweight="bold")

    for r in range(3):
        for c in range(3):
            val = cm[r, c]
            col = "white" if val > cm.max() * 0.55 else "black"
            ax.text(c, r, str(val), ha="center", va="center",
                    fontsize=12, fontweight="bold", color=col)

plt.tight_layout()
p3 = os.path.join(PLOTS_DIR, "confusion_matrices.png")
plt.savefig(p3, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {p3}")

# ── Plot 4: F1 per class (grouped bar) ───────────────────────────────────────
from sklearn.metrics import f1_score as f1_per_class

fig, ax = plt.subplots(figsize=(9, 4))
x2 = np.arange(3)  # 3 classes
for i, name in enumerate(["RNN", "LSTM", "BiLSTM"]):
    per_class = f1_score(results[name]["y_true"], results[name]["y_pred"],
                         average=None, zero_division=0)
    bars = ax.bar(x2 + i * 0.25, per_class, 0.25, label=name,
                  color=COLORS[name], edgecolor="white")
    ax.bar_label(bars, fmt="%.2f", fontsize=8, padding=2)

ax.set_xticks(x2 + 0.25)
ax.set_xticklabels(LABELS, fontsize=11)
ax.set_ylim(0, 1.15)
ax.set_title("Per-Class F1-Score Comparison", fontsize=13, fontweight="bold")
ax.set_ylabel("F1-Score"); ax.legend(fontsize=10); ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
p4 = os.path.join(PLOTS_DIR, "per_class_f1.png")
plt.savefig(p4, dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {p4}")

print(f"\nAll plots saved to {PLOTS_DIR}/")
print("Training complete!")
