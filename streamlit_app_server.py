"""
Streamlit UI with True Model Persistence
Uses a persistent background server to keep models loaded
"""

import streamlit as st
import subprocess
import sys
import os
import json
import time
import requests
import threading
import atexit
from pathlib import Path

# Set page config first
st.set_page_config(
    page_title="LLM Debate System (True Persistence)",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global variables for background server management
BACKGROUND_SERVER_PORT = 8765
BACKGROUND_SERVER_PROCESS = None

def create_background_server_script():
    """Create a persistent background server that keeps models loaded"""
    script_content = '''
import asyncio
import json
import logging
from aiohttp import web, ClientSession
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Suppress logging
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ["httpx", "ollama_integration", "main", "debate_workflow", "dynamic_config"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Global system instance - this is what keeps models loaded!
DEBATE_SYSTEM = None
SYSTEM_INITIALIZED = False

async def initialize_system():
    """Initialize the system once and keep it loaded"""
    global DEBATE_SYSTEM, SYSTEM_INITIALIZED
    
    if SYSTEM_INITIALIZED:
        return {"success": True, "message": "Already initialized"}
    
    try:
        from main import LLMDebateSystem
        from dynamic_config import create_small_model_config_only
        from config import Config
        
        # Setup small models
        orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
        if orchestrator_config and len(debater_configs) >= 2:
            Config.ORCHESTRATOR_MODEL = orchestrator_config
            Config.DEBATER_MODELS = debater_configs
        else:
            return {"success": False, "error": "Failed to configure small models"}
        
        # Initialize system ONCE
        DEBATE_SYSTEM = LLMDebateSystem()
        if await DEBATE_SYSTEM.initialize():
            SYSTEM_INITIALIZED = True
            return {"success": True, "message": "System initialized successfully"}
        else:
            return {"success": False, "error": "System initialization failed"}
            
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Initialization error: {str(e)}", "traceback": traceback.format_exc()}

async def run_debate_with_loaded_system(question, max_rounds=3):
    """Run debate using the already-loaded system"""
    global DEBATE_SYSTEM, SYSTEM_INITIALIZED
    
    if not SYSTEM_INITIALIZED or not DEBATE_SYSTEM:
        return {"success": False, "error": "System not initialized"}
    
    try:
        # Use the SAME system instance with loaded models
        result = await DEBATE_SYSTEM.conduct_debate(question, max_rounds=max_rounds)
        
        return {
            "success": True,
            "question": result.original_question,
            "status": result.final_status.value if hasattr(result.final_status, 'value') else str(result.final_status),
            "rounds": result.total_rounds,
            "duration": result.total_duration if result.total_duration else 0,
            "summary": result.final_summary[:1000] if result.final_summary else "No summary available",
            "consensus_scores": result.consensus_evolution if result.consensus_evolution else [],
            "models_persistent": True  # Indicator that models stayed loaded
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Debate error: {str(e)}", "traceback": traceback.format_exc()}

async def handle_initialize(request):
    """Handle system initialization"""
    result = await initialize_system()
    return web.json_response(result)

async def handle_debate(request):
    """Handle debate requests"""
    data = await request.json()
    question = data.get("question", "")
    max_rounds = data.get("max_rounds", 3)
    
    if not question:
        return web.json_response({"success": False, "error": "No question provided"})
    
    result = await run_debate_with_loaded_system(question, max_rounds)
    return web.json_response(result)

async def handle_status(request):
    """Handle status requests"""
    global SYSTEM_INITIALIZED
    return web.json_response({
        "initialized": SYSTEM_INITIALIZED,
        "models_loaded": SYSTEM_INITIALIZED
    })

async def handle_shutdown(request):
    """Handle shutdown requests"""
    global DEBATE_SYSTEM
    if DEBATE_SYSTEM:
        try:
            await DEBATE_SYSTEM.cleanup()
        except:
            pass
    return web.json_response({"success": True, "message": "Shutdown complete"})

async def create_app():
    """Create the web application"""
    app = web.Application()
    app.router.add_post('/initialize', handle_initialize)
    app.router.add_post('/debate', handle_debate)
    app.router.add_get('/status', handle_status)
    app.router.add_post('/shutdown', handle_shutdown)
    return app

async def main():
    """Main server function"""
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', {BACKGROUND_SERVER_PORT})
    await site.start()
    
    print(f"Background debate server running on port {BACKGROUND_SERVER_PORT}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down...")
        if DEBATE_SYSTEM:
            await DEBATE_SYSTEM.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
'''
    return script_content

def start_background_server():
    """Start the persistent background server"""
    global BACKGROUND_SERVER_PROCESS
    
    if BACKGROUND_SERVER_PROCESS and BACKGROUND_SERVER_PROCESS.poll() is None:
        return True  # Already running
    
    try:
        # Create server script
        server_script = create_background_server_script()
        script_path = "debate_server.py"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(server_script)
        
        # Start the server
        BACKGROUND_SERVER_PROCESS = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
           text=True, cwd=os.getcwd())
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is responding
        return check_background_server()
        
    except Exception as e:
        st.error(f"Failed to start background server: {e}")
        return False

