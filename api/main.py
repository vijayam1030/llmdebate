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
import threading
import subprocess
import json

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
ngrok_url: Optional[str] = None
ngrok_process = None

def start_ngrok():
    """Start ngrok tunnel and return the public URL"""
    global ngrok_url, ngrok_process
    
    try:
        # Start ngrok tunnel
        logger.info("Starting ngrok tunnel...")
        ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '8000', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give ngrok a moment to start
        import time
        time.sleep(5)
        
        # Try multiple times to get the URL since ngrok might take a moment
        for attempt in range(3):
            try:
                # Use requests instead of curl for better error handling
                import requests
                response = requests.get('http://localhost:4040/api/tunnels', timeout=3)
                
                if response.status_code == 200:
                    tunnels_data = response.json()
                    tunnels = tunnels_data.get('tunnels', [])
                    
                    for tunnel in tunnels:
                        if tunnel.get('proto') == 'https':
                            ngrok_url = tunnel.get('public_url')
                            logger.info(f"🌐 ngrok tunnel started: {ngrok_url}")
                            return ngrok_url
                            
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}: Could not get ngrok URL via API: {e}")
                if attempt < 2:  # Sleep between attempts
                    time.sleep(2)
            
        # Check if ngrok is running
        if ngrok_process and ngrok_process.poll() is None:
            logger.info("🌐 ngrok tunnel started (URL will be available in ngrok dashboard)")
            return None  # Will be populated once ngrok fully starts
            
    except FileNotFoundError:
        logger.warning("ngrok not found in PATH. Please install ngrok to enable public URL sharing.")
    except Exception as e:
        logger.error(f"Failed to start ngrok: {e}")
    
    return None

def check_ngrok_url():
    """Check if ngrok URL is available"""
    global ngrok_url
    
    if ngrok_url:  # Already have URL
        return ngrok_url
        
    try:
        import requests
        response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
        
        if response.status_code == 200:
            tunnels_data = response.json()
            tunnels = tunnels_data.get('tunnels', [])
            
            for tunnel in tunnels:
                if tunnel.get('proto') == 'https':
                    ngrok_url = tunnel.get('public_url')
                    if ngrok_url:
                        logger.info(f"🌐 ngrok URL detected: {ngrok_url}")
                        return ngrok_url
                        
    except Exception:
        pass  # Silent fail for periodic checks
    
    return None

