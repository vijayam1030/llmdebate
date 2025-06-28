
import asyncio
import json
import logging
from aiohttp import web, ClientSession
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

# Suppress logging
logging.getLogger().setLevel(logging.CRITICAL)
for logger_name in ["httpx", "ollama_integration", "main", "debate_workflow", "dynamic_config"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Global system instance - this is what keeps models loaded!
DEBATE_SYSTEM = None
SYSTEM_INITIALIZED = False

async def initialize_system():
    """Initialize the system once and keep it loaded"""
    global DEBATE_SYSTEM, SYSTEM_INITIALIZED
    
    if SYSTEM_INITIALIZED:
        return {"success": True, "message": "Already initialized"}
    
    try:
        from main import LLMDebateSystem
        from dynamic_config import create_small_model_config_only
        from config import Config
        
        # Setup small models
        orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
        if orchestrator_config and len(debater_configs) >= 2:
            Config.ORCHESTRATOR_MODEL = orchestrator_config
            Config.DEBATER_MODELS = debater_configs
        else:
            return {"success": False, "error": "Failed to configure small models"}
        
        # Initialize system ONCE
        DEBATE_SYSTEM = LLMDebateSystem()
        if await DEBATE_SYSTEM.initialize():
            SYSTEM_INITIALIZED = True
            return {"success": True, "message": "System initialized successfully"}
        else:
            return {"success": False, "error": "System initialization failed"}
            
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Initialization error: {str(e)}", "traceback": traceback.format_exc()}

async def run_debate_with_loaded_system(question, max_rounds=3):
    """Run debate using the already-loaded system"""
    global DEBATE_SYSTEM, SYSTEM_INITIALIZED
    
    if not SYSTEM_INITIALIZED or not DEBATE_SYSTEM:
        return {"success": False, "error": "System not initialized"}
    
    try:
        # Use the SAME system instance with loaded models
        result = await DEBATE_SYSTEM.conduct_debate(question, max_rounds=max_rounds)
        
        return {
            "success": True,
            "question": result.original_question,
            "status": result.final_status.value if hasattr(result.final_status, 'value') else str(result.final_status),
            "rounds": result.total_rounds,
            "duration": result.total_duration if result.total_duration else 0,
            "summary": result.final_summary[:1000] if result.final_summary else "No summary available",
            "consensus_scores": result.consensus_evolution if result.consensus_evolution else [],
            "models_persistent": True  # Indicator that models stayed loaded
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": f"Debate error: {str(e)}", "traceback": traceback.format_exc()}

async def handle_initialize(request):
    """Handle system initialization"""
    result = await initialize_system()
    return web.json_response(result)

async def handle_debate(request):
    """Handle debate requests"""
    data = await request.json()
    question = data.get("question", "")
    max_rounds = data.get("max_rounds", 3)
    
    if not question:
        return web.json_response({"success": False, "error": "No question provided"})
    
    result = await run_debate_with_loaded_system(question, max_rounds)
    return web.json_response(result)

async def handle_status(request):
    """Handle status requests"""
    global SYSTEM_INITIALIZED
    return web.json_response({
        "initialized": SYSTEM_INITIALIZED,
        "models_loaded": SYSTEM_INITIALIZED
    })

async def handle_shutdown(request):
    """Handle shutdown requests"""
    global DEBATE_SYSTEM
    if DEBATE_SYSTEM:
        try:
            await DEBATE_SYSTEM.cleanup()
        except:
            pass
    return web.json_response({"success": True, "message": "Shutdown complete"})

async def create_app():
    """Create the web application"""
    app = web.Application()
    app.router.add_post('/initialize', handle_initialize)
    app.router.add_post('/debate', handle_debate)
    app.router.add_get('/status', handle_status)
    app.router.add_post('/shutdown', handle_shutdown)
    return app

async def main():
    """Main server function"""
    app = await create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', {BACKGROUND_SERVER_PORT})
    await site.start()
    
    print(f"Background debate server running on port {BACKGROUND_SERVER_PORT}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Server shutting down...")
        if DEBATE_SYSTEM:
            await DEBATE_SYSTEM.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
