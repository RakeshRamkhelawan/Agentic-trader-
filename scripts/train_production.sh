#!/bin/bash
# Production Training Script
# Usage: ./scripts/train_production.sh

echo "========================================"
echo "CHITTA PRODUCTION TRAINING"
echo "========================================"
echo "Started at: $(date)"
echo ""

# Config
MODEL_TYPE="transformer"
EPOCHS=50
HIDDEN_SIZE=256
NUM_LAYERS=4
BATCH_SIZE=32
OUTPUT_DIR="models/production"

# Create output dir
mkdir -p $OUTPUT_DIR

# Log file
LOG_FILE="$OUTPUT_DIR/training_$(date +%Y%m%d_%H%M%S).log"

echo "Configuration:"
echo "  Model: $MODEL_TYPE"
echo "  Epochs: $EPOCHS"
echo "  Hidden size: $HIDDEN_SIZE"
echo "  Layers: $NUM_LAYERS"
echo "  Batch size: $BATCH_SIZE"
echo "  Log: $LOG_FILE"
echo ""

# Start training with nohup (continues after disconnect)
nohup python scripts/train_chitta_ultimate.py \
    --model-type $MODEL_TYPE \
    --epochs $EPOCHS \
    --hidden-size $HIDDEN_SIZE \
    --num-layers $NUM_LAYERS \
    --batch-size $BATCH_SIZE \
    --output-dir $OUTPUT_DIR \
    --save-history \
    > $LOG_FILE 2>&1 &

PID=$!
echo "Training started with PID: $PID"
echo $PID > $OUTPUT_DIR/training.pid

echo ""
echo "To monitor progress:"
echo "  tail -f $LOG_FILE"
echo ""
echo "To stop training:"
echo "  kill $PID"
echo ""
echo "Started at: $(date)"
