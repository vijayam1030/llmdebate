"""
Simple Streamlit launcher that uses small models and avoids torch import issues
"""

import streamlit as st
import sys
import os

# Set page config first
st.set_page_config(
    page_title="🎯 LLM Debate System (Small Models)",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

def setup_small_models_sync():
    """Setup small model configuration synchronously"""
    try:
        import asyncio
        from dynamic_config import create_small_model_config_only
        from config import Config
        
        async def _setup():
            # Create small model config
            orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
            
            if orchestrator_config and len(debater_configs) >= 2:
                # Update global config
                Config.ORCHESTRATOR_MODEL = orchestrator_config
                Config.DEBATER_MODELS = debater_configs
                return True
            return False
        
        # Run async function safely
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we need to create a new thread
                import threading
                import concurrent.futures
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    return new_loop.run_until_complete(_setup())
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result()
            else:
                return loop.run_until_complete(_setup())
        except RuntimeError:
            # No loop exists, create one
            return asyncio.run(_setup())
            
    except Exception as e:
        st.error(f"Error setting up small models: {e}")
        return False

def main():
    st.title("🎯 LLM Debate System")
    st.markdown("*Optimized for small local models*")
    
    # Setup small models on first run
    if 'models_configured' not in st.session_state:
        st.info("🔧 Configuring small models...")
        try:
            if setup_small_models_sync():
                st.session_state.models_configured = True
                st.success("✅ Small models configured successfully!")
                
                # Show current config
                from config import Config
                st.info(f"🧠 Orchestrator: {Config.ORCHESTRATOR_MODEL.model}")
                st.info(f"👥 Debaters: {', '.join([d.model for d in Config.DEBATER_MODELS])}")
                
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
        except Exception as e:
            st.error(f"Configuration error: {e}")
            st.error(f"Error details: {str(e)}")
            return
    
    # Show system status
    st.success("✅ Small model system ready!")
    
    # Simple debate interface
    st.subheader("🎭 Start a Debate")
    
    question = st.text_input("Enter your debate question:", placeholder="What are the benefits of renewable energy?")
    
    if st.button("🚀 Start Debate") and question:
        with st.spinner("🤔 Debating..."):
            try:
                # Run debate with small models
                from main import LLMDebateSystem
                import asyncio
                
                async def run_debate():
                    system = LLMDebateSystem()
                    if await system.initialize():
                        result = await system.conduct_debate(question, max_rounds=3)
                        # Note: Models stay loaded for efficiency - cleanup only on app exit
                        return result
                    return None
                
                # Use event loop properly for Streamlit
                try:
                    # Try to use existing loop
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Create new thread for async execution
                        import threading
                        import concurrent.futures
                        
                        def run_in_thread():
                            new_loop = asyncio.new_event_loop()
                            return new_loop.run_until_complete(run_debate())
                        
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(run_in_thread)
                            result = future.result()
                    else:
                        result = loop.run_until_complete(run_debate())
                except RuntimeError:
                    # No loop exists, create one
                    result = asyncio.run(run_debate())
                
                if result:
                    st.success("✅ Debate completed!")
                    st.subheader("📋 Results")
                    st.write(f"**Question:** {result.original_question}")
                    st.write(f"**Status:** {result.final_status}")
                    st.write(f"**Rounds:** {result.total_rounds}")
                    
                    if result.final_summary:
                        st.subheader("📄 Summary")
                        st.write(result.final_summary)
                    
                    # Show rounds
                    st.subheader("🔄 Debate Rounds")
                    for i, round_data in enumerate(result.rounds, 1):
                        with st.expander(f"Round {i}"):
                            for response in round_data.debater_responses:
                                st.write(f"**{response.debater_name}:** {response.response}")
                else:
                    st.error("❌ Debate failed")
            except Exception as e:
                st.error(f"Error during debate: {e}")

if __name__ == "__main__":
    main()
