"""
Data models and types for the LLM Debate System
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class DebateStatus(str, Enum):
    """Status of the debate process"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    CONSENSUS_REACHED = "consensus_reached"
    MAX_ROUNDS_EXCEEDED = "max_rounds_exceeded"
    ERROR = "error"

class DebaterResponse(BaseModel):
    """Response from a single debater LLM"""
    debater_name: str
    model: str
    response: str
    timestamp: datetime = Field(default_factory=datetime.now)
    round_number: int
    response_length: int = Field(default=0)
    
    def __post_init__(self):
        self.response_length = len(self.response)

class ConsensusAnalysis(BaseModel):
    """Analysis of consensus between debater responses"""
    similarity_scores: Dict[str, float]  # pairwise similarity scores
    average_similarity: float
    consensus_reached: bool
    threshold_used: float
    analysis_method: str
    details: Optional[str] = None

class DebateRound(BaseModel):
    """Single round of debate"""
    round_number: int
    question: str
    debater_responses: List[DebaterResponse]
    consensus_analysis: Optional[ConsensusAnalysis] = None
    orchestrator_feedback: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class DebateResult(BaseModel):
    """Final result of the debate process"""
    original_question: str
    total_rounds: int
    final_status: DebateStatus
    rounds: List[DebateRound]
    consensus_reached: bool = False  # Whether consensus was achieved
    final_summary: Optional[str] = None
    consensus_evolution: List[float] = Field(default_factory=list)  # consensus scores per round
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_duration: Optional[float] = None  # in seconds
    
    def finalize(self):
        """Mark the debate as completed and calculate duration"""
        self.end_time = datetime.now()
        if self.start_time:
            self.total_duration = (self.end_time - self.start_time).total_seconds()

class DebateState(BaseModel):
    """Current state of the debate in LangGraph"""
    question: str
    current_round: int = 0
    max_rounds: int = 3
    consensus_threshold: float = 0.85
    debater_responses: List[DebaterResponse] = Field(default_factory=list)
    consensus_scores: List[float] = Field(default_factory=list)
    status: DebateStatus = DebateStatus.INITIALIZING
    orchestrator_feedback: Optional[str] = None
    final_summary: Optional[str] = None
    rounds_history: List[DebateRound] = Field(default_factory=list)
    
    class Config:
        """Pydantic configuration"""
        use_enum_values = True

class ModelPerformanceMetrics(BaseModel):
    """Performance metrics for individual models"""
    model_name: str
    average_response_time: float
    average_response_length: int
    consensus_contribution_score: float  # how much this model contributes to consensus
    total_responses: int
    error_count: int = 0

class DebateAnalytics(BaseModel):
    """Analytics for debate performance"""
    debate_id: str
    total_debates: int
    average_rounds_to_consensus: float
    consensus_rate: float  # percentage of debates reaching consensus
    model_performance: List[ModelPerformanceMetrics]
    most_effective_model_combination: Optional[str] = None
    common_failure_patterns: List[str] = Field(default_factory=list)

class MCPContext(BaseModel):
    """Model Context Protocol context for sharing between models"""
    shared_knowledge: Dict[str, Any] = Field(default_factory=dict)
    conversation_history: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    agreed_facts: List[str] = Field(default_factory=list)
    disputed_points: List[str] = Field(default_factory=list)
    
    def add_agreed_fact(self, fact: str):
        """Add a fact that all debaters agree on"""
        if fact not in self.agreed_facts:
            self.agreed_facts.append(fact)
            
    def add_disputed_point(self, point: str):
        """Add a point that debaters disagree on"""
        if point not in self.disputed_points:
            self.disputed_points.append(point)
            
    def update_shared_knowledge(self, key: str, value: Any):
        """Update shared knowledge base"""
        self.shared_knowledge[key] = value
