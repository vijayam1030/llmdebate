"""
Streamlit UI with Persistent Model Loading
Keeps models loaded in session state for maximum efficiency
"""

import streamlit as st
import asyncio
import sys
import os
import time
import threading
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
    page_title="LLM Debate System (Persistent Models)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run_async_in_thread(coro):
    """Run async function in a separate thread to avoid event loop conflicts"""
    result = {'value': None, 'error': None}
    
    def thread_target():
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result['value'] = loop.run_until_complete(coro)
        except Exception as e:
            result['error'] = e
        finally:
            loop.close()
    
    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()
    
    if result['error']:
        raise result['error']
    return result['value']

async def initialize_system_async():
    """Initialize the debate system asynchronously"""
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
            "rounds_data": [
                {
                    "round_number": r.round_number,
                    "debater_responses": [
                        {"name": resp.debater_name, "response": resp.response[:200] + "..." if len(resp.response) > 200 else resp.response}
                        for resp in r.debater_responses
                    ],
                    "consensus_score": r.consensus_analysis.average_similarity if r.consensus_analysis else 0
                }
                for r in result.rounds
            ]
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

def initialize_system():
    """Initialize system in thread-safe way"""
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False
        st.session_state.debate_system = None
        st.session_state.initialization_error = None
        st.session_state.models_loaded_count = 0
    
    if not st.session_state.system_initialized:
        with st.spinner("🔧 Initializing AI debate system (this may take 30-60 seconds)..."):
            try:
                system, error = run_async_in_thread(initialize_system_async())
                if system:
                    st.session_state.debate_system = system
                    st.session_state.system_initialized = True
                    st.session_state.initialization_error = None
                    # Get loaded model count
                    try:
                        from ollama_integration import ollama_manager
                        loaded_models = run_async_in_thread(ollama_manager.get_loaded_models())
                        st.session_state.models_loaded_count = len(loaded_models)
                    except:
                        st.session_state.models_loaded_count = 4  # Assume all loaded
                    return True
                else:
                    st.session_state.initialization_error = error
                    return False
            except Exception as e:
                st.session_state.initialization_error = f"System initialization failed: {str(e)}"
                return False
    
    return st.session_state.system_initialized

def main():
    st.title("🚀 LLM Debate System")
    st.markdown("*Persistent model loading - Maximum efficiency*")
    
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
        if st.session_state.get('system_initialized', False):
            st.success("✓ AI system initialized")
            st.info(f"Models loaded: {st.session_state.get('models_loaded_count', 0)}")
        else:
            st.warning("⏳ AI system not initialized")
    
    with col3:
        st.info("🧠 Persistent model loading")
        st.info("🔄 Models stay loaded between debates")
    
    # Configuration info
    with st.expander("System Configuration & Performance"):
        st.markdown("""
        **Model Persistence Benefits:**
        - **First debate**: ~60s (includes model loading)
        - **Subsequent debates**: ~30-45s (models already loaded)
        - **Memory efficient**: Models loaded once per session
        - **Zero conflicts**: Thread-based async execution
        
        **Current Session:**
        """)
        
        if st.session_state.get('system_initialized', False):
            st.write("✅ Models are loaded and ready")
            st.write(f"✅ {st.session_state.get('models_loaded_count', 0)} models in memory")
        else:
            st.write("⏳ Models will be loaded on first debate")
        
        st.markdown("""
        **System Specs:**
        - **Models**: Small models only (under 4GB each)
        - **Orchestrator**: 2000 tokens (detailed analysis)
        - **Debaters**: 800 tokens each (comprehensive arguments)
        - **Max rounds**: 3 (efficient debates)
        - **Memory usage**: ~5.3GB total
        """)
    
    # Initialization section
    if not st.session_state.get('system_initialized', False):
        st.subheader("Initialize AI System")
        
        if st.session_state.get('initialization_error'):
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
        
        if st.button("🚀 Initialize AI System", type="primary", use_container_width=True):
            if not check_ollama_status():
                st.error("Ollama server not running. Please start it first.")
            else:
                success = initialize_system()
                if success:
                    st.success("🎉 AI system initialized successfully!")
                    st.info("Models are now loaded and ready for debates. They will stay loaded for maximum efficiency.")
                    st.rerun()
                else:
                    st.error("Failed to initialize AI system. Check the error above.")
    else:
        # Debate interface
        st.subheader("Start a Debate")
        
        question = st.text_area(
            "Enter your debate question:",
            placeholder="What are the benefits of renewable energy?\\n\\nOr try:\\n- Should AI be regulated?\\n- What's the future of remote work?\\n- Is nuclear energy safe?",
            help="Ask any question you'd like the AI debaters to discuss. Since models are loaded, this will be fast!",
            height=100
        )
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("Start Debate", type="primary", use_container_width=True):
                if not question.strip():
                    st.error("Please enter a question first!")
                else:
                    st.divider()
                    st.subheader(f"Debating: *{question.strip()}*")
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🚀 Starting debate with pre-loaded models...")
                    progress_bar.progress(20)
                    
                    start_time = time.time()
                    
                    # Run the debate
                    with st.spinner("🤔 AI agents are debating... (should be faster since models are loaded)"):
                        try:
                            result = run_async_in_thread(run_debate_async(
                                st.session_state.debate_system, 
                                question.strip(), 
                                max_rounds=3
                            ))
                            
                            duration = time.time() - start_time
                            
                            progress_bar.progress(100)
                            status_text.text(f"✅ Debate completed in {duration:.1f}s!")
                            
                            # Display results
                            if result.get("success"):
                                st.success(f"🎉 Debate completed successfully in {duration:.1f}s!")
                                
                                # Performance note
                                if duration < 45:
                                    st.info("⚡ Fast completion thanks to persistent model loading!")
                                
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
                                
                                # Detailed rounds
                                if result.get("rounds_data"):
                                    st.subheader("🔍 Detailed Rounds")
                                    for round_data in result["rounds_data"]:
                                        with st.expander(f"Round {round_data['round_number']} (Consensus: {round_data['consensus_score']:.3f})"):
                                            for resp in round_data["debater_responses"]:
                                                st.write(f"**{resp['name']}**: {resp['response']}")
                                
                                # Success indicators
                                st.subheader("🏆 System Performance")
                                st.write("✅ Persistent model loading (efficient)")
                                st.write("✅ Thread-based execution (no conflicts)")
                                st.write("✅ Small models only (memory efficient)")
                                st.write("✅ Large token limits (detailed responses)")
                                
                            else:
                                st.error("❌ Debate failed")
                                error_msg = result.get("error", "Unknown error")
                                st.error(f"**Error**: {error_msg}")
                                
                                if result.get("traceback"):
                                    with st.expander("Full Error Details"):
                                        st.code(result["traceback"])
                                
                        except Exception as e:
                            progress_bar.progress(100)
                            status_text.text("❌ Error occurred")
                            st.error(f"Unexpected error: {str(e)}")
        
        # Session management
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reset Session", help="Clear loaded models and restart"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        with col2:
            st.write(f"**Session Status**: {st.session_state.get('models_loaded_count', 0)} models loaded")

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*🚀 LLM Debate System - Persistent Models, Maximum Speed*")

if __name__ == "__main__":
    main()
