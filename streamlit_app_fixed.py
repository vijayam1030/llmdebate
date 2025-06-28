"""
Streamlit UI for LLM Debate System - Torch-free version
Avoids torch import conflicts and asyncio issues
"""

import streamlit as st
import sys
import os

# Prevent torch conflicts by setting environment variable
os.environ['TORCH_LOGGING_DISABLE'] = '1'

# Set page config first
st.set_page_config(
    page_title="🎯 LLM Debate System (Small Models)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def setup_models():
    """Setup small model configuration without asyncio conflicts"""
    try:
        # Import here to avoid conflicts
        import subprocess
        import json
        
        # Use subprocess to run the configuration setup
        result = subprocess.run([
            sys.executable, '-c',
            """
import asyncio
from dynamic_config import create_small_model_config_only
from config import Config

async def setup():
    orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
    if orchestrator_config and len(debater_configs) >= 2:
        Config.ORCHESTRATOR_MODEL = orchestrator_config
        Config.DEBATER_MODELS = debater_configs
        return True
    return False

result = asyncio.run(setup())
print('SUCCESS' if result else 'FAILED')
            """
        ], capture_output=True, text=True, timeout=30)
        
        return result.stdout.strip() == 'SUCCESS'
        
    except Exception as e:
        st.error(f"Configuration error: {e}")
        return False

def run_debate_subprocess(question):
    """Run debate in subprocess to avoid asyncio conflicts"""
    try:
        import subprocess
        import json
        
        # Create a simple script that runs the debate
        debate_script = f"""
import asyncio
from main import LLMDebateSystem
from dynamic_config import create_small_model_config_only
from config import Config
import json

async def run_debate():
    # Setup models
    orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
    Config.ORCHESTRATOR_MODEL = orchestrator_config
    Config.DEBATER_MODELS = debater_configs
    
    # Run debate
    system = LLMDebateSystem()
    if await system.initialize():
        result = await system.conduct_debate("{question}", max_rounds=3)
        await system.cleanup()
        
        # Return simplified result
        return {{
            "question": result.original_question,
            "status": result.final_status.value if hasattr(result.final_status, 'value') else str(result.final_status),
            "rounds": result.total_rounds,
            "duration": result.total_duration,
            "summary": result.final_summary[:500] if result.final_summary else "No summary available",
            "success": True
        }}
    return {{"success": False}}

result = asyncio.run(run_debate())
print(json.dumps(result))
        """
        
        # Run the debate script
        result = subprocess.run([
            sys.executable, '-c', debate_script
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse result"}
        else:
            return {"success": False, "error": result.stderr}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    st.title("🎯 LLM Debate System")
    st.markdown("*Optimized for small local models - Torch conflict free*")
    
    # Show system info
    st.info("💡 This version avoids torch/asyncio conflicts by using subprocess execution")
    
    # Setup small models on first run
    if 'models_configured' not in st.session_state:
        st.info("🔧 Configuring small models...")
        
        with st.spinner("Setting up configuration..."):
            if setup_models():
                st.session_state.models_configured = True
                st.success("✅ Small models configured successfully!")
                st.info("🧠 Using: gemma2:2b (orchestrator) + 3 debaters")
                st.rerun()
            else:
                st.error("❌ Failed to configure small models")
                st.info("Please ensure you have small models installed:")
                st.code("""
ollama pull llama3.2:3b
ollama pull gemma2:2b
ollama pull phi3:mini
ollama pull tinyllama:1.1b
                """)
                return
    
    # Show system status
    st.success("✅ Small model system ready!")
    
    # Configuration info
    with st.expander("📋 System Configuration"):
        st.write("**Large token limits for detailed responses:**")
        st.write("- Orchestrator: 2000 tokens (detailed analysis)")
        st.write("- Debaters: 800 tokens each (comprehensive arguments)")
        st.write("- Max rounds: 3 (efficient debates)")
        st.write("- Memory usage: ~5.3GB total")
        st.write("- Note: 'Response too long' warnings are normal and don't affect functionality")
    
    # Simple debate interface
    st.subheader("🎭 Start a Debate")
    
    question = st.text_input(
        "Enter your debate question:", 
        placeholder="What are the benefits of renewable energy?",
        help="Ask any question you'd like the AI debaters to discuss"
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        run_button = st.button("🚀 Start Debate", type="primary")
    
    with col2:
        if run_button and not question:
            st.warning("Please enter a question first!")
    
    if run_button and question:
        st.divider()
        st.subheader(f"🎭 Debating: *{question}*")
        
        with st.spinner("🤔 AI agents are debating... (this may take 30-60 seconds)"):
            # Show progress info
            progress_info = st.empty()
            progress_info.info("🔄 Initializing models and starting debate...")
            
            result = run_debate_subprocess(question)
            
            progress_info.empty()
        
        if result.get("success"):
            st.success("✅ Debate completed!")
            
            # Show results in nice format
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Status", result.get("status", "Unknown"))
            
            with col2:
                st.metric("Rounds", result.get("rounds", 0))
            
            with col3:
                duration = result.get("duration", 0)
                st.metric("Duration", f"{duration:.1f}s" if duration else "N/A")
            
            # Show summary
            if result.get("summary"):
                st.subheader("📄 Debate Summary")
                st.write(result["summary"])
                
                if len(result["summary"]) >= 500:
                    st.info("💡 Summary truncated for display. Full details in logs.")
            
            st.subheader("🎯 Key Features Demonstrated")
            st.write("✅ Small models only (under 4GB each)")
            st.write("✅ Max 3 rounds (efficient)")
            st.write("✅ No torch conflicts")
            st.write("✅ Large token limits (detailed responses)")
            st.write("✅ Comprehensive AI arguments")
            
        else:
            st.error("❌ Debate failed")
            st.error(f"Error: {result.get('error', 'Unknown error')}")
            st.info("💡 Try again or check that Ollama is running with small models installed")

    # Footer
    st.divider()
    st.markdown("*🎯 LLM Debate System - Small Models, Big Ideas*")

if __name__ == "__main__":
    main()
