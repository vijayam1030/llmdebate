"""
Ultra-robust Streamlit UI for LLM Debate System
Completely avoids torch and asyncio conflicts by using external process execution
"""

import streamlit as st
import subprocess
import sys
import os
import json
import tempfile
import time

# Ensure proper encoding on Windows
if sys.platform.startswith('win'):
    import locale
    # Set console encoding to UTF-8 if possible
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass  # Fall back to default encoding

# Set page config first
st.set_page_config(
    page_title="LLM Debate System (Conflict-Free)",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_debate_script():
    """Create a standalone debate script with clean JSON output"""
    script_content = '''
import asyncio
import sys
import json
import logging
import os
import io
from contextlib import redirect_stdout, redirect_stderr

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Completely suppress all logging and print statements
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ["httpx", "ollama_integration", "main", "debate_workflow", "dynamic_config"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

async def run_debate(question, max_rounds=3):
    # Capture all output to avoid interference with JSON
    captured_output = io.StringIO()
    try:
        with redirect_stdout(captured_output), redirect_stderr(captured_output):
            from main import LLMDebateSystem
            from dynamic_config import create_small_model_config_only
            from config import Config
            
            # Setup small models            orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
            if orchestrator_config and len(debater_configs) >= 2:
                Config.ORCHESTRATOR_MODEL = orchestrator_config
                Config.DEBATER_MODELS = debater_configs
            else:
                return {"success": False, "error": "Failed to configure small models"}
            
            # Run debate
            system = LLMDebateSystem()
            if await system.initialize():
                result = await system.conduct_debate(question, max_rounds=max_rounds)
                # Note: Models stay loaded for efficiency - cleanup only on app exit
                
                # Extract key information - ASCII-safe output only
                return {
                    "success": True,
                    "question": result.original_question,
                    "status": result.final_status.value if hasattr(result.final_status, 'value') else str(result.final_status),
                    "rounds": result.total_rounds,
                    "duration": result.total_duration if result.total_duration else 0,
                    "summary": result.final_summary[:1000] if result.final_summary else "No summary available",
                    "consensus_scores": [round(r.consensus_score, 3) for r in result.rounds] if result.rounds else [],
                    "orchestrator_model": Config.ORCHESTRATOR_MODEL.model,
                    "debater_models": [d.model for d in Config.DEBATER_MODELS]
                }
            else:
                return {"success": False, "error": "System initialization failed"}
            
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Debate error: {str(e)}", "traceback": traceback.format_exc()}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No question provided"}), flush=True)
        sys.exit(1)
    
    question = " ".join(sys.argv[1:])
    result = asyncio.run(run_debate(question))
    # Output ONLY the JSON result - nothing else
    print(json.dumps(result, ensure_ascii=True, separators=(',', ':')), flush=True)
'''
    return script_content

def run_debate_external(question):
    """Run debate in completely separate process"""
    try:
        # Get the current working directory (where the debate system files are)
        current_dir = os.getcwd()
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(create_debate_script())
            script_path = f.name
        
        try:
            # Run the script with the question, ensuring correct working directory and encoding
            process = subprocess.Popen([
                sys.executable, script_path, question
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               text=True, cwd=current_dir, encoding='utf-8', errors='replace')
            
            stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
            
            if process.returncode == 0:
                try:
                    # Clean stdout and find the JSON output
                    lines = stdout.strip().split('\n')
                    json_result = None
                    
                    # Look for JSON starting from the last line (most likely to be our result)
                    for line in reversed(lines):
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                json_result = json.loads(line)
                                break
                            except:
                                continue
                    
                    if json_result:
                        return json_result
                    else:
                        # If no valid JSON found, try the entire stdout as JSON
                        try:
                            return json.loads(stdout.strip())
                        except:
                            return {"success": False, "error": "No valid JSON output found", "stdout": stdout[:500], "stderr": stderr[:500]}
                        
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"JSON decode error: {e}", "stdout": stdout[:500], "stderr": stderr[:500]}
            else:
                return {"success": False, "error": f"Process error: {stderr}", "stdout": stdout}
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(script_path)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Debate timed out (5 minutes)"}
    except Exception as e:
        return {"success": False, "error": f"External process error: {str(e)}"}

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        result = subprocess.run([
            'curl', '-s', 'http://localhost:11434/api/tags'
        ], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        try:
            # Alternative check using Python requests
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=3)
            return response.status_code == 200
        except:
            return False

def main():
    st.title("LLM Debate System")
    st.markdown("*Ultra-robust version - Completely conflict-free*")
    
    # System status check
    st.subheader("System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if check_ollama_status():
            st.success("✓ Ollama server is running")
        else:
            st.error("✗ Ollama server not detected")
            st.info("Please start Ollama: `ollama serve`")
    
    with col2:
        st.info("Using external process execution")
        st.info("No torch/asyncio conflicts")
    
    # Configuration info
    with st.expander("System Configuration"):
        st.markdown("""
        **LLM Debate System Features:**
        - **Models**: Small models only (under 4GB each)
        - **Orchestrator**: 2000 tokens (detailed analysis)
        - **Debaters**: 800 tokens each (comprehensive arguments)
        - **Max rounds**: 3 (efficient debates)
        - **Memory usage**: ~5.3GB total
        - **Execution**: External process (conflict-free)
        - **Token limits**: Large for detailed responses
        """)
    
    # Debate interface
    st.subheader("Start a Debate")
    
    question = st.text_area(
        "Enter your debate question:",
        placeholder="What are the benefits of renewable energy?\n\nOr try:\n- Should AI be regulated?\n- What's the future of remote work?\n- Is nuclear energy safe?",
        help="Ask any question you'd like the AI debaters to discuss. The more specific, the better!",
        height=100
    )
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("Start Debate", type="primary", use_container_width=True):
            if not question.strip():
                st.error("Please enter a question first!")
            elif not check_ollama_status():
                st.error("Ollama server is not running. Please start it first.")
            else:
                st.divider()
                st.subheader(f"Debating: *{question.strip()}*")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Starting external debate process...")
                progress_bar.progress(10)
                
                time.sleep(1)  # Brief pause for UI update
                status_text.text("Loading AI models...")
                progress_bar.progress(30)
                
                # Run the debate
                with st.spinner("AI agents are debating... (this may take 1-3 minutes)"):
                    result = run_debate_external(question.strip())
                
                progress_bar.progress(100)
                status_text.text("✓ Debate completed!")
                
                # Display results
                if result.get("success"):
                    st.success("Debate completed successfully!")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Status", result.get("status", "Unknown"))
                    
                    with col2:
                        st.metric("Rounds", result.get("rounds", 0))
                    
                    with col3:
                        duration = result.get("duration", 0)
                        st.metric("Duration", f"{duration:.1f}s" if duration else "N/A")
                    
                    with col4:
                        scores = result.get("consensus_scores", [])
                        final_score = scores[-1] if scores else 0
                        st.metric("Final Consensus", f"{final_score:.3f}")
                    
                    # Models used
                    st.subheader("Models Used")
                    orchestrator = result.get("orchestrator_model", "Unknown")
                    debaters = result.get("debater_models", [])
                    
                    st.write(f"**Orchestrator**: {orchestrator}")
                    st.write(f"**Debaters**: {', '.join(debaters)}")
                    
                    # Debate summary
                    if result.get("summary"):
                        st.subheader("Debate Summary")
                        st.write(result["summary"])
                        
                        if len(result["summary"]) >= 1000:
                            st.info("Summary truncated for display. Full details available in logs.")
                    
                    # Consensus evolution
                    if result.get("consensus_scores"):
                        st.subheader("Consensus Evolution")
                        scores = result["consensus_scores"]
                        
                        for i, score in enumerate(scores, 1):
                            progress = min(score, 1.0)  # Cap at 1.0 for display
                            st.write(f"Round {i}: {score:.3f}")
                            st.progress(progress)
                    
                    # Success indicators
                    st.subheader("System Performance")
                    st.write("✓ External process execution (no conflicts)")
                    st.write("✓ Small models only (memory efficient)")
                    st.write("✓ Large token limits (detailed responses)")
                    st.write("✓ Max 3 rounds (time efficient)")
                    
                else:
                    st.error("✗ Debate failed")
                    error_msg = result.get("error", "Unknown error")
                    st.error(f"**Error**: {error_msg}")
                    
                    # Show additional debugging info if available
                    if result.get("stdout"):
                        with st.expander("Process Output (for debugging)"):
                            st.code(result["stdout"])
                    
                    if result.get("stderr"):
                        with st.expander("Process Errors (for debugging)"):
                            st.code(result["stderr"])
                    
                    if result.get("traceback"):
                        with st.expander("Full Traceback (for debugging)"):
                            st.code(result["traceback"])
                    
                    st.subheader("Troubleshooting")
                    st.write("1. **Check Ollama**: Make sure `ollama serve` is running")
                    st.write("2. **Check models**: Ensure small models are installed:")
                    st.code("""
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama pull phi3:mini
ollama pull tinyllama:1.1b
                    """)
                    st.write("3. **Check system**: Ensure sufficient memory (~6GB free)")
                    st.write("4. **Check directory**: Make sure you're running from the correct folder")
                    st.write("5. **Try CLI**: Test with `python run_small_debate.py \"your question\"`")

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*LLM Debate System - Small Models, Big Ideas, Zero Conflicts*")

if __name__ == "__main__":
    main()
