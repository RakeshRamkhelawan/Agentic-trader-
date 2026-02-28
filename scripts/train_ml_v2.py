"""Train on actual trade outcomes - predict if a trade will be profitable"""
import torch
import torch.nn as nn
import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
import joblib

# Find latest ML backtest
backtest_dir = Path("backtest_results")
ml_files = list(backtest_dir.glob("ml_optimized_*.json"))
if not ml_files:
    raise FileNotFoundError("No ML-optimized backtest files found")
latest_file = max(ml_files, key=lambda x: x.stat().st_mtime)

print(f"Loading: {latest_file.name}")

# Load data
with open(latest_file, 'r') as f:
    data = json.load(f)

trades = data['trades']
print(f"Total trades: {len(trades)}")

# Build dataset: predict trade success from entry features
X_list = []
y_list = []
profits = []

for trade in trades:
    # Entry features at trade start
    x = [
        trade['entry_rsi'] / 100.0,
        np.tanh(trade['entry_macd'] / 10),
        trade['entry_bb_position'],
        np.tanh(trade['entry_momentum'] * 10),
    ]

    # Target: 1 if profitable, 0 if loss
    pnl = trade['pnl']
    y = 1.0 if pnl > 0 else 0.0

    X_list.append(x)
    y_list.append(y)
    profits.append(pnl)

X = np.array(X_list)
y = np.array(y_list)

print(f"Dataset: {len(X)} trades")
print(f"Win rate in data: {np.mean(y)*100:.1f}%")
print(f"Avg profit: ${np.mean(profits):.2f}")
print(f"")

# Check feature variance
for i, name in enumerate(['RSI', 'MACD', 'BB_POS', 'MOMENTUM']):
    print(f"  {name} variance: {np.var(X[:, i]):.4f}")
print(f"")

# Normalize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler
joblib.dump(scaler, 'backtest_results/ml_trade_scaler.joblib')

# Split
X_train, X_test, y_train, y_test, profits_train, profits_test = train_test_split(
    X_scaled, y, profits, test_size=0.2, random_state=42, stratify=y
)

# Dataset
class TradeDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

train_loader = DataLoader(TradeDataset(X_train, y_train), batch_size=32, shuffle=True)
test_loader = DataLoader(TradeDataset(X_test, y_test), batch_size=32)

# Model
class TradePredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 64), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(64, 32), nn.ReLU(), nn.Dropout(0.2),
            nn.Linear(32, 1), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = TradePredictor().to(device)
criterion = nn.BCELoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)

print(f"Training on {device}")
print(f"Train: {len(X_train)}, Test: {len(X_test)}")
print(f"")

# Calculate baseline
baseline_acc = max(np.mean(y_test), 1 - np.mean(y_test))
print(f"Baseline (always predict majority): {baseline_acc*100:.1f}%")
print(f"")

# Train
best_acc = 0
best_epoch = 0
for epoch in range(200):
    model.train()
    train_loss = 0
    for Xb, yb in train_loader:
        Xb, yb = Xb.to(device), yb.to(device)
        optimizer.zero_grad()
        pred = model(Xb).squeeze()
        loss = criterion(pred, yb)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        train_loss += loss.item()

    # Evaluate
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for Xb, yb in test_loader:
            Xb, yb = Xb.to(device), yb.to(device)
            pred = model(Xb).squeeze()
            pred_labels = (pred > 0.5).float()
            correct += (pred_labels == yb).sum().item()
            total += len(yb)

    acc = correct / total
    if acc > best_acc:
        best_acc = acc
        best_epoch = epoch
        torch.save(model.state_dict(), 'backtest_results/ml_trade_predictor.pt')

    if epoch % 40 == 0 or epoch == 199:
        print(f"Epoch {epoch+1:3d}: Loss={train_loss/len(train_loader):.4f}, Acc={acc*100:.1f}%, Best={best_acc*100:.1f}% @ epoch {best_epoch+1}")

print(f"")
print(f"="*50)
print(f"BEST TEST ACCURACY: {best_acc*100:.1f}%")
print(f"Improvement over baseline: +{(best_acc - baseline_acc)*100:.1f}%")
print(f"="*50)
print(f"Model saved: backtest_results/ml_trade_predictor.pt")
print(f"Scaler saved: backtest_results/ml_trade_scaler.joblib")
