"""
FastAPI REST API for the LLM Debate System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import logging
import os
from datetime import datetime
import uuid
from system.main import LLMDebateSystem
from backend.models import DebateResult, DebateStatus
from config import Config
from backend.ollama_integration import ollama_manager

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

# Mount static files for Angular frontend at root level
angular_dist_path = "/app/angular-ui/dist"

# Global state
debate_system = LLMDebateSystem()
active_debates: Dict[str, DebateResult] = {}
debate_queue: List[str] = []
debate_start_times: Dict[str, datetime] = {}  # Track when debates started

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
    message: Optional[str] = None
    current_round: Optional[int] = None
    total_rounds: Optional[int] = None
    consensus_scores: Optional[List[float]] = None
    final_summary: Optional[str] = None
    duration: Optional[float] = None
    progress: Optional[int] = None  # Add progress field

class SystemStatusResponse(BaseModel):
    ollama_connected: bool
    available_models: List[str]
    missing_models: List[str]
    system_initialized: bool

class DebateListResponse(BaseModel):
    debates: List[Dict[str, Any]]
    total: int

# API Routes - Note: No root API route, Angular will handle the root
@app.get("/api/health", summary="API Health Check")
async def health_check():
    """Health check endpoint for API"""
    return {
        "message": "LLM Debate System API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/status", summary="API Status Check")
async def api_status():
    """Status check endpoint that Angular might be calling"""
    return await get_system_status()

@app.get("/api/config", summary="Get Configuration")
async def api_config():
    """Get configuration endpoint for API"""
    return await get_config()

@app.get("/api/debates", summary="List Debates")
async def api_list_debates(status: Optional[str] = None, limit: int = 10, offset: int = 0):
    """List debates endpoint for API"""
    return await list_debates(status, limit, offset)

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
        debate_start_times[debate_id] = datetime.now()  # Track start time
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
        # Clean up start time tracking
        if debate_id in debate_start_times:
            del debate_start_times[debate_id]
        
        logger.info(f"Debate {debate_id} completed with status: {result.final_status}")
    except Exception as e:
        logger.error(f"Error in background debate {debate_id}: {e}")
        # Remove from queue on error
        if debate_id in debate_queue:
            debate_queue.remove(debate_id)
        # Clean up start time tracking
        if debate_id in debate_start_times:
            del debate_start_times[debate_id]

@app.get("/debates/{debate_id}", response_model=DebateStatusResponse, summary="Get Debate Status")
async def get_debate_status(debate_id: str):
    """Get the status of a specific debate"""
    try:
        # Check if debate is in queue
        if debate_id in debate_queue:
            # Calculate time-based progress for debates in progress
            start_time = debate_start_times.get(debate_id, datetime.now())
            elapsed_time = (datetime.now() - start_time).total_seconds()
            estimated_duration = 120  # seconds, adjust based on your typical debate time
            progress = min(80, (elapsed_time / estimated_duration) * 100)  # Cap at 80% for in-progress
            progress = max(5, progress)  # Always show at least 5% progress when started
            
            return DebateStatusResponse(
                debate_id=debate_id,
                status=DebateStatus.IN_PROGRESS,
                message="Debate is in progress",
                progress=int(progress),
                current_round=0,
                total_rounds=3
            )
        
        # Check if debate is completed
        if debate_id in active_debates:
            result = active_debates[debate_id]
            # Show 100% progress for any completed status (not just COMPLETED or CONSENSUS_REACHED)
            completed_statuses = [DebateStatus.COMPLETED, DebateStatus.CONSENSUS_REACHED, DebateStatus.MAX_ROUNDS_EXCEEDED, DebateStatus.ERROR]
            progress = 100 if result.final_status in completed_statuses else 0
            
            return DebateStatusResponse(
                debate_id=debate_id,
                status=result.final_status,
                current_round=result.total_rounds,
                total_rounds=result.total_rounds,
                consensus_scores=result.consensus_evolution,
                final_summary=result.final_summary,
                duration=result.total_duration,
                progress=progress
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

# API endpoints for Angular frontend (additional to main endpoints)
@app.post("/api/debate/start", response_model=DebateResponse, summary="Start New Debate (API)")
async def api_start_debate(request: DebateRequest, background_tasks: BackgroundTasks):
    """Start a new debate via API endpoint (used by Angular frontend)"""
    return await start_debate(request, background_tasks)

@app.get("/api/debate/{debate_id}/status", response_model=DebateStatusResponse, summary="Get Debate Status (API)")
async def api_get_debate_status(debate_id: str):
    """Get the status of a specific debate via API endpoint (used by Angular frontend)"""
    try:
        # Check if debate is in queue (in progress)
        if debate_id in debate_queue:
            # Calculate time-based progress for debates in progress
            start_time = debate_start_times.get(debate_id, datetime.now())
            elapsed_time = (datetime.now() - start_time).total_seconds()
            estimated_duration = 120  # seconds, adjust based on your typical debate time
            progress = min(80, (elapsed_time / estimated_duration) * 100)  # Cap at 80% for in-progress
            progress = max(5, progress)  # Always show at least 5% progress when started
            
            return DebateStatusResponse(
                debate_id=debate_id,
                status=DebateStatus.IN_PROGRESS,
                message="Debate is in progress",
                progress=int(progress),
                current_round=0,
                total_rounds=3  # Default expected rounds
            )
        
        # Check if debate is completed
        if debate_id in active_debates:
            result = active_debates[debate_id]
            # Show 100% progress for any completed status (not just COMPLETED or CONSENSUS_REACHED)
            completed_statuses = [DebateStatus.COMPLETED, DebateStatus.CONSENSUS_REACHED, DebateStatus.MAX_ROUNDS_EXCEEDED, DebateStatus.ERROR]
            progress = 100 if result.final_status in completed_statuses else 0
            
            return DebateStatusResponse(
                debate_id=debate_id,
                status=result.final_status,
                current_round=result.total_rounds,
                total_rounds=result.total_rounds,
                consensus_scores=result.consensus_evolution,
                final_summary=result.final_summary,
                duration=result.total_duration,
                progress=progress
            )
        
        # Debate not found
        raise HTTPException(status_code=404, detail="Debate not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting debate status via API: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting debate status: {str(e)}")

# Serve Angular frontend at root
@app.get("/")
async def serve_frontend():
    """Serve the Angular frontend"""
    index_path = "/app/angular-ui/dist/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    else:
        # Fallback to API response if Angular not available
        from fastapi.responses import JSONResponse
        return JSONResponse({
            "message": "LLM Debate System API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "note": "Angular frontend not available"
        })

# Serve Angular static assets (JS, CSS files)
@app.get("/{filename}")
async def serve_angular_assets(filename: str):
    """Serve Angular static assets like JS and CSS files"""
    # Only serve known Angular asset types to avoid conflicts
    if (filename.endswith('.js') or filename.endswith('.css') or 
        filename.endswith('.txt') or filename.endswith('.ico')):
        file_path = f"/app/angular-ui/dist/{filename}"
        if os.path.exists(file_path):
            # Determine media type
            if filename.endswith('.js'):
                media_type = 'application/javascript'
            elif filename.endswith('.css'):
                media_type = 'text/css'
            elif filename.endswith('.ico'):
                media_type = 'image/x-icon'
            else:
                media_type = 'text/plain'
            return FileResponse(file_path, media_type=media_type)
    
    # If not an asset file, fall through to catch-all route
    raise HTTPException(status_code=404, detail="Not found")

# Catch-all route for Angular routing (must be last)
@app.get("/{path:path}")
async def serve_angular_routes(path: str):
    """Serve Angular app for any unmatched routes (client-side routing)"""
    # Skip asset files and known paths that should return 404
    if (path.startswith("docs") or path.startswith("redoc") or 
        path.startswith("static/") or path.endswith('.js') or 
        path.endswith('.css') or path.endswith('.txt') or path.endswith('.ico')):
        raise HTTPException(status_code=404, detail="Not found")
    
    # For all other paths (including Angular routes), serve the Angular app
    index_path = "/app/angular-ui/dist/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html')
    else:
        raise HTTPException(status_code=404, detail="Frontend not available")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup"""
    logger.info("Starting LLM Debate System API")
    # Auto-initialize system on startup
    try:
        await debate_system.initialize()
        logger.info("System auto-initialized successfully")
    except Exception as e:
        logger.warning(f"Auto-initialization failed: {e}")
        logger.info("System will initialize on first debate if auto-init failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=Config.FASTAPI_PORT)
