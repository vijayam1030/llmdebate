# 🔥 LLM Debate System - Organized Structure

## 📁 **New Folder Structure**

```
📦 LLM Debate System (Root)
├── 🚀 **Main Execution Files** (Keep in Root)
│   ├── streamlit_app_session.py      # ⭐ MAIN UI - True model persistence
│   ├── launch_session_ui.py          # Python launcher for session UI
│   ├── launch_session_ui.bat         # Windows launcher for session UI
│   ├── main.py                       # Core debate system
│   ├── config.py                     # Configuration
│   └── dynamic_config.py             # Dynamic model selection
│
├── 💻 **Backend** (Core Logic)
│   ├── agents.py                     # LangChain agents
│   ├── models.py                     # Data models
│   ├── debate_workflow.py            # LangGraph workflow
│   ├── consensus_engine.py           # Consensus analysis
│   └── ollama_integration.py         # Ollama integration
│
├── 🎨 **UI** (Alternative Interfaces)
│   ├── streamlit_app_robust.py       # External process UI (updated)
│   ├── streamlit_app_persistent.py   # Thread-based persistence
│   ├── streamlit_app_server.py       # Background server UI
│   ├── streamlit_app_simple.py       # Simple UI
│   ├── streamlit_app_ascii.py        # ASCII-only UI
│   └── streamlit_launcher.py         # UI launcher
│
├── 🛠️ **Scripts** (Utilities & Tests)
│   ├── run_small_debate.py           # CLI debate runner
│   ├── simple_launcher.py            # Simple CLI launcher
│   ├── check_models.py               # Model availability checker
│   ├── test_*.py                     # All test files
│   └── quick_test_3rounds.py         # Quick test script
│
└── 📚 **Legacy** (Old/Archive Files)
    ├── api.py                        # Old API
    ├── debate_server.py              # Old server
    └── run.py                        # Old runner
```

## 🚀 **Quick Start**

### **Option 1: Windows Launcher (Easiest)**
```cmd
# Double-click or run:
launch_session_ui.bat
```

### **Option 2: Direct Python**
```cmd
# From the root directory:
streamlit run streamlit_app_session.py
```

### **Option 3: Python Launcher**
```cmd
python launch_session_ui.py
```

## ⭐ **Recommended UI: `streamlit_app_session.py`**

This is the **BEST** option for model persistence:

✅ **True Model Persistence** - Models stay loaded between debates  
✅ **Session State** - No external processes or servers  
✅ **Simple & Reliable** - No complex dependencies  
✅ **Fast Subsequent Debates** - Models already loaded  
✅ **Memory Efficient** - Optimal resource usage  

## 🔧 **Alternative UIs (in `/ui/` folder)**

- **`streamlit_app_robust.py`** - External process (conflict-free but reloads models)
- **`streamlit_app_persistent.py`** - Thread-based persistence
- **`streamlit_app_server.py`** - Background server approach
- **`streamlit_app_simple.py`** - Basic UI without persistence

## 📋 **System Requirements**

- **Python 3.8+**
- **Ollama** running locally (`ollama serve`)
- **Small models installed** (under 4GB each):
  ```bash
  ollama pull llama3.2:3b
  ollama pull gemma2:2b
  ollama pull phi3:mini
  ollama pull tinyllama:1.1b
  ```

## 🏗️ **Benefits of New Structure**

1. **🎯 Clean Root** - Only essential files in main directory
2. **📁 Organized** - Logical grouping by function
3. **⭐ Best UI First** - Session UI prominently featured
4. **🔧 Easy Maintenance** - Clear separation of concerns
5. **🚀 Simple Launch** - One-click Windows launcher

## 💡 **Usage Tips**

- **Start with**: `launch_session_ui.bat` (Windows) or `streamlit run streamlit_app_session.py`
- **For CLI**: Use `python scripts/run_small_debate.py "your question"`
- **For testing**: Check files in `/scripts/` folder
- **For development**: Backend logic in `/backend/` folder

---

**🎯 Focus: Session-based UI provides the best experience with true model persistence!**