def stop_ngrok():
    """Stop ngrok tunnel"""
    global ngrok_process
    if ngrok_process:
        try:
            ngrok_process.terminate()
            ngrok_process.wait(timeout=5)
            logger.info("ngrok tunnel stopped")
        except Exception as e:
            logger.error(f"Error stopping ngrok: {e}")
            try:
                ngrok_process.kill()
            except:
                pass
        finally:
            ngrok_process = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the debate system on startup"""
    global debate_system, ngrok_url
    logger.info("Initializing LLM Debate System...")
    
    # Start ngrok tunnel in background
    def start_ngrok_background():
        start_ngrok()
    
    ngrok_thread = threading.Thread(target=start_ngrok_background, daemon=True)
    ngrok_thread.start()
    
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
    stop_ngrok()

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
    allow_origins=["http://localhost:4200", "http://localhost:8000", "*"],  # Angular dev server, production, and ngrok
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
    ngrok_url: Optional[str] = None

@app.get("/api")
async def api_root():
    """API root endpoint"""
    return {"message": "LLM Debate System API", "version": "1.0.0"}

@app.get("/api/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system initialization status"""
    logger.info(f"Status check - debate_system: {debate_system is not None}")
    
    # Check for ngrok URL if we don't have it yet
    check_ngrok_url()
    
    if debate_system is None:
        return SystemStatusResponse(
            initialized=False,
            models_loaded=[],
            config={"error": "System not initialized - check server logs"},
            ngrok_url=ngrok_url
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
            config=config_dict,
            ngrok_url=ngrok_url
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return SystemStatusResponse(
            initialized=False,
            models_loaded=[],
            config={"error": str(e)},
            ngrok_url=ngrok_url
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
        # Return a helpful response instead of 404
        return DebateStatusResponse(
            debate_id=debate_id,
            status="not_found",
            progress=0.0,
            current_round=None,
            total_rounds=None,
            result={"error": "Debate not found. It may have been cleared due to server restart."}
        )
    
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
    """Run debate in background with progress tracking"""
    max_rounds = max_rounds or 3
    
    try:
        # Initialize debate tracking
        current_debates[debate_id]["status"] = "running"
        current_debates[debate_id]["progress"] = 0.1
        current_debates[debate_id]["current_round"] = 0
        current_debates[debate_id]["total_rounds"] = max_rounds
        
        logger.info(f"Starting debate {debate_id}: {question}")
        
        # Create a custom debate conductor with progress tracking
        from backend.debate_workflow import debate_workflow
        
        # Start debate and monitor state
        state = {
            "question": question,
            "current_round": 0,
            "max_rounds": max_rounds,
            "consensus_threshold": 0.85,
            "debater_responses": [],
            "consensus_scores": [],
            "status": "initializing",
            "orchestrator_feedback": None,
            "final_summary": None,
            "rounds_history": []
        }
        
        # Custom progress tracking with actual round monitoring
        async def track_debate_progress():
            """Monitor the debate progress"""
            last_round = 0
            round_check_interval = 2  # Check every 2 seconds
            
            while current_debates[debate_id]["status"] == "running":
                await asyncio.sleep(round_check_interval)
                
                # Check if we're still running
                if debate_id not in current_debates:
                    break
                    
                # Estimate progress based on time and expected completion
                # Basic progress tracking: 10% start + (80% / max_rounds) per round + 10% final
                estimated_progress = 0.1  # Starting progress
                
                # Add progress for completed rounds (estimate based on time)
                import time
                elapsed = time.time() - current_debates[debate_id]["started_at"].timestamp()
                
                # Rough estimation: 45 seconds per round average
                estimated_rounds_completed = min(elapsed / 45, max_rounds)
                round_progress = (estimated_rounds_completed / max_rounds) * 0.8
                
                total_progress = min(estimated_progress + round_progress, 0.9)  # Cap at 90% until complete
                
                current_debates[debate_id]["progress"] = total_progress
                current_debates[debate_id]["current_round"] = min(int(estimated_rounds_completed) + 1, max_rounds)
        
        # Start progress tracking
        progress_task = asyncio.create_task(track_debate_progress())
        
        try:
            # Run the actual debate with timeout protection
            debate_task = asyncio.create_task(debate_system.conduct_debate(
                question=question,
                max_rounds=max_rounds
            ))
            
            # Wait for debate with timeout (5 minutes)
            try:
                result = await asyncio.wait_for(debate_task, timeout=300.0)
            except asyncio.TimeoutError:
                logger.error(f"Debate {debate_id} timed out after 5 minutes")
                progress_task.cancel()
                current_debates[debate_id]["status"] = "failed"
                current_debates[debate_id]["progress"] = 0.0
                current_debates[debate_id]["error"] = "Debate timed out after 5 minutes"
                return
            
            # Stop progress tracking
            progress_task.cancel()
            
            # Convert result to serializable format
            result_dict = {
                "question": question,
                "final_status": result.final_status.value,
                "final_summary": result.final_summary or "No summary available",
                "total_rounds": result.total_rounds,
                "consensus_reached": result.consensus_reached,
                "rounds": []
            }
            
            # Add round details
            for round_data in result.rounds:
                # Safety check for round data
                if not hasattr(round_data, 'debater_responses'):
                    logger.warning(f"Round {round_data.round_number} missing debater_responses")
                    continue
                    
                round_dict = {
                    "round_number": round_data.round_number,
                    "responses": [
                        {
                            "agent_name": getattr(resp, 'debater_name', 'Unknown'),
                            "response": resp.response,
                            "token_count": getattr(resp, 'response_length', len(resp.response)),
                            "timestamp": resp.timestamp.isoformat() if hasattr(resp, 'timestamp') else datetime.now().isoformat()
                        }
                        for resp in round_data.debater_responses
                    ],
                    "consensus_analysis": {
                        "average_similarity": round_data.consensus_analysis.average_similarity if round_data.consensus_analysis else 0.0,
                        "consensus_reached": round_data.consensus_analysis.consensus_reached if round_data.consensus_analysis else False,
                        "similarity_matrix": getattr(round_data.consensus_analysis, 'similarity_scores', {}) if round_data.consensus_analysis else {}
                    },
                    "orchestrator_feedback": round_data.orchestrator_feedback or "No feedback available"
                }
                result_dict["rounds"].append(round_dict)
            
            # Update with final result
            current_debates[debate_id]["status"] = "completed"
            current_debates[debate_id]["progress"] = 1.0
            current_debates[debate_id]["current_round"] = result.total_rounds
            current_debates[debate_id]["result"] = result_dict
            current_debates[debate_id]["completed_at"] = datetime.now()
            
            logger.info(f"Debate {debate_id} completed successfully")
            
        except Exception as e:
            progress_task.cancel()
            raise e
        
    except Exception as e:
        logger.error(f"Debate {debate_id} failed: {e}")
        current_debates[debate_id]["status"] = "failed"
        current_debates[debate_id]["progress"] = 0.0
        current_debates[debate_id]["error"] = str(e)

# Mount Angular static files AFTER all API routes are defined
angular_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "angular-ui", "dist")
if os.path.exists(angular_dist):
    app.mount("/", StaticFiles(directory=angular_dist, html=True), name="angular")
    logger.info(f"Angular static files will be mounted from: {angular_dist}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
