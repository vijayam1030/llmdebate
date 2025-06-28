"""
FastAPI REST API for the LLM Debate System
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
from datetime import datetime
import uuid

from main import LLMDebateSystem
from models import DebateResult, DebateStatus
from config import Config
from ollama_integration import ollama_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="LLM Debate System API",
    description="REST API for conducting multi-LLM debates using local Ollama models",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
debate_system = LLMDebateSystem()
active_debates: Dict[str, DebateResult] = {}
debate_queue: List[str] = []

# Request/Response models
class DebateRequest(BaseModel):
    question: str
    max_rounds: Optional[int] = None
    consensus_threshold: Optional[float] = None

class DebateResponse(BaseModel):
    debate_id: str
    status: str
    message: str

class DebateStatusResponse(BaseModel):
    debate_id: str
    status: DebateStatus
    current_round: Optional[int] = None
    total_rounds: Optional[int] = None
    consensus_scores: Optional[List[float]] = None
    final_summary: Optional[str] = None
    duration: Optional[float] = None

class SystemStatusResponse(BaseModel):
    ollama_connected: bool
    available_models: List[str]
    missing_models: List[str]
    system_initialized: bool

class DebateListResponse(BaseModel):
    debates: List[Dict[str, Any]]
    total: int

# API Routes

@app.get("/", summary="API Health Check")
async def root():
    """Health check endpoint"""
    return {
        "message": "LLM Debate System API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/system/status", response_model=SystemStatusResponse, summary="Get System Status")
async def get_system_status():
    """Get the current system status including Ollama connection and available models"""
    try:
        # Check Ollama connection
        ollama_connected = await ollama_manager.check_ollama_connection()
        
        available_models = []
        missing_models = []
        
        if ollama_connected:
            # Get available models
            all_models = await ollama_manager.list_available_models()
            required_models = Config.get_available_models()
            
            available_models = [m for m in required_models if m in all_models]
            missing_models = [m for m in required_models if m not in all_models]
        else:
            missing_models = Config.get_available_models()
        
        return SystemStatusResponse(
            ollama_connected=ollama_connected,
            available_models=available_models,
            missing_models=missing_models,
            system_initialized=debate_system.initialized
        )
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking system status: {str(e)}")

@app.post("/system/initialize", summary="Initialize System")
async def initialize_system():
    """Initialize the debate system"""
    try:
        success = await debate_system.initialize()
        if success:
            return {"message": "System initialized successfully", "status": "success"}
        else:
            raise HTTPException(status_code=500, detail="System initialization failed")
    
    except Exception as e:
        logger.error(f"Error initializing system: {e}")
        raise HTTPException(status_code=500, detail=f"Error initializing system: {str(e)}")

@app.post("/debates", response_model=DebateResponse, summary="Start New Debate")
async def start_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Start a new debate with the given question"""
    try:
        # Generate unique debate ID
        debate_id = str(uuid.uuid4())
        
        # Validate request
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Add to queue and start background processing
        debate_queue.append(debate_id)
        background_tasks.add_task(
            conduct_debate_background,
            debate_id,
            request.question,
            request.max_rounds,
            request.consensus_threshold
        )
        
        return DebateResponse(
            debate_id=debate_id,
            status="started",
            message=f"Debate started with ID: {debate_id}"
        )
        
    except Exception as e:
        logger.error(f"Error starting debate: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting debate: {str(e)}")

async def conduct_debate_background(
    debate_id: str,
    question: str,
    max_rounds: Optional[int],
    consensus_threshold: Optional[float]
):
    """Background task to conduct the debate"""
    try:
        logger.info(f"Starting debate {debate_id}: {question}")
        
        # Initialize system if needed
        if not debate_system.initialized:
            await debate_system.initialize()
        
        # Conduct debate
        result = await debate_system.conduct_debate(question, max_rounds)
        
        # Store result
        active_debates[debate_id] = result
        
        # Remove from queue
        if debate_id in debate_queue:
            debate_queue.remove(debate_id)
        
        logger.info(f"Debate {debate_id} completed with status: {result.final_status}")
        
    except Exception as e:
        logger.error(f"Error in background debate {debate_id}: {e}")
        # Remove from queue on error
        if debate_id in debate_queue:
            debate_queue.remove(debate_id)

@app.get("/debates/{debate_id}", response_model=DebateStatusResponse, summary="Get Debate Status")
async def get_debate_status(debate_id: str):
    """Get the status of a specific debate"""
    try:
        # Check if debate is in queue
        if debate_id in debate_queue:
            return DebateStatusResponse(
                debate_id=debate_id,
                status=DebateStatus.IN_PROGRESS,
                message="Debate is in progress"
            )
        
        # Check if debate is completed
        if debate_id in active_debates:
            result = active_debates[debate_id]
            return DebateStatusResponse(
                debate_id=debate_id,
                status=result.final_status,
                current_round=result.total_rounds,
                total_rounds=result.total_rounds,
                consensus_scores=result.consensus_evolution,
                final_summary=result.final_summary,
                duration=result.total_duration
            )
        
        # Debate not found
        raise HTTPException(status_code=404, detail="Debate not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting debate status: {str(e)}")

