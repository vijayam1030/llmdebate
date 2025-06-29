"""
Backend package for LLM Debate System
Contains core logic, agents, and workflow components
"""

from .models import (
    DebateResult, DebateStatus, DebaterResponse, 
    DebateRound, ConsensusAnalysis, MCPContext
)
from .agents import DebaterAgent, OrchestratorAgent
from .debate_workflow import DebateWorkflow
from .consensus_engine import ConsensusEngine
from .ollama_integration import ollama_manager, model_factory

__all__ = [
    'DebateResult', 'DebateStatus', 'DebaterResponse',
    'DebateRound', 'ConsensusAnalysis', 'MCPContext',
    'DebaterAgent', 'OrchestratorAgent', 
    'DebateWorkflow', 'ConsensusEngine',
    'ollama_manager', 'model_factory'
]
