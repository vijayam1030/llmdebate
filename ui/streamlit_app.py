"""
Streamlit web interface for the LLM Debate System
"""

import asyncio
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
from typing import List

from main import LLMDebateSystem
from models import DebateResult, DebateStatus
from config import Config
from ollama_integration import ollama_manager

# Page configuration
st.set_page_config(
    page_title="🎯 LLM Debate System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1e3a8a;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .debate-question {
        background-color: #f0f9ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    .debater-response {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #10b981;
    }
    .consensus-score {
        font-size: 1.2rem;
        font-weight: bold;
        color: #059669;
    }
    .status-success {
        color: #059669;
        font-weight: bold;
    }
    .status-warning {
        color: #d97706;
        font-weight: bold;
    }
    .status-error {
        color: #dc2626;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if 'debate_system' not in st.session_state:
        st.session_state.debate_system = LLMDebateSystem()
        st.session_state.system_initialized = False
        st.session_state.debate_history = []
        st.session_state.current_debate = None

def format_status_badge(status: DebateStatus) -> str:
    """Format status as colored badge"""
    status_colors = {
        DebateStatus.CONSENSUS_REACHED: "🟢",
        DebateStatus.MAX_ROUNDS_EXCEEDED: "🟡", 
        DebateStatus.ERROR: "🔴",
        DebateStatus.IN_PROGRESS: "🔵"
    }
    return f"{status_colors.get(status, '⚪')} {status.value.replace('_', ' ').title()}"

def create_consensus_chart(consensus_scores: List[float]) -> go.Figure:
    """Create a line chart showing consensus evolution"""
    if not consensus_scores:
        return None
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(consensus_scores) + 1)),
        y=consensus_scores,
        mode='lines+markers',
        name='Consensus Score',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=8)
    ))
    
    # Add threshold line
    fig.add_hline(
        y=Config.CONSENSUS_THRESHOLD,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Consensus Threshold ({Config.CONSENSUS_THRESHOLD})"
    )
    
    fig.update_layout(
        title="Consensus Evolution Across Rounds",
        xaxis_title="Round",
        yaxis_title="Consensus Score",
        yaxis=dict(range=[0, 1]),
        template="plotly_white",
        height=400
    )
    
    return fig

def create_response_length_chart(debate_result: DebateResult) -> go.Figure:
    """Create a chart showing response lengths by debater and round"""
    data = []
    for round_data in debate_result.rounds:
        for response in round_data.debater_responses:
            data.append({
                'Round': round_data.round_number,
                'Debater': response.debater_name,
                'Response Length': response.response_length,
                'Model': response.model
            })
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    fig = px.bar(
        df,
        x='Round',
        y='Response Length',
        color='Debater',
        title="Response Lengths by Round and Debater",
        template="plotly_white",
        height=400
    )
    
    return fig

async def check_system_status():
    """Check if Ollama and required models are available"""
    status = {
        'ollama_connected': False,
        'models_available': [],
        'missing_models': []
    }
    
    try:
        # Check Ollama connection
        status['ollama_connected'] = await ollama_manager.check_ollama_connection()
        
        if status['ollama_connected']:
            # Check available models
            available_models = await ollama_manager.list_available_models()
            required_models = Config.get_available_models()
            
            status['models_available'] = [m for m in required_models if m in available_models]
            status['missing_models'] = [m for m in required_models if m not in available_models]
    
    except Exception as e:
        st.error(f"Error checking system status: {e}")
    
    return status

