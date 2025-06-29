# 🚀 LLM Debate System - Launch Guide

## Single Command Launch Options

### 🎯 **Recommended: Full Setup & Launch**
```batch
start_full_system.bat
```
**What it does:**
- ✅ Checks all prerequisites (Python, Node.js, npm)
- ✅ Creates Python virtual environment if needed
- ✅ Installs npm dependencies if needed
- ✅ Builds Angular frontend
- ✅ Installs Python dependencies
- ✅ Starts FastAPI backend server

### ⚡ **Quick Start (assumes setup done)**
```batch
quick_start.bat
```
**What it does:**
- ✅ Quick Angular build
- ✅ Starts server immediately
- ⚡ Faster startup (skips dependency checks)

### 🔧 **Development Mode**
```batch
dev_start.bat
```
**What it does:**
- ✅ Starts backend with auto-reload
- ✅ Serves Angular from backend
- 💡 Instructions for Angular dev server

### 🌍 **Cross-Platform (Python)**
```bash
python launch_full_stack.py
```
**What it does:**
- ✅ Works on Windows, macOS, Linux
- ✅ Same functionality as `start_full_system.bat`
- ✅ Full setup and launch

## 🌐 Access Points

Once started, access the system at:

| Service | URL | Description |
|---------|-----|-------------|
| **Main UI** | http://localhost:8000 | Angular frontend |
| **API Docs** | http://localhost:8000/docs | FastAPI documentation |
| **Status** | http://localhost:8000/api/status | System status check |

## 📋 Prerequisites

### Required Software:
- **Python 3.8+** (with pip)
- **Node.js 16+** (with npm)
- **Ollama** (running on localhost:11434)

### Required Models:
```bash
ollama pull phi3:mini
ollama pull llama3.2:1b  
ollama pull gemma2:2b
ollama pull llama3.2:3b
```

## 🔧 Manual Setup (if needed)

### 1. Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate.bat

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r system/requirements.txt
```

### 2. Angular Frontend
```bash
cd angular-ui
npm install
npm run build
cd ..
```

### 3. Start Server
```bash
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🎛️ Development Workflow

### Angular Development (with live reload):
1. Start backend: `dev_start.bat`
2. In another terminal:
   ```bash
   cd angular-ui
   npm start
   ```
3. Access Angular dev server: http://localhost:4200
4. Access backend API: http://localhost:8000

### Backend Development:
- Use `dev_start.bat` for auto-reload on Python changes
- Check logs in terminal
- Test API at http://localhost:8000/docs

## 🛠️ Troubleshooting

### Common Issues:

1. **"Python not found"**
   - Install Python 3.8+ and add to PATH
   - Verify: `python --version`

2. **"Node.js not found"**  
   - Install Node.js 16+ from nodejs.org
   - Verify: `node --version`

3. **"Ollama connection failed"**
   - Start Ollama: `ollama serve`
   - Pull required models (see above)

4. **"Port 8000 already in use"**
   - Stop other services on port 8000
   - Or change port in launch scripts

5. **"Angular build failed"**
   - Delete `angular-ui/node_modules`
   - Run `npm install` in `angular-ui` folder

### Clean Start:
```bash
# Remove old builds
rmdir /s angular-ui\dist
rmdir /s angular-ui\node_modules
rmdir /s .venv

# Fresh start
start_full_system.bat
```

## 📁 File Structure

```
llm debate/
├── 🚀 start_full_system.bat    # Full setup & launch
├── ⚡ quick_start.bat          # Quick launch  
├── 🔧 dev_start.bat            # Development mode
├── 🌍 launch_full_stack.py     # Cross-platform launcher
├── api/                        # FastAPI backend
├── angular-ui/                 # Angular frontend
├── system/                     # Core system
└── backend/                    # LLM integration
```

## ✅ Success Indicators

When the system starts successfully, you should see:

```
✅ System initialized successfully!
📊 Currently loaded models: ['phi3:mini', 'llama3.2:1b', 'llama3.2:3b', 'gemma2:2b']
INFO: Uvicorn running on http://0.0.0.0:8000
```

Navigate to http://localhost:8000 and verify:
- ✅ "System Initialized: ✅" 
- ✅ "Start Debate" button is enabled
- ✅ Models are loaded and visible
