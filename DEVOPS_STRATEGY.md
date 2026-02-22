
# LLM Agent Training Strategy & Implementation Guide

## 1. Overview
This project implements a complete pipeline for fine-tuning a Mistral-7B model to act as a trading agent using the ReAct reasoning pattern.

## 2. Pipeline Components
- **Data Preparation**: `model/src/data_prep.py` - Extracts reasoning chains from backtest logs and formats them into instruction-tuning JSONL.
- **Training**: `model/src/train.py` - Implements 4-bit QLoRA fine-tuning using Hugging Face PEFT.
- **Evaluation**: `model/src/eval.py` - Benchmarks model performance and generates analytics reports.
- **Deployment**: `backend/api/gateway_inference.py` - FastAPI gateway for real-time inference.

## 3. LoRA Hyperparameter Selection Best Practices
For an 8GB VRAM GPU (RTX 4060):
- **Rank (R)**: 64 (Provides enough capacity for complex reasoning).
- **Alpha**: 16 (Standard scaling).
- **Target Modules**: `q_proj, v_proj, k_proj, o_proj, gate_proj` (Maximize coverage).
- **Batch Size**: 1 with Gradient Accumulation (4-8) to simulate larger batches without OOM.

## 4. Environment Requirements & Troubleshooting
### The Python 3.13 Windows Blocker
**Issue**: As of early 2026, official PyTorch CUDA wheels for Windows + Python 3.13 are not stable on standard indices.
**Recommended Fix**:
1. Downgrade to **Python 3.11**.
2. Install Torch with: `pip install torch --index-url https://download.pytorch.org/whl/cu121`
3. Use **WSL2 (Ubuntu)** for a more native Linux-like development experience where CUDA wheels are readily available for all Python versions.

## 5. Deployment Instructions
1. Ensure model artifacts are in `./model/artifacts/trading-agent-mistral-lora`.
2. Run the gateway: `python backend/api/gateway_inference.py`.
3. Endpoint: `POST /v1/agent/predict`.
