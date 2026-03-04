# GPU-Accelerated Ollama Setup Guide

## Overview

This guide explains how to optimally configure Ollama with GPU acceleration for the Agentic Trader Platform. The setup routes different agent types to the most appropriate LLM provider based on latency requirements.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LLM Gateway                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  HOT PATH    │  │  FAST PATH   │  │  STANDARD/BATCH PATH │  │
│  │  < 100ms     │  │  < 500ms     │  │  > 2s                │  │
│  │              │  │              │  │                      │  │
│  │  Cloud APIs  │  │  Cloud/Local │  │  Ollama GPU          │  │
│  │  - OpenAI    │  │  - Mixed     │  │  - Free              │  │
│  │  - DeepSeek  │  │  - Fallback  │  │  - Unlimited         │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Routing Categories

### Hot Path Agents (Real-time)
**Latency Requirement:** < 100ms
**Provider:** Cloud APIs (OpenAI, DeepSeek)
**Agents:**
- Risk Guardian (order validation)
- Execution Agent (trade execution)

### Fast Path Agents
**Latency Requirement:** < 500ms
**Provider:** Mixed (Cloud preferred, Ollama fallback)
**Agents:**
- News Agent (live news feed)
- Macro Agent (market updates)

### Standard Path Agents (GPU Optimized)
**Latency Requirement:** 1-5s
**Provider:** Ollama GPU (local, free)
**Agents:**
- **Sentiment Agent** - Analyzes news sentiment using `deepseek-r1:7b`
- **Research Agent** - Deep analysis using `deepseek-r1:14b`
- **Valuation Agent** - Fundamental analysis using `deepseek-r1:14b`

### Batch Path Agents (GPU Batch Processing)
**Latency Requirement:** > 5s
**Provider:** Ollama GPU with batching
**Agents:**
- Asset Discovery (bulk analysis)
- Backtest Agent (historical analysis)

## GPU Configuration

### NVIDIA GPU Support

1. **Install NVIDIA Container Toolkit:**
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

2. **Verify GPU Access:**
```bash
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Docker Compose GPU Configuration

The `docker-compose.yml` already includes GPU configuration:

```yaml
ollama:
  image: ollama/ollama:latest
  runtime: nvidia  # Enable NVIDIA runtime
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all  # Use all GPUs
            capabilities: [gpu]
  environment:
    - OLLAMA_NUM_PARALLEL=4        # Parallel requests
    - OLLAMA_MAX_LOADED_MODELS=2   # Keep 2 models in VRAM
    - OLLAMA_GPU_OVERHEAD=512MB    # GPU memory buffer
```

### Ollama Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_NUM_PARALLEL` | 1 | Number of parallel model executions |
| `OLLAMA_MAX_LOADED_MODELS` | 1 | Max models to keep loaded in VRAM |
| `OLLAMA_GPU_OVERHEAD` | 0 | Reserved GPU memory (MB) |
| `OLLAMA_DEBUG` | 0 | Enable debug logging |
| `CUDA_VISIBLE_DEVICES` | all | Which GPU(s) to use |

## Model Selection Guide

### Recommended Models by Task (RTX 4090 8GB VRAM)

| Task | Model | Size | VRAM | Speed | Use Case |
|------|-------|------|------|-------|----------|
| **Sentiment** | deepseek-r1:7b | 4.7GB | ~6GB | Fast | Quick sentiment scoring |
| **Analysis** | deepseek-r1:7b | 4.7GB | ~6GB | Fast | Research analysis |
| **Summarization** | phi3:mini | 2.2GB | ~3GB | Very Fast | News summarization |
| **Coding** | deepseek-r1:7b | 4.7GB | ~6GB | Fast | Strategy scripting |
| **Chat** | phi3:mini | 2.2GB | ~3GB | Very Fast | General queries |

**Total for 2 models in VRAM:** 4.7GB + 2.2GB = 6.9GB < 8GB ✅

### Models to Pull (RTX 4090 8GB)

```bash
# Core models for 8GB VRAM
docker compose exec ollama ollama pull deepseek-r1:7b  # 4.7GB - Analysis/Sentiment
docker compose exec ollama ollama pull phi3:mini        # 2.2GB - Summarization/Chat

# Optional (keep one loaded at a time due to VRAM)
docker compose exec ollama ollama pull codellama:7b     # 3.8GB - Coding tasks
```

### Pull Models

```bash
# Pull recommended models
docker compose exec ollama ollama pull deepseek-r1:7b
docker compose exec ollama ollama pull deepseek-r1:14b
docker compose exec ollama ollama pull phi3:medium
docker compose exec ollama ollama pull codellama:7b

# List available models
docker compose exec ollama ollama list
```

## Performance Optimization

