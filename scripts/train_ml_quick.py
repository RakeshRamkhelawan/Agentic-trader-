"""Quick ML training on ML-optimized backtest data"""
import torch
import torch.nn as nn
import json
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler

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

features = data['ml_features']

# Build sequences - predict next action based on current features
X_list = []
y_list = []

for i in range(len(features) - 1):
    f = features[i]
    next_f = features[i + 1]

    # Features at time t
    x = [
        f['rsi'] / 100.0,  # Normalize to 0-1
        np.tanh(f['macd'] / 10),  # Normalize MACD
        f['bb_position'],
        np.tanh(f['mom_1d'] * 10),  # Normalize momentum
        f['volume_ratio'],
        f['atr_pct'] * 10,  # Scale ATR
    ]

    # Target: 1 if next action is BUY (good opportunity), 0 otherwise
    action = next_f['action']
    if action == 'BUY':
        y = 1.0
    else:
        y = 0.0

    X_list.append(x)
    y_list.append(y)

X = np.array(X_list)
y = np.array(y_list)

print(f"Dataset: {len(X)} samples")
print(f"BUY signals: {np.sum(y):.0f} ({np.mean(y)*100:.1f}%)")
print(f"")

# Normalize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler
import joblib
joblib.dump(scaler, 'backtest_results/ml_scaler.joblib')

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# Dataset
class TradingDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

train_loader = DataLoader(TradingDataset(X_train, y_train), batch_size=64, shuffle=True)
test_loader = DataLoader(TradingDataset(X_test, y_test), batch_size=64)

# Model
class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = MLP().to(device)
criterion = nn.BCELoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=1e-4)

print(f"Training on {device}")
print(f"Train: {len(X_train)}, Test: {len(X_test)}")
print(f"")

# Calculate baseline (always predict majority class)
baseline_acc = max(np.mean(y_test), 1 - np.mean(y_test))
print(f"Baseline accuracy: {baseline_acc*100:.1f}%")
print(f"")

# Train
best_acc = 0
for epoch in range(100):
    model.train()
    train_loss = 0
    for Xb, yb in train_loader:
        Xb, yb = Xb.to(device), yb.to(device)
        optimizer.zero_grad()
        pred = model(Xb).squeeze()
        loss = criterion(pred, yb)
        loss.backward()
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
        torch.save(model.state_dict(), 'backtest_results/ml_mlp_best.pt')

    if epoch % 20 == 0 or epoch == 99:
        print(f"Epoch {epoch+1:3d}: Loss={train_loss/len(train_loader):.4f}, Acc={acc*100:.1f}%, Best={best_acc*100:.1f}%")

print(f"")
print(f"BEST TEST ACCURACY: {best_acc*100:.1f}%")
print(f"Improvement over baseline: +{(best_acc - baseline_acc)*100:.1f}%")
print(f"Model saved: backtest_results/ml_mlp_best.pt")
print(f"Scaler saved: backtest_results/ml_scaler.joblib")
