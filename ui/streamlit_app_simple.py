"""
Simple Streamlit UI that uses the existing CLI scripts
Most reliable approach - just calls the working Python scripts
"""

import streamlit as st
import subprocess
import sys
import os
import json
import time

# Set page config first
st.set_page_config(
    page_title="🎯 LLM Debate System (CLI Wrapper)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def run_debate_cli(question):
    """Run debate using the existing run_small_debate.py script"""
    try:
        # Use the working run_small_debate.py script
        result = subprocess.run([
            sys.executable, 'run_small_debate.py', question
        ], capture_output=True, text=True, timeout=300, cwd=os.getcwd())
        
        if result.returncode == 0:
            return {
                "success": True,
                "output": result.stdout,
                "error": result.stderr
            }
        else:
            return {
                "success": False,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Debate timed out (5 minutes)"}
    except Exception as e:
        return {"success": False, "error": f"CLI execution error: {str(e)}"}

def check_files_exist():
    """Check if required files exist"""
    required_files = [
        'run_small_debate.py',
        'main.py', 
        'config.py',
        'dynamic_config.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    return missing_files

def check_ollama_status():
    """Check if Ollama is running"""
    try:
        result = subprocess.run([
            sys.executable, '-c',
            'import requests; print("OK" if requests.get("http://localhost:11434/api/tags", timeout=3).status_code == 200 else "FAIL")'
        ], capture_output=True, text=True, timeout=10)
        return result.stdout.strip() == "OK"
    except:
        return False

def main():
    st.title("🎯 LLM Debate System")
    st.markdown("*Simple CLI wrapper - Most reliable approach*")
    
    # System checks
    st.subheader("🔍 System Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📁 File Check:**")
        missing_files = check_files_exist()
        if not missing_files:
            st.success("✅ All required files found")
        else:
            st.error(f"❌ Missing files: {', '.join(missing_files)}")
            st.stop()
    
    with col2:
        st.write("**🌐 Ollama Check:**")
        if check_ollama_status():
            st.success("✅ Ollama server is running")
        else:
            st.error("❌ Ollama server not detected")
            st.info("Please start Ollama: `ollama serve`")
    
    # Configuration info
    with st.expander("📋 System Information"):
        st.markdown("""
        **🎯 This UI uses the proven CLI scripts:**
        - Calls `run_small_debate.py` directly (no import conflicts)
        - Uses existing small model configuration
        - Same functionality as CLI but with web interface
        - Large token limits: Orchestrator 2000, Debaters 800
        - Max 3 rounds per debate
        - Memory usage: ~5.3GB total
        """)
    
    # Debate interface
    st.subheader("🎭 Start a Debate")
    
    question = st.text_area(
        "Enter your debate question:",
        placeholder="What are the benefits of renewable energy?\n\nOr try:\n- Should AI be regulated?\n- What's the future of remote work?\n- Is nuclear energy safe?",
        help="Ask any question you'd like the AI debaters to discuss",
        height=100
    )
    
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        if st.button("🚀 Start Debate", type="primary", use_container_width=True):
            if not question.strip():
                st.error("Please enter a question first!")
            elif check_files_exist():
                st.error("Missing required files. Please run from the correct directory.")
            elif not check_ollama_status():
                st.error("Ollama server is not running. Please start it first.")
            else:
                st.divider()
                st.subheader(f"🎭 Debating: *{question.strip()}*")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔄 Starting debate via CLI...")
                progress_bar.progress(20)
                
                # Run the debate using CLI
                with st.spinner("🤔 AI agents are debating... (1-3 minutes)"):
                    result = run_debate_cli(question.strip())
                
                progress_bar.progress(100)
                status_text.text("✅ Debate process completed!")
                
                # Display results
                if result.get("success"):
                    st.success("🎉 Debate completed successfully!")
                    
                    # Show the output
                    if result.get("output"):
                        st.subheader("📄 Debate Output")
                        
                        # Try to format the output nicely
                        output = result["output"]
                        
                        # Look for key sections in the output
                        if "DEBATE SUMMARY" in output:
                            parts = output.split("DEBATE SUMMARY")
                            if len(parts) > 1:
                                st.subheader("🔄 Debate Process")
                                st.text(parts[0])
                                st.subheader("📋 Final Summary")
                                st.text("DEBATE SUMMARY" + parts[1])
                            else:
                                st.text(output)
                        else:
                            st.text(output)
                    
                    st.subheader("🎯 Key Features Demonstrated")
                    st.write("✅ CLI-based execution (most reliable)")
                    st.write("✅ Small models only (under 4GB each)")
                    st.write("✅ Max 3 rounds (efficient)")
                    st.write("✅ Large token limits (detailed responses)")
                    st.write("✅ No import/asyncio conflicts")
                    
                else:
                    st.error("❌ Debate failed")
                    error_msg = result.get("error", "Unknown error")
                    st.error(f"**Error**: {error_msg}")
                    
                    # Show CLI output for debugging
                    if result.get("output"):
                        with st.expander("📝 CLI Output (for debugging)"):
                            st.text(result["output"])
                    
                    if result.get("error") and result["error"] != error_msg:
                        with st.expander("⚠️ CLI Errors (for debugging)"):
                            st.text(result["error"])
                    
                    st.subheader("🔧 Troubleshooting")
                    st.write("1. **Check directory**: Make sure you're in the project folder")
                    st.write("2. **Test CLI directly**: Try `python run_small_debate.py \"test question\"`")
                    st.write("3. **Check Ollama**: Make sure `ollama serve` is running")
                    st.write("4. **Check models**: Ensure small models are installed:")
                    st.code("""
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama pull phi3:mini
ollama pull tinyllama:1.1b
                    """)

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("*🎯 LLM Debate System - CLI Wrapper (Most Reliable)*")

if __name__ == "__main__":
    main()
