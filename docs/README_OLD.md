# 🎯 LLM Debate System

A sophisticated multi-LLM debate system built with LangChain, LangGraph, and local Ollama models. The system orchestrates debates between three specialized LLM agents until they reach consensus, providing comprehensive analysis and insights.

## 🚀 Features

- **🤖 Multi-Agent Architecture**: 1 orchestrator + 3 specialized debater LLMs
- **🔄 LangGraph Workflow**: State-driven debate process with automatic consensus detection
- **📊 Real-time Analytics**: Consensus tracking, response analysis, and performance metrics
- **🌐 Multiple Interfaces**: CLI, Web UI (Streamlit), and REST API
- **🔒 100% Local**: No internet required - uses Ollama for local LLM inference
- **📈 MCP Integration**: Model Context Protocol for advanced context sharing
- **🎨 Beautiful UI**: Modern Streamlit interface with charts and visualizations
- **🔧 Dynamic Configuration**: Automatically adapts to available local models
- **⚡ Smart Launcher**: Pre-flight checks and model management

## 🏗️ Architecture

### Debate Flow
1. **Question Input**: User provides a debate question
2. **Initial Responses**: Three debater LLMs provide initial perspectives
3. **Consensus Analysis**: Semantic similarity analysis using embeddings
4. **Orchestrator Feedback**: Large LLM provides guidance for convergence
5. **Iterative Refinement**: Debaters refine positions based on feedback
6. **Final Summary**: Comprehensive summary when consensus is reached

### Model Configuration
- **Dynamic Mode** (Default): Automatically detects and uses available models
- **Static Mode**: Uses predefined models from config.py

**Recommended Models:**
- **Orchestrator**: `llama3.2:3b` (or any available small model)
- **Analytical Debater**: `gemma2:2b` - Facts and logic focused
- **Creative Debater**: `phi3:mini` - Alternative perspectives and innovation
- **Practical Debater**: `tinyllama:1.1b` - Real-world applications and solutions

**Minimum Requirement:** Any 2+ models will work with dynamic configuration!

## 📋 Prerequisites

1. **Python 3.8+**
2. **Ollama** installed and running
   ```bash
   # Install Ollama from https://ollama.ai/
   ollama serve  # Start the Ollama server
   ```

## ⚡ Quick Start

### Web UI (Recommended)
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Web Interface**:
   ```bash
   # Option 1: Simple reliable UI (wraps CLI)
   streamlit run streamlit_app_simple.py
   
   # Option 2: Robust UI (external process)
   streamlit run streamlit_app_robust.py
   
   # Option 3: ASCII-safe UI (no Unicode issues on Windows)
   streamlit run streamlit_app_ascii.py
   
   # Option 4: Use launcher scripts (Windows)
   run_ui.bat          # Default UI
   run_ui_ascii.bat    # ASCII-safe UI for Windows
   ```

3. **Open Your Browser**: Navigate to `http://localhost:8501` (or port shown in terminal)

### Smart Launcher (CLI)

The smart launcher automatically checks if all required models are available before running:

**Windows:**
```cmd
# Interactive mode with automatic model check
debate.bat

# Direct question mode
debate.bat "What are the benefits of renewable energy?"

# Launch web interface
debate.bat --web

# Launch API server
debate.bat --api

# Skip model check (faster startup)
debate.bat --skip-check "Your question"
```

**Linux/Mac:**
```bash
# Make executable (first time only)
chmod +x debate.sh

# Interactive mode with automatic model check
./debate.sh

# Direct question mode  
./debate.sh "What are the benefits of renewable energy?"

# Launch web interface
./debate.sh --web

# Launch API server
./debate.sh --api

# Skip model check (faster startup)
./debate.sh --skip-check "Your question"
```

**Python Launcher (Cross-platform):**
```bash
# Interactive mode with model check
python run.py

# Direct question mode
python run.py "Your question here"

# Launch web interface
python run.py --web

# Launch API server
python run.py --api

# Skip model check
python run.py --skip-check "Your question"

# Only check models (don't launch app)
python run.py --check-only
```

### Traditional Setup

### Windows
```cmd
# Clone and setup
git clone <repository>
cd llm-debate
setup.bat  # Automated setup script
```

### Linux/Mac
```bash
# Clone and setup
git clone <repository>
cd llm-debate
chmod +x setup.sh
./setup.sh  # Automated setup script
```

### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Download recommended small models (efficient for local use)
ollama pull llama3.2:3b     # Orchestrator (small but capable)
ollama pull gemma2:2b       # Analytical debater
ollama pull phi3:mini       # Creative debater  
ollama pull tinyllama:1.1b  # Practical debater

# Create environment file
cp .env.example .env
```

## 🎮 Usage

### 1. Command Line Interface
```bash
# Interactive mode
python main.py

# Single question mode
python main.py "What are the benefits of renewable energy?"

# Help
python main.py --help
```

### 2. Web Interface (Streamlit)
```bash
# Most reliable (CLI wrapper approach)
streamlit run streamlit_app_simple.py

# Original (may have conflicts with some setups)
streamlit run streamlit_app.py

# Alternative conflict-free versions
streamlit run streamlit_app_robust.py
streamlit run streamlit_app_fixed.py
```
- Navigate to `http://localhost:8501`
- Interactive web interface with real-time charts
- Debate history and analytics

### 3. REST API (FastAPI)
```bash
python api.py
```
- API documentation: `http://localhost:8000/docs`
- Swagger UI: `http://localhost:8000/redoc`