@app.get("/debates/{debate_id}/full", summary="Get Full Debate Results")
async def get_full_debate_results(debate_id: str):
    """Get the complete results of a debate including all rounds"""
    try:
        if debate_id not in active_debates:
            if debate_id in debate_queue:
                raise HTTPException(status_code=202, detail="Debate is still in progress")
            else:
                raise HTTPException(status_code=404, detail="Debate not found")
        
        result = active_debates[debate_id]
        
        # Convert to dictionary for JSON serialization
        return {
            "debate_id": debate_id,
            "original_question": result.original_question,
            "final_status": result.final_status.value,
            "total_rounds": result.total_rounds,
            "final_summary": result.final_summary,
            "consensus_evolution": result.consensus_evolution,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "total_duration": result.total_duration,
            "rounds": [
                {
                    "round_number": round_data.round_number,
                    "question": round_data.question,
                    "debater_responses": [
                        {
                            "debater_name": resp.debater_name,
                            "model": resp.model,
                            "response": resp.response,
                            "response_length": resp.response_length,
                            "timestamp": resp.timestamp.isoformat()
                        }
                        for resp in round_data.debater_responses
                    ],
                    "consensus_analysis": {
                        "similarity_scores": round_data.consensus_analysis.similarity_scores,
                        "average_similarity": round_data.consensus_analysis.average_similarity,
                        "consensus_reached": round_data.consensus_analysis.consensus_reached,
                        "analysis_method": round_data.consensus_analysis.analysis_method,
                        "details": round_data.consensus_analysis.details
                    } if round_data.consensus_analysis else None,
                    "orchestrator_feedback": round_data.orchestrator_feedback,
                    "timestamp": round_data.timestamp.isoformat()
                }
                for round_data in result.rounds
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting full debate results: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting full debate results: {str(e)}")

@app.get("/debates", response_model=DebateListResponse, summary="List All Debates")
async def list_debates(status: Optional[str] = None, limit: int = 10, offset: int = 0):
    """List all debates with optional filtering"""
    try:
        debates = []
        
        # Include completed debates
        for debate_id, result in active_debates.items():
            if status and result.final_status.value != status:
                continue
                
            debates.append({
                "debate_id": debate_id,
                "question": result.original_question[:100] + "..." if len(result.original_question) > 100 else result.original_question,
                "status": result.final_status.value,
                "total_rounds": result.total_rounds,
                "start_time": result.start_time.isoformat(),
                "duration": result.total_duration
            })
        
        # Include debates in progress
        for debate_id in debate_queue:
            if status and status != DebateStatus.IN_PROGRESS.value:
                continue
                
            debates.append({
                "debate_id": debate_id,
                "question": "In progress...",
                "status": DebateStatus.IN_PROGRESS.value,
                "total_rounds": 0,
                "start_time": datetime.now().isoformat(),
                "duration": None
            })
        
        # Sort by start time (newest first)
        debates.sort(key=lambda x: x["start_time"], reverse=True)
        
        # Apply pagination
        total = len(debates)
        debates = debates[offset:offset + limit]
        
        return DebateListResponse(debates=debates, total=total)
        
    except Exception as e:
        logger.error(f"Error listing debates: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing debates: {str(e)}")

@app.delete("/debates/{debate_id}", summary="Delete Debate")
async def delete_debate(debate_id: str):
    """Delete a specific debate"""
    try:
        if debate_id in active_debates:
            del active_debates[debate_id]
            return {"message": f"Debate {debate_id} deleted successfully"}
        elif debate_id in debate_queue:
            # Cannot delete debates in progress
            raise HTTPException(status_code=400, detail="Cannot delete debate in progress")
        else:
            raise HTTPException(status_code=404, detail="Debate not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting debate: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting debate: {str(e)}")

@app.get("/config", summary="Get System Configuration")
async def get_config():
    """Get the current system configuration"""
    return {
        "orchestrator_model": {
            "name": Config.ORCHESTRATOR_MODEL.name,
            "model": Config.ORCHESTRATOR_MODEL.model,
            "temperature": Config.ORCHESTRATOR_MODEL.temperature,
            "personality": Config.ORCHESTRATOR_MODEL.personality
        },
        "debater_models": [
            {
                "name": debater.name,
                "model": debater.model,
                "temperature": debater.temperature,
                "personality": debater.personality
            }
            for debater in Config.DEBATER_MODELS
        ],
        "max_rounds": Config.MAX_ROUNDS,
        "consensus_threshold": Config.CONSENSUS_THRESHOLD,
        "similarity_method": Config.SIMILARITY_METHOD,
        "ollama_base_url": Config.OLLAMA_BASE_URL
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    logger.info("Starting LLM Debate System API")
    
    # Optional: Auto-initialize system on startup
    # try:
    #     await debate_system.initialize()
    #     logger.info("System auto-initialized successfully")
    # except Exception as e:
    #     logger.warning(f"Auto-initialization failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.FASTAPI_PORT)
