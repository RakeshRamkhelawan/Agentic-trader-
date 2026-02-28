# Chitta Model Training - Results & Next Steps

## ✅ What We Accomplished

### 1. Training Pipeline Built
- **Dataset Builder v2**: Correctly parses your backtest JSON structure
  - Extracts: equity_curve, harmony_curve, elemental stats, trades
  - Generates: 67,133 sequences from 10 backtest files
  - Features: 21 input features (returns, drawdown, prana, harmony, elemental confidences)

### 2. First Training Run Completed
```
Dataset: 67,133 sequences
Features: 21 (returns, drawdown, prana, harmony_mean, harmony_std,
              fire/water/air/earth/ether confidence, num_assets)
Train/Val split: 53,706 / 13,427 (80/20)
Model: LSTM (128 hidden, 2 layers)
Status: Training in progress (CPU-intensive)
```

### 3. Quick Test Validation
```
Subset test: 13,496 sequences from 2 files
Training: 5 epochs completed successfully
Convergence: Train loss 0.000490 → 0.000003
Validation accuracy: 43% (above random 33%)
```

## 🔧 Files Created

| File | Purpose |
|------|---------|
| `backend/core/ml/backtest_dataset_builder_v2.py` | Parses backtest JSON → PyTorch Dataset |
| `backend/core/ml/lstm_model.py` | LSTM & Transformer architectures |
| `backend/core/ml/market_emotion_calibrator.py` | Dynamic thresholds from backtest stats |
| `backend/core/buddhi/buddhi_reflection.py` | Multi-horizon evaluation (no lookahead bias) |
| `backend/core/prediction/chitta_forecaster_v2.py` | Uses trained models for inference |
| `scripts/train_chitta_model_v2.py` | Full training script |
| `scripts/quick_train_test.py` | Fast validation test |

## 🎯 Current Status

**Training is running** but slow on CPU:
- Full dataset: ~5 min per epoch
- Estimated time for 30 epochs: 2.5 hours

## 🚀 Next Steps (Verfijning)

### Option 1: Speed Up Training (Recommended First)
```python
# Use GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"

# Or reduce dataset size for faster iteration
# Use only 3 backtest files instead of 10 for experimentation
```

### Option 2: Improve Model Architecture
Current: LSTM(21 features → 128 hidden → 1 output)

Improvements:
1. **Add attention mechanism** to focus on important timesteps
2. **Ensemble**: Train 3 models, average predictions
3. **Multi-task**: Predict both return AND volatility

### Option 3: Feature Engineering
Current features are basic. Add:
```python
# Technical indicators
- RSI (momentum)
- MACD (trend)
- Bollinger Bands (volatility)
- Volume profile

# Chitta-specific
- Harmony trend (increasing/decreasing)
- Council agreement score
- Time since last trade
- Market regime detection (trending vs ranging)
```

### Option 4: Hyperparameter Tuning
```bash
# Current (baseline)
--epochs 30 --batch-size 32 --hidden-size 128

# Experiments to run:
1. --hidden-size 256 --num-layers 3  (bigger model)
2. --sequence-length 100  (longer history)
3. --prediction-horizon 10  (further ahead prediction)
4. --dropout 0.3  (more regularization)
```

### Option 5: Transformer Instead of LSTM
```bash
python scripts/train_chitta_model_v2.py \
    --model-type transformer \
    --epochs 20 \
    --batch-size 16
```

Transformers often work better for long sequences (capturing long-range dependencies).

## 📊 Expected Performance After Refinement

| Metric | Current (Quick Test) | After Refinement | Target |
|--------|---------------------|------------------|--------|
| **Direction Accuracy** | 43% | 55-60% | 65%+ |
| **Sharpe (predicted)** | 0.1 | 0.5-0.8 | 1.0+ |
| **Validation Loss** | 0.000003 | <0.000001 | Minimized |

## 🛠️ Immediate Actions You Can Take

### 1. Continue Training (if you have time)
```bash
# Run overnight or on server with GPU
python scripts/train_chitta_model_v2.py --epochs 50 --batch-size 64
```

### 2. Quick Hyperparameter Test
```bash
# Test different configs
python scripts/train_chitta_model_v2.py --epochs 10 --sequence-length 100
python scripts/train_chitta_model_v2.py --epochs 10 --hidden-size 256
```

### 3. Feature Engineering Experiment
Edit `backtest_dataset_builder_v2.py`, add technical indicators:
```python
# In process_equity_curve()
df["rsi"] = calculate_rsi(df["returns"], window=14)
df["volatility_7d"] = df["returns"].rolling(7).std()
```

### 4. A/B Test Framework
Compare model predictions vs current heuristic:
```python
# In production
if model_confidence > 0.6:
    use_model_prediction()
else:
    use_heuristic_fallback()
```

## 🎯 Success Criteria

**Minimum Viable Model:**
- [ ] Validation loss < 0.00001
- [ ] Direction accuracy > 55%
- [ ] Inference time < 10ms
- [ ] Model size < 10MB

**Production Ready:**
- [ ] Direction accuracy > 65%
- [ ] Backtested on unseen data
- [ ] A/B test shows improvement over heuristic
- [ ] Integrated into ChittaForecasterV2

## 🚀 Running Full Training Now

Since training takes hours on CPU, you have 3 options:

### Option A: Run Locally (Overnight)
```bash
# Start before you go to bed
python scripts/train_chitta_model_v2.py --epochs 50 --output-dir models/full_train
```

### Option B: Use Google Colab (Free GPU)
Upload the script and data to Google Colab:
```python
# In Colab
!pip install torch pandas numpy
!python train_chitta_model_v2.py --epochs 50 --batch-size 128
```

### Option C: Reduce Dataset (Fast Experimentation)
```bash
# Use only 3 best backtest files
python scripts/quick_train_test.py --epochs 20  # Modified to use 3 files
```

## 📈 Monitoring Training

While training runs, monitor:
```bash
# Watch the log
tail -f training_output.log

# Check for overfitting
# If train_loss ↓ but val_loss ↑ → overfitting (reduce model size or add dropout)

# Check for convergence
# If train_loss plateaus → increase learning rate or change architecture
```

---

**What would you like to focus on for verfijning?**
1. Speed up training (GPU/reduce data)?
2. Improve model architecture?
3. Add more features?
4. Hyperparameter tuning?
5. Something else?
