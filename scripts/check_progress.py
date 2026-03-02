#!/usr/bin/env python3
"""
Check training progress
"""

import json
import time
from pathlib import Path

def main():
    history_file = Path("models/production/history_fixed.json")
    model_file = Path("models/production/chitta_fixed_best.pt")

    print("=" * 60)
    print("CHITTA TRAINING PROGRESS")
    print("=" * 60)

    # Check model
    if model_file.exists():
        size_mb = model_file.stat().st_size / 1024 / 1024
        print(f"✓ Model file: {model_file.name}")
        print(f"  Size: {size_mb:.2f} MB")

    # Check history
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

        if history:
            latest = history[-1]
            print(f"\n📈 Latest Epoch: {latest['epoch']}")
            print(f"   Train Loss: {latest['train_loss']:.6f}")
            print(f"   Val Loss:   {latest['val_loss']:.6f}")
            print(f"   Val Acc:    {latest['val_acc']:.2%}")

            # Show last 5 epochs
            print(f"\n📊 Last {min(5, len(history))} epochs:")
            for h in history[-5:]:
                print(f"   E{h['epoch']:2d}: Train={h['train_loss']:.4f}, Val={h['val_loss']:.4f}, Acc={h['val_acc']:.1%}")

            # Best epoch
            best = min(history, key=lambda x: x['val_loss'])
            print(f"\n🏆 Best epoch: {best['epoch']} (Val Loss: {best['val_loss']:.6f})")
    else:
        print("\n⏳ Training just started, no history yet...")

    print("\n" + "=" * 60)
    print("Run this script again to check progress")

if __name__ == "__main__":
    main()