### 1. GPU Memory Management (RTX 4090 8GB)

For a GPU with **8GB VRAM**:
- ✅ **Optimal:** deepseek-r1:7b (4.7GB) + phi3:mini (2.2GB) = 6.9GB total
- Use `OLLAMA_MAX_LOADED_MODELS=2` (keep both loaded)
- Set `OLLAMA_GPU_OVERHEAD=1024` (1GB buffer)
- Total: ~7.9GB / 8GB VRAM

```yaml
environment:
  - OLLAMA_NUM_PARALLEL=4
  - OLLAMA_MAX_LOADED_MODELS=2
  - OLLAMA_GPU_OVERHEAD=1024
```

For a GPU with **16GB VRAM**:
- Keep 2 large models or 3 small models loaded
- Use `OLLAMA_MAX_LOADED_MODELS=2`
- Set `OLLAMA_GPU_OVERHEAD=2048` (2GB buffer)

### 2. Batch Processing

Batch path agents automatically batch requests:
```python
# Process 50 items at once
results = await router.route_batch(
    agent_id="backtest_v1",
    prompts=prompts,
)
```

### 3. Caching

Enable caching for repeated queries:
```python
result = await agent.analyze_news(
    headlines,
    coin="BTC",
    use_cache=True  # Uses LRU cache
)
```

## Verification

### 1. Check GPU Usage

```bash
# Inside Ollama container
docker compose exec ollama nvidia-smi

# Watch GPU usage in real-time
watch -n 1 docker compose exec ollama nvidia-smi
```

### 2. Test GPU Inference

```bash
# Run test query
curl -X POST http://localhost:11435/api/generate -d '{
  "model": "deepseek-r1:7b",
  "prompt": "Analyze sentiment: Bitcoin reaches new all-time high",
  "stream": false
}'
```

### 3. Verify Agent Connection

Check logs:
```bash
docker compose logs api-server | grep -E "(Ollama|Sentiment|GPU)"
```

Expected output:
```
✅ SentimentAgent connected to Ollama (deepseek-r1:7b)
🎮 GPU detected: Models loaded: 1
Sentiment for BTC: bullish (0.72) in 450ms [GPU]
```

## Troubleshooting

### GPU Not Detected

1. Check NVIDIA runtime:
```bash
docker info | grep -i nvidia
```

2. Verify GPU in container:
```bash
docker compose exec ollama nvidia-smi
```

3. Check Ollama logs:
```bash
docker compose logs ollama | grep -i gpu
```

### Out of Memory

1. Reduce parallel executions:
```yaml
environment:
  - OLLAMA_NUM_PARALLEL=1
  - OLLAMA_MAX_LOADED_MODELS=1
```

2. Use smaller model:
```bash
docker compose exec ollama ollama pull phi3:mini  # 1.6GB instead of 3.8GB
```

3. Enable CPU offloading (automatic if GPU OOM)

### Slow Performance

1. Check GPU utilization:
```bash
nvidia-smi dmon -s p
```

2. Ensure models are loaded in VRAM:
```bash
docker compose exec ollama ollama ps
```

3. Reduce batch size if needed:
```python
batch_size=2  # Instead of 4 or 10
```

## Cost Comparison

| Provider | Cost per 1M tokens | Speed | Privacy |
|----------|-------------------|-------|---------|
| **Ollama GPU** | $0 (local) | Medium | ✅ Full |
| **DeepSeek API** | $0.50 | Fast | ❌ Cloud |
| **OpenAI GPT-4** | $10.00 | Fast | ❌ Cloud |
| **OpenAI GPT-4o-mini** | $0.15 | Fast | ❌ Cloud |

**Savings with Ollama GPU:**
- Sentiment analysis: ~$0.001/query → $0 (100% savings)
- Research reports: ~$0.10/query → $0 (100% savings)
- At 10,000 queries/day: **$1,000/day → $0 savings**

## Best Practices

1. **Route by Latency**: Use Cloud APIs only when < 500ms required
2. **Batch Non-Urgent Work**: Queue sentiment analysis for batch processing
3. **Cache Repeated Queries**: News sentiment for same coin within 1 hour
4. **Monitor GPU Memory**: Keep 1-2 models loaded, unload others
5. **Use Appropriate Models**: 7B for sentiment, 14B for deep analysis
6. **Fallback Gracefully**: Always have rule-based fallback if Ollama fails

## Monitoring

### Prometheus Metrics (if enabled)

```
llm_requests_total{provider="ollama"}
llm_latency_seconds{provider="ollama"}
ollama_gpu_memory_used_mb
ollama_models_loaded
```

### Health Checks

```bash
# Ollama health
curl http://localhost:11435/api/tags

# Agent health
curl http://localhost:8003/api/v1/agents/status
```
