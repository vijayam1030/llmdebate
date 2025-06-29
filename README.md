# 🎯 LLM Debate System - Angular Edition

**A modern AI debate system with Angular frontend and FastAPI backend using local Ollama models**

## 🚀 Quick Start

### **Windows (Easiest)**
```bash
# Double-click:
start_angular_ui.bat

# Or from command line:
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### **Any Platform**
```bash
# Install Python dependencies:
pip install -r system/requirements.txt

# Install Angular dependencies (first time only):
cd angular-ui && npm install && cd ..

# Build Angular frontend (first time only):
cd angular-ui && npx ng build && cd ..

# Run the server:
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 🌐 Access the Application

Open your browser and go to: **http://localhost:8000**

## 📁 Project Structure

```
📁 Root (Clean!)
├── api/                        🚀 FastAPI backend
│   └── main.py                    REST API server
├── angular-ui/                 🎨 Angular frontend
│   ├── src/                       Source code
│   └── dist/                      Built files (served by API)
├── start_angular_ui.bat        ⭐ Main launcher
├── system/                     🔧 Core system files
├── backend/                    🤖 Debate logic
├── ui/                         📁 Legacy Streamlit UIs
├── legacy/                     📁 Old/archived files
├── README.md                   📖 This file
└── .env                        🔧 Environment config

📁 /api/                        🚀 FastAPI Backend
├── main.py                     🌐 REST API server with endpoints

📁 /angular-ui/                 🎨 Angular Frontend  
├── src/app/                    📱 Angular components
├── dist/                       📦 Built files (auto-served)
└── package.json                📋 Node dependencies

📁 /backend/                    🔧 Core system logic
├── agents.py                   🤖 AI agents
├── models.py                   📊 Data models  
├── debate_workflow.py          🔄 Debate flow
├── consensus_engine.py         🎯 Agreement analysis
└── ollama_integration.py       🔗 Model interface

📁 /system/                     ⚙️ Configuration
├── config.py                   📋 Settings
├── dynamic_config.py           🔄 Auto-config
├── main.py                     🎯 Core system
└── requirements.txt            📦 Dependencies

📁 /bin/                        💻 Executables  
├── launch.bat                  🖱️ Easy Windows launcher
├── launch_session_ui.bat       🎯 Session UI launcher
└── *.bat, *.sh                 🔧 Other scripts

📁 /docs/                       📚 Documentation
├── ORGANIZATION_COMPLETE.md    ✅ Structure guide
├── WORKING_SETUP.md           🔧 Setup guide
└── *.md                       📖 Other docs

📁 /logs/                       📜 Log files
📁 /scripts/                    🔧 Utilities & tests
📁 /ui/                         🎨 Alternative UIs
📁 /legacy/                     📦 Archived code
```

## ✨ Key Features

- ✅ **Only Small Models** - Under 4GB each (tinyllama, phi3:mini, gemma2:2b, llama3.2:3b)
- ✅ **True Model Persistence** - Models stay loaded between debates  
- ✅ **Max 3 Rounds** - Efficient, focused debates
- ✅ **Clean Interface** - Streamlit web UI
- ✅ **Windows Compatible** - No Unicode/encoding issues
- ✅ **Organized Structure** - Clear separation of concerns

## 🔧 Configuration

The system auto-configures using small models. Manual config in `/system/config.py` if needed.

**Recommended Models** (install with `ollama pull <model>`):
- `tinyllama:1.1b` - Ultra-fast, 1.1GB
- `phi3:mini` - Compact, 2.3GB  
- `gemma2:2b` - Efficient, 1.6GB
- `llama3.2:3b` - Balanced, 2GB

## 🎭 Usage

1. **Launch**: Double-click `bin\launch.bat` or run `streamlit run streamlit_app_session.py`
2. **Ask**: Enter your debate question
3. **Watch**: 3 AI agents debate the topic
4. **Results**: Get consensus analysis and summary

## 🏗️ Development

- **Backend**: Core logic in `/backend/`
- **System**: Settings in `/system/`  
- **Tests**: Utilities in `/scripts/`
- **Docs**: Guides in `/docs/`

---

## ✨ Modern Angular Features

### 🎨 **Beautiful Material Design UI**
- Clean, responsive interface with Angular Material components
- Real-time progress tracking with visual progress bars
- Tabbed results view for organized debate analysis
- Mobile-friendly responsive design

### 🚀 **Advanced Functionality** 
- **Real-time Updates**: Live debate progress with automatic polling
- **REST API**: Clean separation between frontend and backend
- **Session Management**: Persistent model loading and state
- **Error Handling**: User-friendly error messages and notifications
- **Expandable Results**: Collapsible rounds view for detailed analysis

### 🔧 **Developer Benefits**
- **FastAPI Backend**: Modern async Python REST API
- **Angular Frontend**: TypeScript, reactive forms, HTTP client
- **Hot Reload**: Development server with live updates
- **Production Ready**: Optimized builds served directly by FastAPI
- **API Documentation**: Automatic Swagger/OpenAPI docs at `/docs`

## 🎯 **Key Advantages Over Streamlit**

✅ **Better Performance**: Faster loading and smoother interactions  
✅ **Modern UI/UX**: Professional Material Design interface  
✅ **Mobile Responsive**: Works perfectly on phones and tablets  
✅ **Real-time Updates**: Live progress without page refreshes  
✅ **Better Error Handling**: User-friendly error messages  
✅ **API First**: RESTful design for easy integration  
✅ **Production Ready**: Optimized builds and professional deployment

---

**Clean, fast, and efficient AI debates with local models! 🎉**
