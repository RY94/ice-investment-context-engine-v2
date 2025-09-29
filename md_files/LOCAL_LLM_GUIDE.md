# docs/LOCAL_LLM_GUIDE.md
# Complete local LLM setup guide using Ollama for cost-optimized ICE deployment
# Covers installation, model selection, hybrid configurations, and integration patterns
# Relevant files: setup/local_llm_setup.py, setup/local_llm_adapter.py, ice_lightrag/ice_rag.py, CLAUDE.md

# Local LLM Guide

This guide provides comprehensive instructions for setting up local LLM infrastructure using Ollama for cost-optimized ICE deployment, including hybrid configurations and integration patterns.

## Overview

Local LLM setup using Ollama can reduce ICE operational costs from $50-200/month to $0-7/month while maintaining good performance for financial analysis tasks.

## 🚀 Ollama Installation

### macOS/Linux Installation

```bash
# Install Ollama using the official installer
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version

# Start Ollama service (runs on localhost:11434)
ollama serve
```

### Windows Installation

```bash
# Download from https://ollama.com/download
# Run the installer and follow setup instructions

# Verify installation in Command Prompt or PowerShell
ollama --version

# Start Ollama service
ollama serve
```

### Docker Installation (Alternative)

```bash
# Run Ollama in Docker container
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Pull models
docker exec -it ollama ollama pull llama3.1:8b
```

## 📦 Recommended Models for Financial Analysis

### Primary Models

```bash
# Best balance of speed/quality for financial reasoning
ollama pull llama3.1:8b          # 4.7GB - Recommended primary model

# Better financial domain understanding
ollama pull qwen2.5:7b           # 4.4GB - Alternative for complex financial analysis

# Lightweight option for development
ollama pull llama3.2:3b          # 2.0GB - Fast but lower quality
```

### Embedding Models (Optional for Full Local Setup)

```bash
# Local embeddings model (optional - can use OpenAI embeddings)
ollama pull nomic-embed-text     # 274MB - Local text embeddings

# Alternative embedding model
ollama pull all-minilm          # 46MB - Smaller but lower quality
```

### Testing Model Installation

```bash
# Test model functionality with financial query
ollama run llama3.1:8b "What is the P/E ratio and how is it calculated?"

# Test reasoning capability
ollama run qwen2.5:7b "Explain the relationship between interest rates and tech stock valuations"
```

## ⚙️ Configuration Options

### Option 1: Pure Local Setup (Zero API Costs)

```bash
# Set environment variables for pure local setup
export LLM_MODE="local"
export OLLAMA_MODEL="llama3.1:8b"
export OLLAMA_EMBEDDING_MODEL="nomic-embed-text"
export OPENAI_API_KEY=""  # Not needed for pure local
```

**Benefits:**
- $0/month operational costs
- Complete data privacy
- No internet dependency for inference
- Unlimited usage

**Limitations:**
- Lower reasoning quality for complex financial analysis
- Slower processing for large documents
- Requires local compute resources

### Option 2: Hybrid Local/Remote Setup (Recommended)

```bash
# Hybrid setup: Local for extraction, OpenAI for reasoning
export LLM_MODE="hybrid"
export OLLAMA_MODEL="llama3.1:8b"
export OPENAI_API_KEY="sk-..."  # For complex reasoning only
export HYBRID_THRESHOLD="complex"  # When to use OpenAI
```

**Benefits:**
- ~$7/month costs (entity extraction free, reasoning paid)
- Good balance of cost and performance
- Privacy for entity extraction tasks
- High quality for complex financial reasoning

**Cost Breakdown:**
- Entity extraction: $0 (local)
- Complex reasoning: ~$5/month (OpenAI GPT-4o-mini)
- Embeddings: ~$2/month (OpenAI text-embedding-3-small)

### Option 3: Local + Cloud Embeddings

```bash
# Local LLM with cloud embeddings for better retrieval
export LLM_MODE="local"
export OLLAMA_MODEL="llama3.1:8b"
export OPENAI_API_KEY="sk-..."  # For embeddings only
export USE_LOCAL_EMBEDDINGS="false"
```

**Benefits:**
- ~$2-3/month costs (embeddings only)
- Better retrieval quality than local embeddings
- Complete LLM privacy

## 🔧 Integration with ICE

### ICELightRAG Configuration

