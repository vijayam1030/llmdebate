#!/usr/bin/env python3
"""
Simple test of the status endpoint without starting a server
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from system.config import Config

async def test_config():
    """Test config access directly"""
    print("🔧 Testing Config access...")
    
    print(f"Orchestrator model: {Config.ORCHESTRATOR_MODEL.model}")
    print(f"Debater models: {[model.model for model in Config.DEBATER_MODELS]}")
    print(f"Max rounds: {Config.MAX_ROUNDS}")
    print(f"Orchestrator max tokens: {getattr(Config, 'ORCHESTRATOR_MAX_TOKENS', Config.ORCHESTRATOR_MODEL.max_tokens)}")
    print(f"Debater max tokens: {getattr(Config, 'DEBATER_MAX_TOKENS', Config.DEBATER_MODELS[0].max_tokens if Config.DEBATER_MODELS else 800)}")
    
    # Test what the API would return
    debater_model_names = [model.model for model in Config.DEBATER_MODELS]
    orchestrator_model_name = Config.ORCHESTRATOR_MODEL.model
    models_list = debater_model_names + [orchestrator_model_name]
    
    print(f"\nAPI would return models_loaded: {models_list}")
    print("✅ Config test complete!")

if __name__ == "__main__":
    asyncio.run(test_config())