#### API Examples
```bash
# Start a debate
curl -X POST "http://localhost:8000/debates" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the benefits of AI in education?"}'

# Check debate status
curl "http://localhost:8000/debates/{debate_id}"

# Get full results
curl "http://localhost:8000/debates/{debate_id}/full"
```

## 🛠️ Model Management

### Check Model Availability
```bash
# Check which models are available/missing
python check_models.py

# List all required models
python check_models.py --list-models

# Check only (don't offer to download)
python check_models.py --check-only

# Auto-download missing models
python check_models.py --auto-download
```

### Manual Model Download
```bash
# Download all small models manually (recommended)
ollama pull llama3.2:3b     # Orchestrator (small)
ollama pull gemma2:2b       # Analytical Debater
ollama pull phi3:mini       # Creative Debater  
ollama pull tinyllama:1.1b  # Practical Debater

# Check what's installed
ollama list
```

## 🛠️ Configuration

Edit `config.py` to customize:

```python
# Model selection (now using small models)
ORCHESTRATOR_MODEL.model = "llama3.2:3b"  # Small orchestrator
DEBATER_MODELS[0].model = "gemma2:2b"      # Analytical debater

# Debate parameters
MAX_ROUNDS = 5                   # Maximum debate rounds
CONSENSUS_THRESHOLD = 0.85       # Similarity threshold for consensus
MIN_RESPONSE_LENGTH = 50         # Minimum response length
MAX_RESPONSE_LENGTH = 1000       # Maximum response length

# Consensus detection
SIMILARITY_METHOD = "semantic"   # "semantic" or "keyword"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

## 📊 Features Deep Dive

### Consensus Engine
- **Semantic Analysis**: Uses sentence transformers for meaning comparison
- **Keyword Analysis**: TF-IDF vectorization for content similarity
- **Progressive Tracking**: Monitors consensus evolution across rounds
- **Threshold Detection**: Configurable similarity thresholds

### MCP Integration
- **Context Sharing**: Maintains shared knowledge between models
- **Fact Tracking**: Automatically identifies agreed and disputed points
- **Entity Extraction**: Extracts key concepts and claims
- **Conversation Memory**: Maintains debate history and context

### Analytics & Monitoring
- **Consensus Evolution**: Track how agreement develops over time
- **Response Analysis**: Length, quality, and contribution metrics
- **Model Performance**: Compare effectiveness of different LLMs
- **Debate Patterns**: Identify common success/failure patterns

## 🎯 Example Debate Questions

- "What are the benefits and drawbacks of artificial intelligence in education?"
- "Should renewable energy completely replace fossil fuels?"
- "How can we effectively address climate change globally?"
- "What is the best approach to regulate social media platforms?"
- "How will remote work impact society in the long term?"

## 📁 Project Structure

```
llm-debate/
├── main.py                 # CLI interface and main application
├── run.py                  # Smart launcher with model checking
├── check_models.py         # Model availability checker
├── debate.bat             # Windows launcher script
├── debate.sh              # Unix launcher script
├── config.py              # Configuration settings
├── models.py              # Pydantic data models
├── ollama_integration.py  # Ollama LLM integration
├── agents.py              # LangChain debater and orchestrator agents
├── debate_workflow.py     # LangGraph workflow definition
├── consensus_engine.py    # Consensus detection and analysis
├── mcp_integration.py     # Model Context Protocol implementation
├── streamlit_app.py       # Streamlit web interface
├── api.py                 # FastAPI REST API
├── test_system.py         # System test suite
├── requirements.txt       # Python dependencies
├── setup.sh              # Linux/Mac setup script
├── setup.bat             # Windows setup script
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🔧 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   ```bash
   # Ensure Ollama is running
   ollama serve
   
   # Check if accessible
   curl http://localhost:11434/api/tags
   ```

2. **Model Not Found**
   ```bash
   # Download missing small models
   ollama pull llama3.2:3b
   ollama pull gemma2:2b
   ollama pull phi3:mini
   ollama pull tinyllama:1.1b
   ollama list  # Check installed models
   ```

3. **Memory Issues**
   ```bash
   # Use ultra-small models if needed
   # Or use lightweight mode:
   python main.py --lightweight --max-size 2.0
   ```

4. **Unicode/Encoding Errors on Windows**
   ```
   # Error: 'charmap' codec can't encode character
   
   # Solution 1: Use ASCII-safe UI
   streamlit run streamlit_app_ascii.py
   
   # Solution 2: Use batch launcher
   run_ui_ascii.bat
   
   # Solution 3: Set environment variable
   set PYTHONIOENCODING=utf-8
   ```

5. **Streamlit Torch/AsyncIO Conflicts**
   ```bash
   # Use conflict-free versions:
   streamlit run streamlit_app_simple.py    # Most reliable
   streamlit run streamlit_app_robust.py    # External process
   streamlit run streamlit_app_ascii.py     # Windows-safe
   ```

6. **Slow Performance**
   - Reduce `MAX_ROUNDS` in config
   - Use smaller models
   - Adjust `MAX_RESPONSE_LENGTH`

### Logs and Debugging
- Check `debate_logs.txt` for detailed logs
- Enable debug logging in `config.py`: `LOG_LEVEL = "DEBUG"`
- Use `--verbose` flag with CLI commands

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **LangChain**: Framework for building LLM applications
- **LangGraph**: State graph framework for complex workflows
- **Ollama**: Local LLM inference platform
- **Streamlit**: Beautiful web app framework
- **FastAPI**: Modern web API framework

## 📞 Support

- **Issues**: Create an issue on GitHub
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Check the `/docs` folder for detailed guides

---

**Happy Debating! 🎯**
