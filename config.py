"""
Configuration settings for the LLM Debate System using Local Ollama Models
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class ModelConfig:
    """Configuration for individual models"""
    name: str
    model: str
    temperature: float
    max_tokens: int
    personality: str
    system_prompt: str

class Config:
    """Configuration class for LLM Debate System with Ollama"""
    
    # Ollama Configuration
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_TIMEOUT = 60
    
    # Orchestrator Model (Small Local Model)
    ORCHESTRATOR_MODEL = ModelConfig(
        name="Orchestrator",
        model="llama3.2:3b",  # Small, efficient orchestrator model
        temperature=0.3,
        max_tokens=2000,
        personality="analytical and diplomatic",
        system_prompt="""You are an expert debate orchestrator. Your role is to:
1. Analyze responses from three debater LLMs
2. Determine if they have reached consensus
3. Provide feedback to help them converge
4. Synthesize final summaries when consensus is reached
Be objective, thorough, and focus on finding common ground."""
    )
    
    # Debater Models (Small Local Models)
    DEBATER_MODELS = [
        ModelConfig(
            name="Analytical_Debater",
            model="gemma2:2b",
            temperature=0.6,
            max_tokens=800,
            personality="analytical and fact-focused",
            system_prompt="""You are an analytical debater who focuses on facts, data, and logical reasoning. 
Provide well-structured arguments based on evidence and clear reasoning. 
Be thorough but concise in your responses."""
        ),
        ModelConfig(
            name="Creative_Debater", 
            model="phi3:mini",
            temperature=0.8,
            max_tokens=800,
            personality="creative and perspective-oriented",
            system_prompt="""You are a creative debater who brings unique perspectives and innovative thinking.
Explore different angles, consider alternative viewpoints, and think outside the box.
Challenge assumptions while remaining constructive."""
        ),
        ModelConfig(
            name="Practical_Debater",
            model="tinyllama:1.1b",
            temperature=0.7,
            max_tokens=800,
            personality="practical and solution-focused",
            system_prompt="""You are a practical debater focused on real-world applications and solutions.
Emphasize actionable insights, practical implications, and concrete examples.
Bridge theory with practice in your arguments."""
        )
    ]
    
    # Debate Configuration
    MAX_ROUNDS = 3
    CONSENSUS_THRESHOLD = 0.85  # Similarity threshold for consensus
    MIN_RESPONSE_LENGTH = 50
    MAX_RESPONSE_LENGTH = 1000
    
    # Consensus Detection
    SIMILARITY_METHOD = "semantic"  # "semantic" or "keyword"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # LangGraph Configuration
    CHECKPOINTER_TYPE = "memory"  # "memory" or "sqlite"
    GRAPH_RECURSION_LIMIT = 50
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FILE = "debate_logs.txt"
    
    # UI Configuration
    STREAMLIT_PORT = 8501
    FASTAPI_PORT = 8000
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get list of available models for validation"""
        models = [cls.ORCHESTRATOR_MODEL.model]
        models.extend([debater.model for debater in cls.DEBATER_MODELS])
        return models
