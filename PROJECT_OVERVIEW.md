# LLM Debate System – Project Overview

## 1. Project Purpose
A modular, local-first AI debate system that lets users pose a question and watch three small LLM agents debate, orchestrated by a fourth agent. The system is designed for easy sharing (public URLs), robust error handling, and multi-user support.

---

## 2. Technologies Used
- **Python**: Core backend logic and orchestration
- **Ollama**: Local LLM model serving (tinyllama, phi3:mini, gemma2:2b, llama3.2:3b)
- **FastAPI**: REST API backend (for Angular UI)
- **Angular**: Modern web frontend (optional)
- **Gradio**: Alternative web UI with built-in public sharing
- **ngrok**: Tunneling for public URLs (FastAPI/Angular stack)
- **Streamlit**: (Legacy/simple UI)
- **dotenv**: Environment variable management

---

## 3. Application Entry Points
- **Gradio UI**: `python gradio_app.py`  
  - Public/shareable URL is shown in the terminal after launch.
- **FastAPI/Angular UI**: 
  - Backend: `python api/main.py` (or via Uvicorn)
  - Frontend: Angular build served by backend or via Angular dev server
  - Public URL via ngrok (if enabled)
- **Streamlit UI**: `streamlit run streamlit_app_session.py` (legacy/simple)

---

## 4. Main URLs
- **Gradio**:  
  - Local: `http://localhost:7860/`  
  - Public: (auto-generated, e.g. `https://xxxx.gradio.live/`)
- **FastAPI**:  
  - API root: `http://localhost:8000/api`  
  - Status: `http://localhost:8000/api/status`  
  - Debate: `http://localhost:8000/api/debate/start` (POST)
  - Angular UI: `http://localhost:8000/` (if built and served)
  - Public: (ngrok URL, e.g. `https://xxxx.ngrok-free.app/`)

---

## 5. Application Flow (Debate Process)

### (A) User Interaction
- User enters a debate question (and optionally max rounds) in the UI (Gradio or Angular).
- User clicks "Start Debate".

### (B) Backend Orchestration
- The backend initializes (if not already) and loads small LLM models.
- A unique debate session is created.
- For each round:
  1. **Each Debater Agent** receives the question and context, generates a response.
  2. **Orchestrator Agent** reviews all responses, analyzes consensus, and provides feedback.
  3. If consensus is not reached and max rounds not hit, the next round starts with updated context.
  4. If consensus is reached or max rounds hit, the orchestrator generates a final summary.
- All round data, responses, and consensus analysis are tracked in memory.

### (C) Results
- The UI displays:
  - Final summary
  - All rounds and agent responses
  - Consensus status
  - Total rounds

---

## 6. Data Flow Diagram

```
[User] --(question)--> [UI (Gradio/Angular)] --(API call)--> [Backend]
    [Backend] --(question/context)--> [Debater Agents (LLMs)]
    [Backend] <--(responses)-- [Debater Agents]
    [Backend] --(responses)--> [Orchestrator Agent (LLM)]
    [Backend] <--(feedback/consensus)-- [Orchestrator]
    [Backend] --(results)--> [UI]
    [UI] --(display)--> [User]
```

---

## 7. How Data is Passed Between Rounds
- Each round, the backend maintains a state object for the debate session:
  - Question
  - Current round number
  - All previous responses
  - Orchestrator feedback
  - Consensus status
- This state is updated after each round and passed as context to the next round's agents.
- When consensus is reached or rounds are exhausted, the orchestrator generates a final summary.

---

## 8. Multi-User & Sharing
- Each debate session is tracked by a unique ID.
- Multiple users can use the public URL simultaneously; each gets their own debate session.
- Gradio and ngrok both provide public URLs for easy sharing.

---

## 9. Error Handling & Robustness
- Backend always returns a summary, even if LLMs fail.
- UI always displays progress and results, even on error.
- ngrok/Gradio URLs are shown in the UI for easy sharing.

---

## 10. Extending or Customizing
- Add new agents or change personalities in `system/config.py`.
- Swap UI (Gradio, Angular, Streamlit) as needed.
- Use different LLMs by updating model config.

---

**For more details, see the README and code comments.**



(.venv) C:\Users\wanth\OneDrive\harry\ai\ml\python\llm debate>npm install -g cloudflared

added 1 package in 3s

(.venv) C:\Users\wanth\OneDrive\harry\ai\ml\python\llm debate>cloudflared tunnel --url http://localhost:4200
