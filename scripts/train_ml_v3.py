"""Train on price direction prediction using technical indicators"""
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

features = data['ml_features']
print(f"Total feature records: {len(features)}")

# Build sequences - predict next price direction
X_list = []
y_list = []
price_changes = []

for i in range(len(features) - 1):
    f = features[i]
    next_f = features[i + 1]

    # Features at time t
    x = [
        f['rsi'] / 100.0,
        np.tanh(f['macd'] / 10),
        f['bb_position'],
        np.tanh(f['mom_1d'] * 10),
        f['volume_ratio'] / 2,  # Normalize
        np.tanh(f['atr_pct'] * 5),
    ]

    # Target: 1 if price goes up next period, 0 if down
    price_change = (next_f['price'] - f['price']) / f['price']
    y = 1.0 if price_change > 0 else 0.0

    X_list.append(x)
    y_list.append(y)
    price_changes.append(price_change)

X = np.array(X_list)
y = np.array(y_list)

print(f"Dataset: {len(X)} samples")
print(f"Price up: {np.sum(y):.0f} ({np.mean(y)*100:.1f}%)")
print(f"Avg price change: {np.mean(price_changes)*100:.3f}%")
print(f"")

# Check feature variance
for i, name in enumerate(['RSI', 'MACD', 'BB_POS', 'MOM', 'VOL_RATIO', 'ATR']):
    print(f"  {name} variance: {np.var(X[:, i]):.4f}")
print(f"")

# Normalize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Save scaler
joblib.dump(scaler, 'backtest_results/ml_direction_scaler.joblib')

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)

# Dataset
class DirectionDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    def __len__(self): return len(self.X)
    def __getitem__(self, i): return self.X[i], self.y[i]

train_loader = DataLoader(DirectionDataset(X_train, y_train), batch_size=64, shuffle=True)
test_loader = DataLoader(DirectionDataset(X_test, y_test), batch_size=64)

# Model
class DirectionPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 64), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(64, 1), nn.Sigmoid()
        )
    def forward(self, x): return self.net(x)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = DirectionPredictor().to(device)
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
train_losses = []
for epoch in range(150):
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

    avg_loss = train_loss / len(train_loader)
    train_losses.append(avg_loss)

    # Evaluate every 10 epochs
    if epoch % 10 == 0 or epoch == 149:
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
            torch.save(model.state_dict(), 'backtest_results/ml_direction_predictor.pt')

        print(f"Epoch {epoch+1:3d}: Loss={avg_loss:.4f}, Acc={acc*100:.1f}%, Best={best_acc*100:.1f}%")

print(f"")
print(f"="*50)
print(f"FINAL RESULTS:")
print(f"  Best accuracy: {best_acc*100:.1f}%")
print(f"  Baseline: {baseline_acc*100:.1f}%")
print(f"  Improvement: +{(best_acc - baseline_acc)*100:.1f}%")
if best_acc > baseline_acc + 0.05:
    print(f"  Status: MODEL LEARNED PATTERNS!")
else:
    print(f"  Status: No significant learning")
print(f"="*50)
print(f"Model saved: backtest_results/ml_direction_predictor.pt")
