"""
Streamlit UI with Simple Model Persistence
Uses a simple persistent process with file-based communication
"""

import streamlit as st
import subprocess
import sys
import os
import json
import time
import psutil
from pathlib import Path

# Set page config first
st.set_page_config(
    page_title="LLM Debate System (Simple Persistence)",
    page_icon="🔋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration
PERSISTENT_PROCESS_FILE = "debate_process.pid"
COMMAND_FILE = "debate_command.json"
RESULT_FILE = "debate_result.json"
STATUS_FILE = "debate_status.json"

def create_persistent_worker_script():
    """Create a simple persistent worker that keeps models loaded"""
    script_content = '''
import asyncio
import json
import time
import os
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# File paths
COMMAND_FILE = "debate_command.json"
RESULT_FILE = "debate_result.json"  
STATUS_FILE = "debate_status.json"

# Global system instance - keeps models loaded!
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
        import logging
        
        # Suppress logging
        logging.getLogger().setLevel(logging.CRITICAL)
        for logger_name in ["httpx", "ollama_integration", "main", "debate_workflow", "dynamic_config"]:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        
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
            "models_persistent": True
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Debate error: {str(e)}", "traceback": traceback.format_exc()}

def update_status(status_data):
    """Update status file"""
    with open(STATUS_FILE, 'w') as f:
        json.dump(status_data, f)

def write_result(result_data):
    """Write result to file"""
    with open(RESULT_FILE, 'w') as f:
        json.dump(result_data, f)

async def main():
    """Main worker loop"""
    print("Starting persistent debate worker...")
    
    # Initial status
    update_status({
        "initialized": False,
        "models_loaded": False,
        "last_update": time.time()
    })
    
    while True:
        try:
            # Check for commands
            if os.path.exists(COMMAND_FILE):
                with open(COMMAND_FILE, 'r') as f:
                    command = json.load(f)
                
                # Remove command file
                os.remove(COMMAND_FILE)
                
                if command["action"] == "initialize":
                    print("Initializing system...")
                    result = await initialize_system()
                    write_result(result)
                    
                    # Update status
                    update_status({
                        "initialized": SYSTEM_INITIALIZED,
                        "models_loaded": SYSTEM_INITIALIZED,
                        "last_update": time.time()
                    })
                    
                elif command["action"] == "debate":
                    print(f"Running debate: {command['question'][:50]}...")
                    result = await run_debate_with_loaded_system(
                        command["question"], 
                        command.get("max_rounds", 3)
                    )
                    write_result(result)
                    
                elif command["action"] == "shutdown":
                    print("Shutting down...")
                    if DEBATE_SYSTEM:
                        try:
                            await DEBATE_SYSTEM.cleanup()
                        except:
                            pass
                    break
            
            # Update status periodically
            update_status({
                "initialized": SYSTEM_INITIALIZED,
                "models_loaded": SYSTEM_INITIALIZED,
                "last_update": time.time()
            })
            
            await asyncio.sleep(0.5)  # Check for commands every 500ms
            
        except KeyboardInterrupt:
            print("Worker interrupted")
            break
        except Exception as e:
            print(f"Worker error: {e}")
            await asyncio.sleep(1)
    
    print("Worker stopped")

if __name__ == "__main__":
    asyncio.run(main())
'''
    return script_content

def start_persistent_worker():
    """Start the persistent worker process"""
    try:
        # Create worker script
        worker_script = create_persistent_worker_script()
        script_path = "debate_worker.py"
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(worker_script)
        
        # Start the worker
        process = subprocess.Popen([
            sys.executable, script_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
           text=True, cwd=os.getcwd())
        
        # Save PID
        with open(PERSISTENT_PROCESS_FILE, 'w') as f:
            f.write(str(process.pid))
        
        # Wait for worker to start
        time.sleep(2)
        
        return True
        
    except Exception as e:
        st.error(f"Failed to start worker: {e}")
        return False

def stop_persistent_worker():
    """Stop the persistent worker process"""
    try:
        if os.path.exists(PERSISTENT_PROCESS_FILE):
            with open(PERSISTENT_PROCESS_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Send shutdown command first
            send_command({"action": "shutdown"})
            time.sleep(2)
            
            # Kill process if still running
            try:
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
            except:
                pass
            
            os.remove(PERSISTENT_PROCESS_FILE)
    except:
        pass
    
    # Clean up files
    for file in [COMMAND_FILE, RESULT_FILE, STATUS_FILE]:
        if os.path.exists(file):
            os.remove(file)

def is_worker_running():
    """Check if worker process is running"""
    try:
        if not os.path.exists(PERSISTENT_PROCESS_FILE):
            return False
        
        with open(PERSISTENT_PROCESS_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        return psutil.pid_exists(pid)
    except:
        return False

def send_command(command_data):
    """Send command to worker process"""
    try:
        with open(COMMAND_FILE, 'w') as f:
            json.dump(command_data, f)
        return True
    except:
        return False

def wait_for_result(timeout=300):
    """Wait for result from worker"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if os.path.exists(RESULT_FILE):
            try:
                with open(RESULT_FILE, 'r') as f:
                    result = json.load(f)
                os.remove(RESULT_FILE)
                return result
            except:
                pass
        time.sleep(0.5)
    
    return {"success": False, "error": "Timeout waiting for result"}

def get_worker_status():
    """Get worker status"""
    try:
        if not os.path.exists(STATUS_FILE):
            return {"initialized": False, "models_loaded": False}
        
        with open(STATUS_FILE, 'r') as f:
            status = json.load(f)
        
        # Check if status is recent (within 5 seconds)
        if time.time() - status.get("last_update", 0) > 5:
            return {"initialized": False, "models_loaded": False}
        
        return status
    except:
        return {"initialized": False, "models_loaded": False}

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        return response.status_code == 200
    except:
        return False

def main():
    st.title("🔋 LLM Debate System")
    st.markdown("*Simple Model Persistence - File-based Communication*")
    
    # Initialize session state
    if 'worker_started' not in st.session_state:
        st.session_state.worker_started = False
    
    # Auto-detect worker status
    worker_running = is_worker_running()
    if worker_running != st.session_state.worker_started:
        st.session_state.worker_started = worker_running
    
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
        if st.session_state.worker_started and worker_running:
            st.success("✓ Worker process running")
        else:
            st.warning("⏳ Worker process not running")
    
    with col3:
        if st.session_state.worker_started:
            status = get_worker_status()
            if status.get("models_loaded", False):
                st.success("✓ Models loaded & persistent")
            else:
                st.warning("⏳ Models not loaded")
        else:
            st.info("🔧 Worker needed")
    
    # Worker management
    if not st.session_state.worker_started or not worker_running:
        st.subheader("Start Worker Process")
        st.info("The worker process keeps models loaded between debates for maximum efficiency.")
        
        if st.button("🚀 Start Worker", type="primary"):
            with st.spinner("Starting persistent worker process..."):
                if start_persistent_worker():
                    st.success("✅ Worker started successfully!")
                    st.session_state.worker_started = True
                    st.rerun()
                else:
                    st.error("❌ Failed to start worker")
    
    else:
        status = get_worker_status()
        
        if not status.get("initialized", False):
            st.subheader("Initialize AI Models")
            st.info("This loads the models once into the worker process. They will stay loaded until you stop the worker.")
            
            if st.button("🧠 Load Models", type="primary"):
                with st.spinner("Loading AI models into worker (60-90 seconds)..."):
                    if send_command({"action": "initialize"}):
                        result = wait_for_result(120)
                        if result.get("success"):
                            st.success("🎉 AI models loaded successfully!")
                            st.info("Models are now persistent and ready for fast debates!")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to load models: {result.get('error', 'Unknown error')}")
                    else:
                        st.error("❌ Failed to send initialization command")
        
        else:
            # Debate interface
            st.subheader("⚡ Fast Debates (Models Pre-loaded)")
            
            # Performance info
            with st.expander("Model Persistence Status"):
                st.markdown("""
                **✅ Worker Process Active**
                - Models are loaded and persistent
                - No loading/unloading between debates
                - Expected debate time: ~30-45 seconds
                - Models stay loaded until worker is stopped
                
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
                        
                        # Send debate command
                        command = {
                            "action": "debate",
                            "question": question.strip(),
                            "max_rounds": 3
                        }
                        
                        with st.spinner("⚡ AI agents debating with persistent models..."):
                            if send_command(command):
                                result = wait_for_result(300)
                                
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
                                    st.write("✅ File-based communication")
                                    st.write("✅ Consistent fast performance")
                                    st.write("✅ Memory efficient (models loaded once)")
                                    
                                else:
                                    st.error("❌ Debate failed")
                                    error_msg = result.get("error", "Unknown error")
                                    st.error(f"**Error**: {error_msg}")
                            else:
                                st.error("❌ Failed to send debate command")
            
            # Worker management
            st.divider()
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Restart Worker"):
                    stop_persistent_worker()
                    time.sleep(2)
                    if start_persistent_worker():
                        st.success("Worker restarted!")
                        st.rerun()
            
            with col2:
                worker_status = get_worker_status()
                st.write(f"**Status**: {'Initialized' if worker_status.get('initialized') else 'Not initialized'}")
            
            with col3:
                if st.button("🛑 Stop Worker"):
                    stop_persistent_worker()
                    st.session_state.worker_started = False
                    st.success("Worker stopped")
                    st.rerun()

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*🔋 Simple Model Persistence - File-based Communication*")

if __name__ == "__main__":
    main()