def main():
    """Main Streamlit application"""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🎯 LLM Debate System</h1>', unsafe_allow_html=True)
    st.markdown("*Multi-LLM debate platform using local Ollama models*")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Configuration")
        
        # System status
        with st.expander("🔍 System Status", expanded=True):
            status_placeholder = st.empty()
            
            if st.button("Check System Status"):
                with st.spinner("Checking system status..."):
                    status = asyncio.run(check_system_status())
                    
                    with status_placeholder.container():
                        if status['ollama_connected']:
                            st.success("✅ Ollama Connected")
                        else:
                            st.error("❌ Ollama Not Connected")
                            st.info("Please ensure Ollama is running on localhost:11434")
                        
                        if status['models_available']:
                            st.success(f"✅ Available Models: {len(status['models_available'])}")
                            for model in status['models_available']:
                                st.text(f"  • {model}")
                        
                        if status['missing_models']:
                            st.warning(f"⚠️ Missing Models: {len(status['missing_models'])}")
                            for model in status['missing_models']:
                                st.text(f"  • {model}")
                            st.info("Missing models will be downloaded automatically when needed.")
        
        # Configuration
        st.header("🎛️ Debate Settings")
        max_rounds = st.slider("Max Rounds", 1, 10, Config.MAX_ROUNDS)
        consensus_threshold = st.slider("Consensus Threshold", 0.5, 1.0, Config.CONSENSUS_THRESHOLD, 0.05)
        
        # Model information
        with st.expander("🤖 Model Configuration"):
            st.write("**Orchestrator:**")
            st.text(f"• {Config.ORCHESTRATOR_MODEL.model}")
            st.write("**Debaters:**")
            for debater in Config.DEBATER_MODELS:
                st.text(f"• {debater.name}: {debater.model}")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🎯 New Debate", "📊 Analytics", "📚 History"])
    
    with tab1:
        st.header("Start a New Debate")
        
        # Question input
        question = st.text_area(
            "Enter your debate question:",
            placeholder="e.g., What are the benefits and drawbacks of artificial intelligence in education?",
            height=100
        )
        
        # Example questions
        with st.expander("💡 Example Questions"):
            example_questions = [
                "What are the benefits and drawbacks of renewable energy?",
                "Should artificial intelligence development be regulated?", 
                "What is the best approach to address climate change?",
                "How can we improve public education systems?",
                "What are the implications of remote work on society?"
            ]
            
            for i, example in enumerate(example_questions):
                if st.button(f"Use: {example}", key=f"example_{i}"):
                    question = example
                    st.rerun()
        
        # Start debate button
        if st.button("🚀 Start Debate", type="primary", disabled=not question.strip()):
            if not question.strip():
                st.error("Please enter a question for the debate.")
                return
            
            # Initialize system if needed
            if not st.session_state.system_initialized:
                with st.spinner("Initializing debate system..."):
                    initialization_success = asyncio.run(st.session_state.debate_system.initialize())
                    if not initialization_success:
                        st.error("Failed to initialize the debate system. Please check your Ollama installation.")
                        return
                    st.session_state.system_initialized = True
                    st.success("System initialized successfully!")
            
            # Conduct debate
            with st.spinner("Conducting debate... This may take a few minutes."):
                try:
                    result = asyncio.run(st.session_state.debate_system.conduct_debate(question, max_rounds))
                    st.session_state.current_debate = result
                    st.session_state.debate_history.append(result)
                    st.success("Debate completed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error during debate: {e}")
        
        # Display current debate results
        if st.session_state.current_debate:
            result = st.session_state.current_debate
            
            st.markdown("---")
            st.header("📋 Debate Results")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Status", format_status_badge(result.final_status))
            with col2:
                st.metric("Total Rounds", result.total_rounds)
            with col3:
                if result.total_duration:
                    st.metric("Duration", f"{result.total_duration:.1f}s")
            with col4:
                if result.consensus_evolution:
                    final_consensus = result.consensus_evolution[-1]
                    st.metric("Final Consensus", f"{final_consensus:.3f}")
            
            # Question
            st.markdown(f'<div class="debate-question"><strong>Question:</strong> {result.original_question}</div>', 
                       unsafe_allow_html=True)
            
            # Final summary
            if result.final_summary:
                st.subheader("🎯 Final Summary")
                st.markdown(result.final_summary)
            
            # Consensus evolution chart
            if result.consensus_evolution and len(result.consensus_evolution) > 1:
                st.subheader("📈 Consensus Evolution")
                fig = create_consensus_chart(result.consensus_evolution)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Round-by-round breakdown
            st.subheader("🔄 Round-by-Round Breakdown")
            for i, round_data in enumerate(result.rounds):
                with st.expander(f"Round {round_data.round_number}", expanded=(i == 0)):
                    # Consensus score for this round
                    if round_data.consensus_analysis:
                        consensus_score = round_data.consensus_analysis.average_similarity
                        st.markdown(f'<div class="consensus-score">Consensus Score: {consensus_score:.3f}</div>', 
                                   unsafe_allow_html=True)
                    
                    # Debater responses
                    for response in round_data.debater_responses:
                        st.markdown(f'<div class="debater-response">'
                                   f'<strong>{response.debater_name}</strong> ({response.model})<br>'
                                   f'{response.response}'
                                   f'</div>', unsafe_allow_html=True)
                    
                    # Orchestrator feedback
                    if round_data.orchestrator_feedback:
                        st.info(f"**Orchestrator Feedback:** {round_data.orchestrator_feedback}")
    
    with tab2:
        st.header("📊 Debate Analytics")
        
        if st.session_state.debate_history:
            # Overall statistics
            total_debates = len(st.session_state.debate_history)
            successful_debates = len([d for d in st.session_state.debate_history 
                                    if d.final_status == DebateStatus.CONSENSUS_REACHED])
            avg_rounds = sum(d.total_rounds for d in st.session_state.debate_history) / total_debates
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Debates", total_debates)
            with col2:
                st.metric("Success Rate", f"{(successful_debates/total_debates)*100:.1f}%")
            with col3:
                st.metric("Avg Rounds", f"{avg_rounds:.1f}")
            
            # Response length analysis
            if st.session_state.current_debate:
                st.subheader("📏 Response Length Analysis")
                fig = create_response_length_chart(st.session_state.current_debate)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.info("No debate data available. Conduct some debates to see analytics.")
    
    with tab3:
        st.header("📚 Debate History")
        
        if st.session_state.debate_history:
            for i, debate in enumerate(reversed(st.session_state.debate_history)):
                with st.expander(f"Debate {len(st.session_state.debate_history)-i}: {debate.original_question[:100]}..."):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Status:** {format_status_badge(debate.final_status)}")
                    with col2:
                        st.write(f"**Rounds:** {debate.total_rounds}")
                    with col3:
                        if debate.total_duration:
                            st.write(f"**Duration:** {debate.total_duration:.1f}s")
                    
                    if debate.final_summary:
                        st.write("**Summary:**")
                        st.write(debate.final_summary[:300] + "..." if len(debate.final_summary) > 300 else debate.final_summary)
                    
                    if st.button(f"View Full Details", key=f"view_{i}"):
                        st.session_state.current_debate = debate
                        st.rerun()
        else:
            st.info("No debate history available.")

if __name__ == "__main__":
    main()
