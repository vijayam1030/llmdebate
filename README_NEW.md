# 🎯 LLM Debate System (Small Models Only)

**A clean, organized AI debate system using only small local Ollama models (<4GB each)**

## 🚀 Quick Start

### **Windows (Easiest)**
```bash
# Double-click:
bin\launch.bat

# Or from command line:
streamlit run streamlit_app_session.py
```

### **Any Platform**
```bash
# Install dependencies:
pip install -r config/requirements.txt

# Run the web interface:
streamlit run streamlit_app_session.py
```

## 📁 Project Structure

```
📁 Root (Clean!)
├── streamlit_app_session.py    ⭐ Main web interface
├── README.md                   📖 This file
├── .env                        🔧 Environment config
└── .gitignore

📁 /backend/                    🔧 Core system logic
├── agents.py                   🤖 AI agents
├── models.py                   📊 Data models  
├── debate_workflow.py          🔄 Debate flow
├── consensus_engine.py         🎯 Agreement analysis
└── ollama_integration.py       🔗 Model interface

📁 /config/                     ⚙️ Configuration
├── config.py                   📋 Settings
├── dynamic_config.py           🔄 Auto-config
├── main.py                     🎯 Core system
├── requirements.txt            📦 Dependencies
└── launch_session_ui.py        🚀 Python launcher

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

The system auto-configures using small models. Manual config in `/config/config.py` if needed.

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
- **Config**: Settings in `/config/`  
- **Tests**: Utilities in `/scripts/`
- **Docs**: Guides in `/docs/`

---

## 🛠️ Troubleshooting: ngrok/Public URL Stops Working

If your public (ngrok) URL stops working after some time, but the local URL (http://localhost:...) still works, this is expected behavior for free ngrok tunnels. Free ngrok tunnels automatically expire after 1-2 hours.

**What to do:**
1. **Restart ngrok:**
   - Close the ngrok window or stop the ngrok process.
   - Restart ngrok using your usual command or script.
   - Copy the new public URL and update it in the UI if needed.
2. **Why this happens:**
   - Free ngrok accounts have time-limited tunnels. This is not a bug in the debate system.
3. **Persistent URLs:**
   - For always-on, unchanging URLs, consider upgrading to a paid ngrok plan or using alternatives like [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) or [localtunnel](https://github.com/localtunnel/localtunnel).

**Tip:** If you share the ngrok URL, let users know it may change if the tunnel restarts.

---

**Clean, fast, and efficient AI debates with local models! 🎉**
