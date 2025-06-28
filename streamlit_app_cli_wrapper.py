"""
Ultra-simple Streamlit UI for LLM Debate System
Directly calls the working CLI script as a subprocess
"""

import streamlit as st
import subprocess
import sys
import os
import time

# Set page config first
st.set_page_config(
    page_title="LLM Debate System - CLI Wrapper",
    page_icon=":fire:",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run_debate_cli(question):
    """Run debate using the working CLI script"""
    try:
        current_dir = os.getcwd()
        
        # Use the working CLI script directly
        if sys.platform.startswith('win'):
            process = subprocess.Popen([
                sys.executable, "run_small_debate.py", question
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               text=True, cwd=current_dir, encoding='utf-8', errors='replace',
               creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            process = subprocess.Popen([
                sys.executable, "run_small_debate.py", question
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               text=True, cwd=current_dir, encoding='utf-8', errors='replace')
        
        stdout, stderr = process.communicate(timeout=300)  # 5 minute timeout
        
        if process.returncode == 0:
            # Parse the CLI output to extract key information
            return parse_cli_output(stdout)
        else:
            return {"success": False, "error": f"CLI process failed: {stderr}", "stdout": stdout}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Debate timed out (5 minutes)"}
    except Exception as e:
        return {"success": False, "error": f"Process error: {str(e)}"}

def parse_cli_output(output):
    """Parse CLI output to extract debate information"""
    try:
        lines = output.split('\n')
        result = {"success": True}
        
        # Extract key information from CLI output
        for line in lines:
            if "Question:" in line:
                result["question"] = line.split("Question:")[-1].strip()
            elif "Status:" in line:
                result["status"] = line.split("Status:")[-1].strip()
            elif "Total Rounds:" in line:
                try:
                    result["rounds"] = int(line.split("Total Rounds:")[-1].strip())
                except:
                    result["rounds"] = 3
            elif "Duration:" in line:
                try:
                    duration_str = line.split("Duration:")[-1].strip().replace(" seconds", "")
                    result["duration"] = float(duration_str)
                except:
                    result["duration"] = 0
            elif "Orchestrator:" in line and "🧠" in line:
                result["orchestrator_model"] = line.split(":")[-1].strip()
            elif "Debaters:" in line and "👥" in line:
                debaters_str = line.split(":")[-1].strip()
                result["debater_models"] = [d.strip() for d in debaters_str.split(",")]
            elif "Consensus Evolution:" in line:
                # Extract consensus scores
                consensus_line = line.split("Consensus Evolution:")[-1].strip()
                scores = []
                for part in consensus_line.split("→"):
                    try:
                        score = float(part.strip())
                        scores.append(score)
                    except:
                        pass
                result["consensus_scores"] = scores
        
        # Extract summary (everything after "FINAL SUMMARY:")
        summary_start = output.find("FINAL SUMMARY:")
        if summary_start != -1:
            summary_section = output[summary_start:]
            # Find the end of summary (before "DEBATE ROUNDS:")
            summary_end = summary_section.find("DEBATE ROUNDS:")
            if summary_end != -1:
                summary = summary_section[len("FINAL SUMMARY:"):summary_end].strip()
            else:
                summary = summary_section[len("FINAL SUMMARY:"):].strip()
            result["summary"] = summary[:1000] if summary else "Summary extraction failed"
        else:
            result["summary"] = "No summary found in output"
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Output parsing error: {str(e)}", "raw_output": output[:1000]}

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        result = subprocess.run([
            'curl', '-s', 'http://localhost:11434/api/tags'
        ], capture_output=True, timeout=5)
        if result.returncode == 0:
            return True
    except:
        pass
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=3)
        return response.status_code == 200
    except:
        pass
    
    return False

def main():
    st.title("LLM Debate System")
    st.markdown("*CLI Wrapper - Maximum Compatibility*")
    
    # System status check
    st.subheader("System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if check_ollama_status():
            st.success("Ollama server is running")
        else:
            st.error("Ollama server not detected")
            st.info("Please start Ollama: `ollama serve`")
    
    with col2:
        st.info("Using direct CLI wrapper")
        st.info("Maximum compatibility mode")
    
    # Configuration info
    with st.expander("System Configuration"):
        st.markdown("""
        **LLM Debate System Features:**
        - **Models**: Small models only (under 4GB each)
        - **Orchestrator**: 2000 tokens (detailed analysis)
        - **Debaters**: 800 tokens each (comprehensive arguments)
        - **Max rounds**: 3 (efficient debates)
        - **Memory usage**: ~5.3GB total
        - **Execution**: Direct CLI script wrapper
        - **Compatibility**: Maximum (no subprocess conflicts)
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
                
                status_text.text("Starting debate process...")
                progress_bar.progress(10)
                
                time.sleep(1)
                status_text.text("Loading AI models...")
                progress_bar.progress(30)
                
                # Run the debate
                with st.spinner("AI agents are debating... (this may take 1-3 minutes)"):
                    result = run_debate_cli(question.strip())
                
                progress_bar.progress(100)
                status_text.text("Debate completed!")
                
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
                    if debaters:
                        st.write(f"**Debaters**: {', '.join(debaters)}")
                    
                    # Debate summary
                    if result.get("summary"):
                        st.subheader("Debate Summary")
                        st.write(result["summary"])
                        
                        if len(result["summary"]) >= 1000:
                            st.info("Summary truncated for display. Full details available in CLI logs.")
                    
                    # Consensus evolution
                    if result.get("consensus_scores"):
                        st.subheader("Consensus Evolution")
                        scores = result["consensus_scores"]
                        
                        for i, score in enumerate(scores, 1):
                            progress = min(score, 1.0)
                            st.write(f"Round {i}: {score:.3f}")
                            st.progress(progress)
                    
                    # Success indicators
                    st.subheader("System Performance")
                    st.write("- Direct CLI execution (maximum compatibility)")
                    st.write("- Small models only (memory efficient)")
                    st.write("- Large token limits (detailed responses)")
                    st.write("- Max 3 rounds (time efficient)")
                    
                else:
                    st.error("Debate failed")
                    error_msg = result.get("error", "Unknown error")
                    st.error(f"**Error**: {error_msg}")
                    
                    # Show debugging info if available
                    if result.get("stdout"):
                        with st.expander("CLI Output (for debugging)"):
                            st.code(result["stdout"][:2000])  # Limit display
                    
                    if result.get("raw_output"):
                        with st.expander("Raw Output (for debugging)"):
                            st.code(result["raw_output"])
                    
                    st.subheader("Troubleshooting")
                    st.write("1. **Check Ollama**: Make sure `ollama serve` is running")
                    st.write("2. **Check models**: Ensure small models are installed:")
                    st.code("""
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama pull phi3:mini
ollama pull tinyllama:1.1b
                    """)
                    st.write("3. **Test CLI**: Try `python run_small_debate.py \"your question\"`")

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*LLM Debate System - Direct CLI Wrapper for Maximum Compatibility*")

if __name__ == "__main__":
    main()
