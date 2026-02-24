#!/bin/bash
# Ollama Setup Script for Agentic Trader Platform
# Usage: ./setup_ollama.sh [model_name]

set -e

MODEL=${1:-llama3.2}

echo "============================================================"
echo "Agentic Trader Platform - Ollama Setup"
echo "============================================================"
echo "Model: $MODEL"
echo ""

# Check if Ollama container is running
if ! docker-compose ps | grep -q "ollama.*Up"; then
    echo "Starting Ollama container..."
    docker-compose --profile llm up -d ollama
    echo "Waiting for Ollama to start..."
    sleep 10
fi

echo "Downloading model: $MODEL"
echo "This may take several minutes depending on the model size..."
echo ""

docker-compose exec ollama ollama pull $MODEL

echo ""
echo "============================================================"
echo "Model downloaded successfully!"
echo "============================================================"
echo ""
echo "Testing model..."
docker-compose exec ollama ollama run $MODEL "Hello, are you working?"

echo ""
echo "============================================================"
echo "Ollama is ready to use!"
echo "============================================================"
echo ""
echo "Update your .env file:"
echo "  LLM_PROVIDER=ollama"
echo "  OLLAMA_BASE_URL=http://ollama:11434"
echo "  OLLAMA_MODEL=$MODEL"
echo ""
echo "Available models:"
docker-compose exec ollama ollama list
echo "============================================================"
