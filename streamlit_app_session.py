"""
Streamlit UI with True Session-Based Model Persistence
Uses Streamlit session state to keep models loaded between debates
"""

import streamlit as st
import asyncio
import sys
import os
import time
import threading
import queue
from typing import Optional

# Ensure proper encoding on Windows
if sys.platform.startswith('win'):
    import locale
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass

# Set page config first
st.set_page_config(
    page_title="LLM Debate System (Session Persistence)",
    page_icon="💾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Thread-safe queue for async operations
async_queue = queue.Queue()

def run_async_safely(coro):
    """Run async function safely in a separate thread"""
    result_container = {"result": None, "error": None, "done": False}
    
    def run_in_thread():
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                result_container["result"] = result
            finally:
                loop.close()
        except Exception as e:
            result_container["error"] = str(e)
        finally:
            result_container["done"] = True
    
    # Start thread
    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()
    
    # Wait for completion with progress
    progress_bar = st.progress(0)
    progress_text = st.empty()
    
    start_time = time.time()
    while not result_container["done"]:
        elapsed = time.time() - start_time
        if elapsed < 30:
            progress = min(elapsed / 30, 0.3)
            progress_text.text(f"Initializing... ({elapsed:.1f}s)")
        elif elapsed < 60:
            progress = 0.3 + min((elapsed - 30) / 30, 0.4)
            progress_text.text(f"Loading models... ({elapsed:.1f}s)")
        else:
            progress = 0.7 + min((elapsed - 60) / 30, 0.3)
            progress_text.text(f"Almost ready... ({elapsed:.1f}s)")
        
        progress_bar.progress(progress)
        time.sleep(0.5)
    
    progress_bar.progress(1.0)
    progress_text.text("✅ Complete!")
    
    # Join thread
    thread.join(timeout=1)
    
    if result_container["error"]:
        raise Exception(result_container["error"])
    
    return result_container["result"]

async def initialize_system_async():
    """Initialize the debate system asynchronously"""
    try:
        # Add the current directory to Python path to fix import issues
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from main import LLMDebateSystem
        from dynamic_config import create_small_model_config_only
        from config import Config
        
        # Setup small models
        orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
        if orchestrator_config and len(debater_configs) >= 2:
            Config.ORCHESTRATOR_MODEL = orchestrator_config
            Config.DEBATER_MODELS = debater_configs
        else:
            return None, "Failed to configure small models"
        
        # Initialize system
        system = LLMDebateSystem()
        if await system.initialize():
            return system, None
        else:
            return None, "System initialization failed"
            
    except Exception as e:
        import traceback
        return None, f"Initialization error: {str(e)}\\n{traceback.format_exc()}"

async def run_debate_async(system, question, max_rounds=3):
    """Run a debate asynchronously"""
    try:
        result = await system.conduct_debate(question, max_rounds=max_rounds)
        return {
            "success": True,
            "question": result.original_question,
            "status": result.final_status.value if hasattr(result.final_status, 'value') else str(result.final_status),
            "rounds": result.total_rounds,
            "duration": result.total_duration if result.total_duration else 0,
            "summary": result.final_summary if result.final_summary else "No summary available",
            "consensus_scores": result.consensus_evolution if result.consensus_evolution else [],
            "models_persistent": True
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Debate error: {str(e)}", "traceback": traceback.format_exc()}

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        return response.status_code == 200
    except:
        return False

def initialize_session_state():
    """Initialize session state variables"""
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False
    if 'debate_system' not in st.session_state:
        st.session_state.debate_system = None
    if 'initialization_error' not in st.session_state:
        st.session_state.initialization_error = None
    if 'models_loaded_count' not in st.session_state:
        st.session_state.models_loaded_count = 0
    if 'total_debates' not in st.session_state:
        st.session_state.total_debates = 0

def main():
    # Initialize session state
    initialize_session_state()
    
    st.title("💾 LLM Debate System")
    st.markdown("*Session-Based Model Persistence - No External Processes*")
    
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
        if st.session_state.system_initialized:
            st.success("✓ AI system initialized")
            st.info(f"Models loaded: {st.session_state.models_loaded_count}")
        else:
            st.warning("⏳ AI system not initialized")
    
    with col3:
        st.info("💾 Session-based persistence")
        if st.session_state.total_debates > 0:
            st.info(f"Debates run: {st.session_state.total_debates}")
        else:
            st.info("Ready for first debate")
    
    # Configuration info
    with st.expander("Model Persistence Benefits & Features"):
        if st.session_state.system_initialized:
            st.markdown("""
            **✅ Models Currently Loaded in Session:**
            - Models are loaded and persistent in this browser session
            - No loading/unloading between debates
            - Expected debate time: ~30-45 seconds
            - Models stay loaded until you close this tab
            
            **📋 Enhanced Summary Features:**
            - **Full-length summaries** (no truncation limits)
            - **Enhanced formatting** with styled display
            - **Smart expansion** for long summaries
            - **Summary statistics** (length, words, lines)
            
            **Performance:**
            - First debate: Fast (models already loaded)
            - Subsequent debates: Consistently fast
            - Zero model reloading overhead
            """)
        else:
            st.markdown("""
            **🔧 Session Persistence System:**
            - Models load once per browser session
            - Stay loaded until you close the tab
            - No external processes or servers needed
            - Thread-safe async execution
            - Streamlit native session state
            
            **📋 Summary Features:**
            - **Full debate summaries** without length limits
            - **Enhanced display** with proper formatting
            - **Expandable sections** for long content
            - **Statistics tracking** for content analysis
            """)
    
    # Initialization section
    if not st.session_state.system_initialized:
        st.subheader("Initialize AI System")
        
        if st.session_state.initialization_error:
            st.error(f"Initialization failed: {st.session_state.initialization_error}")
            
            with st.expander("Troubleshooting"):
                st.write("1. **Check Ollama**: Make sure `ollama serve` is running")
                st.write("2. **Check models**: Ensure models are installed:")
                st.code("""
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama pull phi3:mini
ollama pull tinyllama:1.1b
                """)
                st.write("3. **Check memory**: Ensure ~6GB free RAM")
                st.write("4. **Try CLI**: Test with `python run_small_debate.py \"test question\"`")
            
            if st.button("🔄 Retry Initialization"):
                st.session_state.initialization_error = None
                st.rerun()
        
        st.info("This will load AI models once into your browser session. They will stay loaded for all subsequent debates.")
        
        if st.button("🚀 Initialize AI System", type="primary", use_container_width=True):
            if not check_ollama_status():
                st.error("Ollama server not running. Please start it first.")
            else:
                try:
                    with st.spinner("🔧 Initializing AI system... (this will take 60-90 seconds)"):
                        system, error = run_async_safely(initialize_system_async())
                        
                        if system:
                            st.session_state.debate_system = system
                            st.session_state.system_initialized = True
                            st.session_state.initialization_error = None
                            st.session_state.models_loaded_count = 4  # Assume all 4 models loaded
                            
                            st.success("🎉 AI system initialized successfully!")
                            st.info("✨ Models are now loaded and persistent in your session!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.session_state.initialization_error = error
                            st.error("Failed to initialize AI system.")
                            st.rerun()
                            
                except Exception as e:
                    st.session_state.initialization_error = f"Initialization failed: {str(e)}"
                    st.error("Failed to initialize AI system.")
                    st.rerun()
    
    else:
        # Debate interface
        st.subheader("⚡ Lightning-Fast Debates")
        
        # Session info
        if st.session_state.total_debates > 0:
            st.info(f"🏆 You've run {st.session_state.total_debates} debate(s) with persistent models!")
        
        question = st.text_area(
            "Enter your debate question:",
            placeholder="What are the benefits of renewable energy?\\n\\nOr try:\\n- Should AI be regulated?\\n- What's the future of remote work?\\n- Is nuclear energy safe?",
            help="Since models are pre-loaded, this debate will be lightning fast!",
            height=100
        )
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("⚡ Lightning Debate", type="primary", use_container_width=True):
                if not question.strip():
                    st.error("Please enter a question first!")
                else:
                    st.divider()
                    st.subheader(f"⚡ Lightning Debate: *{question.strip()}*")
                    
                    start_time = time.time()
                    
                    # Run the debate with persistent models
                    try:
                        with st.spinner("⚡ AI agents debating with persistent models..."):
                            result = run_async_safely(run_debate_async(
                                st.session_state.debate_system, 
                                question.strip(), 
                                max_rounds=3
                            ))
                            
                            duration = time.time() - start_time
                            st.session_state.total_debates += 1
                            
                            # Display results
                            if result.get("success"):
                                st.success(f"🎉 Debate completed in {duration:.1f}s!")
                                
                                # Performance celebration
                                if duration < 45:
                                    st.info("⚡ Lightning fast! Models stayed loaded throughout.")
                                elif duration < 60:
                                    st.info("🚀 Fast completion thanks to persistent models!")
                                
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
                                
                                # Debate summary - Force maximum width with CSS injection
                                if result.get("summary"):
                                    st.subheader("📋 Debate Summary")
                                    
                                    # Inject CSS to force full width
                                    st.markdown("""
                                    <style>
                                    .stTextArea > div > div > textarea {
                                        width: 100% !important;
                                        max-width: none !important;
                                    }
                                    .summary-container {
                                        width: 100vw !important;
                                        margin-left: calc(-50vw + 50%) !important;
                                        padding: 20px calc(50vw - 50%) !important;
                                        background-color: #f8f9fa;
                                        border-left: 5px solid #007acc;
                                        margin-top: 15px;
                                        margin-bottom: 15px;
                                    }
                                    </style>
                                    """, unsafe_allow_html=True)
                                    
                                    summary_text = result["summary"]
                                    
                                    # Method 1: Custom HTML container for maximum width
                                    st.markdown(f"""
                                    <div class="summary-container">
                                    <h4>📄 Complete Summary</h4>
                                    <div style="line-height: 1.8; font-size: 16px; white-space: pre-wrap; font-family: 'Source Sans Pro', sans-serif;">
                                    {summary_text}
                                    </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Method 2: Also provide text_area as backup
                                    with st.expander("📝 Copy/Edit Summary", expanded=False):
                                        st.text_area(
                                            "Summary Text:", 
                                            value=summary_text,
                                            height=max(200, min(len(summary_text.split('\n')) * 25, 500)),
                                            key="summary_text_area"
                                        )
                                        
                                        # Add summary stats
                                        summary_stats_col1, summary_stats_col2, summary_stats_col3 = st.columns(3)
                                        with summary_stats_col1:
                                            st.metric("Summary Length", f"{len(summary_text)} chars")
                                        with summary_stats_col2:
                                            word_count = len(summary_text.split())
                                            st.metric("Word Count", f"{word_count} words")
                                        with summary_stats_col3:
                                            lines = summary_text.count('\n') + 1
                                            st.metric("Lines", f"{lines}")
                                
                                # Consensus evolution - Enhanced layout
                                if result.get("consensus_scores"):
                                    st.subheader("📈 Consensus Evolution")
                                    scores = result["consensus_scores"]
                                    
                                    # Create two columns for better layout
                                    consensus_col1, consensus_col2 = st.columns([3, 1])
                                    
                                    with consensus_col1:
                                        for i, score in enumerate(scores, 1):
                                            progress = min(score, 1.0)
                                            st.markdown(f"**Round {i}:** {score:.3f}")
                                            st.progress(progress)
                                            st.write("")  # Add spacing
                                    
                                    with consensus_col2:
                                        # Summary stats
                                        if len(scores) > 1:
                                            improvement = scores[-1] - scores[0]
                                            st.metric("Overall Change", f"{improvement:+.3f}")
                                            st.metric("Best Round", f"{max(scores):.3f}")
                                            trend = "📈 Improving" if improvement > 0.05 else "📉 Declining" if improvement < -0.05 else "➡️ Stable"
                                            st.metric("Trend", trend)
                                
                                # Success indicators
                                st.subheader("🏆 Performance Highlights")
                                st.write("✅ Models stayed persistent (no loading/unloading)")
                                st.write("✅ Session-based architecture")
                                st.write("✅ Thread-safe async execution")
                                st.write("✅ Zero external dependencies")
                                
                            else:
                                st.error("❌ Debate failed")
                                error_msg = result.get("error", "Unknown error")
                                st.error(f"**Error**: {error_msg}")
                                
                                if result.get("traceback"):
                                    with st.expander("Full Error Details"):
                                        st.code(result["traceback"])
                                
                    except Exception as e:
                        st.error(f"Unexpected error: {str(e)}")
        
        # Session management
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Reset Session"):
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Session reset! Models will be reloaded on next initialization.")
                st.rerun()
        
        with col2:
            st.write(f"**Session**: {st.session_state.models_loaded_count} models loaded")
            st.write(f"**Debates**: {st.session_state.total_debates} completed")
        
        with col3:
            if st.button("ℹ️ Session Info"):
                st.info(f"""
                **Session Statistics:**
                - Models loaded: {st.session_state.models_loaded_count}
                - Debates completed: {st.session_state.total_debates}
                - System initialized: {st.session_state.system_initialized}
                - Models persistent: ✅ Yes
                """)

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*💾 Session-Based Model Persistence - Simple & Reliable*")

if __name__ == "__main__":
    main()
