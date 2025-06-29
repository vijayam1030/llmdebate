"""
FastAPI Backend for LLM Debate System
Replaces Streamlit with a REST API
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

# Import our existing system
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from system.main import LLMDebateSystem
from system.config import Config, ModelConfig
from system.dynamic_config import create_small_model_config_only
from backend.models import DebateResult, DebateStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for session management
debate_system: Optional[LLMDebateSystem] = None
current_debates: Dict[str, Dict[str, Any]] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the debate system on startup"""
    global debate_system
    logger.info("Initializing LLM Debate System...")
    
    try:
        # Create small model config
        result = await create_small_model_config_only()
        if not result or result[0] is None:
            raise Exception("No suitable small models found")
        
        orchestrator_config, debater_configs = result
        
        # Handle both string and ModelConfig object types
        if hasattr(orchestrator_config, 'model'):
            orchestrator_model = orchestrator_config.model
        else:
            orchestrator_model = str(orchestrator_config)
            
        if debater_configs and hasattr(debater_configs[0], 'model'):
            debater_models = [config.model for config in debater_configs]
        else:
            debater_models = [str(config) for config in debater_configs]
        
        # Update Config with proper ModelConfig objects
        Config.ORCHESTRATOR_MODEL = ModelConfig(
            name="Orchestrator",
            model=orchestrator_model,
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
        
        # Create ModelConfig objects for debaters
        debater_personalities = [
            ("Analytical_Debater", "analytical and fact-focused", "You are an analytical debater who focuses on facts, data, and logical reasoning."),
            ("Creative_Debater", "creative and perspective-oriented", "You are a creative debater who brings unique perspectives and innovative thinking."),
            ("Pragmatic_Debater", "pragmatic and solution-oriented", "You are a pragmatic debater focused on practical solutions and real-world applications.")
        ]
        
        Config.DEBATER_MODELS = []
        for i, (name, personality, system_prompt) in enumerate(debater_personalities):
            if i < len(debater_models):
                Config.DEBATER_MODELS.append(ModelConfig(
                    name=name,
                    model=debater_models[i],
                    temperature=0.6 + (i * 0.1),  # Vary temperature slightly
                    max_tokens=800,
                    personality=personality,
                    system_prompt=system_prompt
                ))
        
        logger.info(f"Configuration set - Orchestrator: {Config.ORCHESTRATOR_MODEL}")
        logger.info(f"Configuration set - Debaters: {Config.DEBATER_MODELS}")
        
        # Initialize system
        debate_system = LLMDebateSystem()
        await debate_system.initialize()
        
        logger.info("System initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        debate_system = None
        # Don't log success if there was an error!
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down LLM Debate System...")

# FastAPI app with lifespan
app = FastAPI(
    title="LLM Debate System API",
    description="REST API for AI-powered debates",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for Angular frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8000"],  # Angular dev server and production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Angular static files (when built) - AFTER API routes to avoid conflicts
angular_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "angular-ui", "dist")
if os.path.exists(angular_dist):
    # Mount static files on a sub-path first to test
    logger.info(f"Angular dist folder found at: {angular_dist}")
else:
    logger.warning(f"Angular dist folder not found at: {angular_dist}")

# Pydantic models for API
class DebateRequest(BaseModel):
    question: str
    max_rounds: Optional[int] = 3

class DebateResponse(BaseModel):
    debate_id: str
    status: str
    message: str

class DebateStatusResponse(BaseModel):
    debate_id: str
    status: str
    progress: float
    current_round: Optional[int] = None
    total_rounds: Optional[int] = None
    result: Optional[Dict[str, Any]] = None

class SystemStatusResponse(BaseModel):
    initialized: bool
    models_loaded: List[str]
    config: Dict[str, Any]

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LLM Debate System API", "version": "1.0.0"}

@app.get("/api/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system initialization status"""
    logger.info(f"Status check - debate_system: {debate_system is not None}")
    
    if debate_system is None:
        return SystemStatusResponse(
            initialized=False,
            models_loaded=[],
            config={"error": "System not initialized - check server logs"}
        )
    
    try:
        # Extract model names from ModelConfig objects
        debater_model_names = [model.model for model in Config.DEBATER_MODELS]
        orchestrator_model_name = Config.ORCHESTRATOR_MODEL.model
        models_list = debater_model_names + [orchestrator_model_name]
        
        config_dict = {
            "max_rounds": Config.MAX_ROUNDS,
            "orchestrator_model": orchestrator_model_name,
            "debater_models": debater_model_names,
            "orchestrator_max_tokens": getattr(Config, 'ORCHESTRATOR_MAX_TOKENS', Config.ORCHESTRATOR_MODEL.max_tokens),
            "debater_max_tokens": getattr(Config, 'DEBATER_MAX_TOKENS', Config.DEBATER_MODELS[0].max_tokens if Config.DEBATER_MODELS else 800)
        }
        
        return SystemStatusResponse(
            initialized=True,
            models_loaded=models_list,
            config=config_dict
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return SystemStatusResponse(
            initialized=False,
            models_loaded=[],
            config={"error": str(e)}
        )

@app.post("/api/debate/start", response_model=DebateResponse)
async def start_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Start a new debate"""
    if debate_system is None:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    # Generate unique debate ID
    debate_id = str(uuid.uuid4())
    
    # Initialize debate tracking
    current_debates[debate_id] = {
        "status": "starting",
        "progress": 0.0,
        "question": request.question,
        "max_rounds": request.max_rounds or 3,
        "started_at": datetime.now(),
        "result": None
    }
    
    # Start debate in background
    background_tasks.add_task(run_debate, debate_id, request.question, request.max_rounds)
    
    return DebateResponse(
        debate_id=debate_id,
        status="started",
        message=f"Debate started for question: {request.question}"
    )

@app.get("/api/debate/{debate_id}/status", response_model=DebateStatusResponse)
async def get_debate_status(debate_id: str):
    """Get status of a specific debate"""
    if debate_id not in current_debates:
        raise HTTPException(status_code=404, detail="Debate not found")
    
    debate_info = current_debates[debate_id]
    
    return DebateStatusResponse(
        debate_id=debate_id,
        status=debate_info["status"],
        progress=debate_info["progress"],
        current_round=debate_info.get("current_round"),
        total_rounds=debate_info.get("max_rounds"),
        result=debate_info.get("result")
    )

@app.get("/api/debates")
async def list_debates():
    """List all debates"""
    return {
        "debates": [
            {
                "debate_id": debate_id,
                "question": info["question"],
                "status": info["status"],
                "started_at": info["started_at"].isoformat(),
                "progress": info["progress"]
            }
            for debate_id, info in current_debates.items()
        ]
    }

async def run_debate(debate_id: str, question: str, max_rounds: Optional[int] = None):
    """Run debate in background"""
    try:
        # Update status
        current_debates[debate_id]["status"] = "running"
        current_debates[debate_id]["progress"] = 0.1
        
        # Run the debate
        result = await debate_system.conduct_debate(
            question=question,
            max_rounds=max_rounds or 3
        )
        
        # Convert result to serializable format
        result_dict = {
            "question": question,
            "final_status": result.final_status.value,
            "final_summary": result.final_summary,
            "total_rounds": result.total_rounds,
            "consensus_reached": result.consensus_reached,
            "rounds": []
        }
        
        # Add round details
        for round_data in result.rounds:
            round_dict = {
                "round_number": round_data.round_number,
                "responses": [
                    {
                        "agent_name": resp.agent_name,
                        "response": resp.response,
                        "token_count": resp.token_count,
                        "timestamp": resp.timestamp.isoformat()
                    }
                    for resp in round_data.responses
                ],
                "consensus_analysis": {
                    "average_similarity": round_data.consensus_analysis.average_similarity,
                    "consensus_reached": round_data.consensus_analysis.consensus_reached,
                    "similarity_matrix": round_data.consensus_analysis.similarity_matrix
                },
                "orchestrator_feedback": round_data.orchestrator_feedback
            }
            result_dict["rounds"].append(round_dict)
        
        # Update with final result
        current_debates[debate_id]["status"] = "completed"
        current_debates[debate_id]["progress"] = 1.0
        current_debates[debate_id]["result"] = result_dict
        current_debates[debate_id]["completed_at"] = datetime.now()
        
    except Exception as e:
        logger.error(f"Debate {debate_id} failed: {e}")
        current_debates[debate_id]["status"] = "failed"
        current_debates[debate_id]["error"] = str(e)

# Mount Angular static files AFTER all API routes are defined
angular_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "angular-ui", "dist")
if os.path.exists(angular_dist):
    app.mount("/", StaticFiles(directory=angular_dist, html=True), name="angular")
    logger.info(f"Angular static files will be mounted from: {angular_dist}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
