#!/bin/bash

# LLM Debate System Setup Script

echo "🎯 LLM Debate System Setup"
echo "=========================="

# Check Python version
python_version=$(python --version 2>&1)
echo "Python version: $python_version"

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "✅ Ollama is installed"
    ollama_version=$(ollama --version)
    echo "Ollama version: $ollama_version"
else
    echo "❌ Ollama is not installed"
    echo "Please install Ollama from: https://ollama.ai/"
    echo "Then run: ollama serve"
    exit 1
fi

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "❌ Ollama is not running"
    echo "Please start Ollama with: ollama serve"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Download required models
echo "🤖 Downloading required Ollama models..."

models=("llama3.1:70b" "llama3.1:8b" "mistral:7b" "phi3:medium")

for model in "${models[@]}"; do
    echo "Downloading $model..."
    ollama pull $model
    if [ $? -eq 0 ]; then
        echo "✅ $model downloaded successfully"
    else
        echo "⚠️ Failed to download $model - will be downloaded when first used"
    fi
done

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your settings if needed."
fi

# Test the system
echo "🧪 Testing system initialization..."
python -c "
import asyncio
from main import LLMDebateSystem

async def test():
    system = LLMDebateSystem()
    success = await system.initialize()
    if success:
        print('✅ System test passed')
    else:
        print('❌ System test failed')

asyncio.run(test())
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Usage options:"
echo "  1. Interactive CLI: python main.py"
echo "  2. Single question: python main.py 'Your question here'"
echo "  3. Web interface: streamlit run streamlit_app.py"
echo "  4. REST API: python api.py"
echo ""
echo "Example:"
echo "  python main.py 'What are the benefits of renewable energy?'"
echo ""