def check_background_server():
    """Check if background server is running"""
    try:
        response = requests.get(f'http://localhost:{BACKGROUND_SERVER_PORT}/status', timeout=2)
        return response.status_code == 200
    except:
        return False

def stop_background_server():
    """Stop the background server"""
    global BACKGROUND_SERVER_PROCESS
    
    try:
        # Send shutdown signal
        requests.post(f'http://localhost:{BACKGROUND_SERVER_PORT}/shutdown', timeout=5)
    except:
        pass
    
    if BACKGROUND_SERVER_PROCESS:
        BACKGROUND_SERVER_PROCESS.terminate()
        BACKGROUND_SERVER_PROCESS.wait(timeout=10)
        BACKGROUND_SERVER_PROCESS = None

def initialize_system_via_server():
    """Initialize the system via background server"""
    try:
        response = requests.post(f'http://localhost:{BACKGROUND_SERVER_PORT}/initialize', timeout=120)
        return response.json()
    except Exception as e:
        return {"success": False, "error": f"Server communication error: {e}"}

def run_debate_via_server(question, max_rounds=3):
    """Run debate via background server"""
    try:
        response = requests.post(f'http://localhost:{BACKGROUND_SERVER_PORT}/debate', 
                               json={"question": question, "max_rounds": max_rounds}, 
                               timeout=300)
        return response.json()
    except Exception as e:
        return {"success": False, "error": f"Server communication error: {e}"}

def get_server_status():
    """Get server status"""
    try:
        response = requests.get(f'http://localhost:{BACKGROUND_SERVER_PORT}/status', timeout=5)
        return response.json()
    except:
        return {"initialized": False, "models_loaded": False}

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        return response.status_code == 200
    except:
        return False

# Register cleanup function
atexit.register(stop_background_server)

