# LLM Debate System - How to Run

## Overview
This system enables multi-LLM debates using locally available Ollama models with minimal memory usage. It includes both CLI and web UI interfaces.

## Prerequisites

1. **Install Ollama**
   - Download and install Ollama from https://ollama.ai
   - Ensure Ollama is running on `localhost:11434`

2. **Install Python Dependencies**
   ```cmd
   pip install -r requirements.txt
   ```

3. **Download Small Models** (recommended for low memory usage)
   ```cmd
   ollama pull gemma2:2b
   ollama pull phi3:mini
   ollama pull llama3.2:3b
   ollama pull tinyllama:1.1b
   ```

## Running Options

### 1. Web UI (Streamlit) - Recommended
```cmd
streamlit run streamlit_app.py
```
This will open a web browser at `http://localhost:8501` with a full-featured UI including:
- System status checking
- Model configuration
- Interactive debate setup
- Real-time debate monitoring
- Consensus tracking with charts
- Debate history

### 2. Command Line Interface
```cmd
python main.py
```

#### CLI Options:
- `--small-models` - Use only small models (under 4GB)
- `--max-size 2.5` - Set maximum model size in GB
- `--lightweight` - Load/unload models on demand (saves memory)
- `--question "Your debate question"` - Specify question directly
- `--rounds 3` - Set number of debate rounds
- `--consensus-threshold 0.8` - Set consensus threshold

#### Examples:
```cmd
# Basic debate with small models
python main.py --small-models --question "Should AI be regulated?"

# Memory-efficient debate
python main.py --lightweight --max-size 2.5 --question "Is renewable energy economically viable?"

# Full configuration
python main.py --small-models --rounds 5 --consensus-threshold 0.85 --question "Does social media improve democracy?"
```

### 3. Test and Check Scripts

#### Check Available Models:
```cmd
python check_small.py
```

#### Test System Configuration:
```cmd
python test_system.py
```

#### Simple Test:
```cmd
python simple_test.py
```

## Memory Management

The system includes several memory optimization features:

1. **Small Model Mode** (`--small-models`): Only uses models under 4GB
2. **Lightweight Mode** (`--lightweight`): Loads/unloads models on demand
3. **Automatic Cleanup**: Models are unloaded after debates complete
4. **Size Filtering**: Can set custom size limits with `--max-size`

## Recommended Workflow

1. **First Time Setup**:
   ```cmd
   python check_small.py
   ```
   This shows available models and their sizes.

2. **Run Web UI**:
   ```cmd
   streamlit run streamlit_app.py
   ```
   
3. **Check System Status** in the UI to ensure Ollama is connected and models are available.

4. **Start a Debate** using the web interface with your desired configuration.

## Troubleshooting

### Common Issues:

1. **Ollama Not Connected**
   - Ensure Ollama is running: Check if the Ollama app is started
   - Verify port: Ollama should be on `localhost:11434`

2. **Models Not Found**
   - Download required models with `ollama pull <model_name>`
   - Check available models with `ollama list`

3. **Memory Issues**
   - Use `--lightweight` mode
   - Use `--small-models` flag
   - Reduce `--max-size` to 2.5 or lower

4. **Python Import Errors**
   - Install dependencies: `pip install -r requirements.txt`
   - Ensure all files are in the same directory

### Test Commands:
```cmd
# Test Ollama connection
python test_direct_llm.py

# Test configuration
python test_dynamic_config.py

# Check model availability
python check_models.py
```

## Features

### Web UI Features:
- 🔍 Real-time system status checking
- ⚙️ Dynamic model configuration
- 🎯 Interactive debate setup
- 📊 Live consensus tracking with charts
- 📝 Debate history and management
- 🎨 Modern, responsive design

### CLI Features:
- 💾 Memory-efficient model management
- 🔧 Flexible configuration options
- 📋 Detailed logging and output
- ⚡ Direct API calls for better performance

## Model Recommendations

For best performance with limited memory:
- **Orchestrator**: `gemma2:2b` or `phi3:mini`
- **Debaters**: `llama3.2:3b`, `phi3:mini`, `tinyllama:1.1b`

These models provide good reasoning while staying under 4GB each.