```python
from ice_lightrag.ice_rag import ICELightRAG
import os

# Configure ICE for local LLM usage
ice_rag = ICELightRAG(
    working_dir="./ice_lightrag/storage",
    llm_mode=os.getenv("LLM_MODE", "hybrid"),
    ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    use_local_embeddings=os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true"
)

# Test the setup
result = ice_rag.query(
    "What are the key risks for NVIDIA?",
    mode="hybrid"
)
```

### Custom Ollama Integration

```python
import ollama
from typing import Optional, Dict, Any

class OllamaLLMAdapter:
    """Adapter for integrating Ollama with ICE LightRAG"""

    def __init__(self, model_name: str = "llama3.1:8b", host: str = "localhost:11434"):
        self.model_name = model_name
        self.host = host
        self.client = ollama.Client(host=host)

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using local Ollama model"""
        try:
            response = await self.client.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={
                    'temperature': kwargs.get('temperature', 0.1),
                    'top_p': kwargs.get('top_p', 0.9),
                    'num_ctx': kwargs.get('max_tokens', 4096)
                }
            )
            return response['message']['content']
        except Exception as e:
            raise Exception(f"Ollama generation failed: {e}")

    def is_available(self) -> bool:
        """Check if Ollama service is running and model is available"""
        try:
            models = self.client.list()
            return any(model['name'] == self.model_name for model in models.get('models', []))
        except:
            return False
```

## 📊 Performance Optimization

### Model-Specific Optimizations

```python
# Optimized parameters for different Ollama models
MODEL_CONFIGS = {
    "llama3.1:8b": {
        "temperature": 0.1,
        "top_p": 0.9,
        "num_ctx": 4096,
        "repeat_penalty": 1.1,
        "recommended_batch_size": 1
    },
    "qwen2.5:7b": {
        "temperature": 0.05,  # More deterministic for financial analysis
        "top_p": 0.8,
        "num_ctx": 8192,      # Better context for complex documents
        "repeat_penalty": 1.05,
        "recommended_batch_size": 1
    },
    "llama3.2:3b": {
        "temperature": 0.2,
        "top_p": 0.9,
        "num_ctx": 2048,      # Smaller context window
        "repeat_penalty": 1.2,
        "recommended_batch_size": 2
    }
}
```

### Hardware Requirements

```bash
# Minimum requirements for different models
# llama3.1:8b:  8GB RAM, 4GB VRAM (GPU optional)
# qwen2.5:7b:   8GB RAM, 4GB VRAM (GPU optional)
# llama3.2:3b:  4GB RAM, 2GB VRAM (GPU optional)

# Check system resources
free -h                    # Linux
vm_stat                    # macOS
Get-ComputerInfo          # Windows PowerShell
```

### GPU Acceleration (Optional)

```bash
# Enable GPU acceleration if NVIDIA GPU available
export OLLAMA_GPU=1

# Check GPU usage during inference
nvidia-smi

# Monitor Ollama GPU usage
ollama ps
```

## 🔀 Hybrid Decision Logic

### Automatic Task Classification

```python
def classify_task_complexity(prompt: str) -> str:
    """Classify prompt complexity to decide local vs remote processing"""

    # Simple tasks for local processing
    simple_patterns = [
        'extract', 'list', 'identify', 'find', 'what is',
        'define', 'entities', 'relationships', 'keywords'
    ]

    # Complex tasks requiring OpenAI
    complex_patterns = [
        'analyze', 'compare', 'evaluate', 'reasoning', 'strategy',
        'implications', 'forecast', 'recommend', 'synthesize'
    ]

    prompt_lower = prompt.lower()

    if any(pattern in prompt_lower for pattern in complex_patterns):
        return "complex"
    elif any(pattern in prompt_lower for pattern in simple_patterns):
        return "simple"
    else:
        return "medium"  # Default to local for cost efficiency

# Usage in hybrid setup
async def hybrid_llm_processing(prompt: str) -> str:
    complexity = classify_task_complexity(prompt)

    if complexity == "complex" and os.getenv("OPENAI_API_KEY"):
        # Use OpenAI for complex financial reasoning
        return await openai_generate(prompt)
    else:
        # Use local Ollama for simple/medium tasks
        return await ollama_generate(prompt)
```

## 🛠️ Troubleshooting

### Common Issues

**Ollama Service Not Running:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve

# Check service status
curl http://localhost:11434/api/version
```

**Model Not Found:**
```bash
# List available models
ollama list

# Pull missing model
ollama pull llama3.1:8b

# Remove and re-pull corrupted model
ollama rm llama3.1:8b
ollama pull llama3.1:8b
```

**Memory Issues:**
```bash
# Monitor memory usage during inference
top -p $(pgrep ollama)

# Reduce model context size if OOM errors
export OLLAMA_NUM_CTX=2048  # Reduce from default 4096
```

**Slow Performance:**
```bash
# Enable GPU acceleration
export OLLAMA_GPU=1

# Increase thread count for CPU inference
export OLLAMA_NUM_THREAD=8

# Use smaller model for faster inference
ollama pull llama3.2:3b
```

### Health Monitoring

```python
import requests
import asyncio

async def check_ollama_health() -> Dict[str, Any]:
    """Monitor Ollama service health"""
    try:
        # Check service availability
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        service_healthy = response.status_code == 200

        # Check model availability
        models_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = models_response.json().get('models', []) if models_response.status_code == 200 else []

        return {
            "service_healthy": service_healthy,
            "models_available": len(models),
            "models": [model['name'] for model in models],
            "version": response.json().get('version', 'unknown') if service_healthy else 'unknown'
        }
    except Exception as e:
        return {
            "service_healthy": False,
            "error": str(e),
            "models_available": 0
        }

# Usage
health_status = await check_ollama_health()
print(f"Ollama Health: {health_status}")
```

## 💰 Cost Analysis

### Monthly Cost Comparison

| Configuration | LLM Costs | Embedding Costs | Total/Month | Use Case |
|---------------|-----------|-----------------|-------------|----------|
| **Pure Local** | $0 | $0 | **$0** | Development, privacy-focused |
| **Hybrid Recommended** | $5 | $2 | **$7** | Small fund, balanced performance |
| **Local + Cloud Embeddings** | $0 | $3 | **$3** | Privacy with good retrieval |
| **Full Cloud** | $50 | $8 | **$58** | Production, maximum performance |

### ROI Calculation

```python
# Calculate savings from local LLM deployment
def calculate_local_llm_savings():
    """Calculate monthly savings from local LLM vs cloud-only"""

    cloud_only_costs = {
        "llm_processing": 50,    # GPT-4 for all tasks
        "embeddings": 8,         # text-embedding-3-large
        "api_calls": 12          # API overhead
    }

    hybrid_local_costs = {
        "llm_processing": 5,     # GPT-4o-mini for complex only
        "embeddings": 2,         # text-embedding-3-small
        "api_calls": 0           # Local processing
    }

    monthly_savings = sum(cloud_only_costs.values()) - sum(hybrid_local_costs.values())
    annual_savings = monthly_savings * 12

    return {
        "monthly_savings": monthly_savings,
        "annual_savings": annual_savings,
        "cost_reduction_percentage": (monthly_savings / sum(cloud_only_costs.values())) * 100
    }

# Results: ~$63/month savings (~90% cost reduction)
```

## 🔗 Integration Scripts

### Automated Setup Script

```bash
#!/bin/bash
# setup_local_llm.sh - Automated Ollama setup for ICE

echo "🚀 Setting up Ollama for ICE Investment Context Engine"

# Install Ollama
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
sleep 5

# Pull recommended models
echo "Downloading recommended models..."
ollama pull llama3.1:8b
ollama pull qwen2.5:7b

# Optional: Pull embedding model for full local setup
read -p "Install local embedding model? (y/n): " install_embeddings
if [[ $install_embeddings == "y" ]]; then
    ollama pull nomic-embed-text
fi

# Set environment variables
echo "Setting up environment variables..."
echo 'export LLM_MODE="hybrid"' >> ~/.bashrc
echo 'export OLLAMA_MODEL="llama3.1:8b"' >> ~/.bashrc

echo "✅ Ollama setup complete! Restart your terminal to use new environment variables."
```

---

**Related Documentation:**
- [LightRAG Setup](LIGHTRAG_SETUP.md) - Complete LightRAG configuration guide
- [Query Patterns](QUERY_PATTERNS.md) - Query optimization and mode selection
- [CLAUDE.md](../CLAUDE.md) - Main development guide
- [Setup Scripts](../setup/) - Automated configuration utilities