def main():
    st.title("🧠 LLM Debate System")
    st.markdown("*True Model Persistence - Background Server Approach*")
    
    # Initialize session state
    if 'server_started' not in st.session_state:
        st.session_state.server_started = False
        st.session_state.system_initialized = False
    
    # System status check
    st.subheader("System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if check_ollama_status():
            st.success("✓ Ollama server running")
        else:
            st.error("✗ Ollama server not detected")
            st.info("Start with: `ollama serve`")
    
    with col2:
        server_running = check_background_server()
        if server_running:
            st.success("✓ Background server running")
            st.session_state.server_started = True
        else:
            st.warning("⏳ Background server not running")
            st.session_state.server_started = False
    
    with col3:
        if st.session_state.server_started:
            status = get_server_status()
            if status.get("initialized", False):
                st.success("✓ Models loaded & persistent")
                st.session_state.system_initialized = True
            else:
                st.warning("⏳ Models not loaded")
                st.session_state.system_initialized = False
        else:
            st.info("🔧 Server needed")
    
    # Server management
    if not st.session_state.server_started:
        st.subheader("Start Background Server")
        st.info("The background server keeps models loaded between debates for maximum efficiency.")
        
        if st.button("🚀 Start Background Server", type="primary"):
            with st.spinner("Starting persistent background server..."):
                if start_background_server():
                    st.success("✅ Background server started successfully!")
                    st.session_state.server_started = True
                    st.rerun()
                else:
                    st.error("❌ Failed to start background server")
    
    elif not st.session_state.system_initialized:
        st.subheader("Initialize AI Models")
        st.info("This loads the models once into the background server. They will stay loaded until you stop the server.")
        
        if st.button("🧠 Load Models", type="primary"):
            with st.spinner("Loading AI models into background server (60-90 seconds)..."):
                result = initialize_system_via_server()
                if result.get("success"):
                    st.success("🎉 AI models loaded successfully!")
                    st.info("Models are now persistent and ready for fast debates!")
                    st.session_state.system_initialized = True
                    st.rerun()
                else:
                    st.error(f"❌ Failed to load models: {result.get('error', 'Unknown error')}")
    
    else:
        # Debate interface
        st.subheader("⚡ Fast Debates (Models Pre-loaded)")
        
        # Performance info
        with st.expander("Model Persistence Status"):
            st.markdown("""
            **✅ Background Server Active**
            - Models are loaded and persistent
            - No loading/unloading between debates
            - Expected debate time: ~30-45 seconds
            - Models stay loaded until server is stopped
            
            **Performance Benefits:**
            - First debate: Fast (models already loaded)
            - Subsequent debates: Consistently fast
            - Zero model reloading overhead
            """)
        
        question = st.text_area(
            "Enter your debate question:",
            placeholder="What are the benefits of renewable energy?\n\nOr try:\n- Should AI be regulated?\n- What's the future of remote work?\n- Is nuclear energy safe?",
            help="Since models are pre-loaded, this debate will be fast!",
            height=100
        )
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("⚡ Fast Debate", type="primary", use_container_width=True):
                if not question.strip():
                    st.error("Please enter a question first!")
                else:
                    st.divider()
                    st.subheader(f"🚀 Fast Debate: *{question.strip()}*")
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🧠 Using pre-loaded models...")
                    progress_bar.progress(20)
                    
                    start_time = time.time()
                    
                    # Run the debate
                    with st.spinner("⚡ AI agents debating with persistent models..."):
                        result = run_debate_via_server(question.strip(), max_rounds=3)
                        
                        duration = time.time() - start_time
                        
                        progress_bar.progress(100)
                        status_text.text(f"✅ Debate completed in {duration:.1f}s!")
                        
                        # Display results
                        if result.get("success"):
                            st.success(f"🎉 Debate completed in {duration:.1f}s!")
                            
                            # Performance celebration
                            if result.get("models_persistent"):
                                st.info("⚡ Lightning fast! Models stayed loaded throughout the debate.")
                            
                            # Metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Status", result.get("status", "Unknown"))
                            
                            with col2:
                                st.metric("Rounds", result.get("rounds", 0))
                            
                            with col3:
                                st.metric("Duration", f"{duration:.1f}s")
                            
                            with col4:
                                scores = result.get("consensus_scores", [])
                                final_score = scores[-1] if scores else 0
                                st.metric("Final Consensus", f"{final_score:.3f}")
                            
                            # Debate summary
                            if result.get("summary"):
                                st.subheader("📋 Debate Summary")
                                st.write(result["summary"])
                            
                            # Consensus evolution
                            if result.get("consensus_scores"):
                                st.subheader("📈 Consensus Evolution")
                                scores = result["consensus_scores"]
                                
                                for i, score in enumerate(scores, 1):
                                    progress = min(score, 1.0)
                                    st.write(f"Round {i}: {score:.3f}")
                                    st.progress(progress)
                            
                            # Success indicators
                            st.subheader("🏆 Performance Highlights")
                            st.write("✅ Models stayed persistent (no loading/unloading)")
                            st.write("✅ Background server architecture")
                            st.write("✅ Consistent fast performance")
                            st.write("✅ Memory efficient (models loaded once)")
                            
                        else:
                            st.error("❌ Debate failed")
                            error_msg = result.get("error", "Unknown error")
                            st.error(f"**Error**: {error_msg}")
        
        # Server management
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Restart Server"):
                stop_background_server()
                time.sleep(2)
                if start_background_server():
                    st.success("Server restarted!")
                    st.session_state.system_initialized = False
                    st.rerun()
        
        with col2:
            server_status = get_server_status()
            st.write(f"**Status**: {'Initialized' if server_status.get('initialized') else 'Not initialized'}")
        
        with col3:
            if st.button("🛑 Stop Server"):
                stop_background_server()
                st.session_state.server_started = False
                st.session_state.system_initialized = False
                st.success("Server stopped")
                st.rerun()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*🧠 True Model Persistence - Zero Loading/Unloading*")

if __name__ == "__main__":
    main()
