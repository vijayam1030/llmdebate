#!/usr/bin/env python3
"""
Debug script to test system initialization
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Testing LLM Debate System initialization...")

async def test_init():
    try:
        print("1. Testing dynamic config import...")
        from system.dynamic_config import create_small_model_config_only
        
        print("2. Testing model config creation...")
        orchestrator_config, debater_configs = await create_small_model_config_only()
        
        if orchestrator_config:
            print(f"✅ Orchestrator model found: {orchestrator_config.model}")
            print(f"✅ Debater models found: {[c.model for c in debater_configs]}")
        else:
            print("❌ No suitable small models found!")
            print("   Make sure Ollama is running and has small models installed:")
            print("   ollama pull phi3:mini")
            print("   ollama pull llama3.2:1b")
            print("   ollama pull qwen2.5:1.5b")
            return
        
        print("\n3. Testing system initialization...")
        from system.main import LLMDebateSystem
        from system.config import Config, ModelConfig
        
        # Handle both string and ModelConfig object types
        if hasattr(orchestrator_config, 'model'):
            orchestrator_model = orchestrator_config.model
        else:
            orchestrator_model = str(orchestrator_config)
            
        if debater_configs and hasattr(debater_configs[0], 'model'):
            debater_models = [config.model for config in debater_configs]
        else:
            debater_models = [str(config) for config in debater_configs]
        
        # Create proper ModelConfig objects
        Config.ORCHESTRATOR_MODEL = ModelConfig(
            name="Orchestrator",
            model=orchestrator_model,
            temperature=0.3,
            max_tokens=2000,
            personality="analytical and diplomatic",
            system_prompt="You are an expert debate orchestrator."
        )
        
        Config.DEBATER_MODELS = []
        for i, model in enumerate(debater_models[:3]):  # Use up to 3 debaters
            Config.DEBATER_MODELS.append(ModelConfig(
                name=f"Debater_{i+1}",
                model=model,
                temperature=0.6,
                max_tokens=800,
                personality="analytical",
                system_prompt="You are a skilled debater."
            ))
        
        print(f"Config set - Orchestrator: {Config.ORCHESTRATOR_MODEL.model}")
        print(f"Config set - Debaters: {[d.model for d in Config.DEBATER_MODELS]}")
        
        print("4. Creating LLMDebateSystem instance...")
        debate_system = LLMDebateSystem()
        print("✅ LLMDebateSystem created successfully!")
        
        print("5. Testing async initialization...")
        await debate_system.initialize()
        print("✅ System initialized successfully!")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_init())

print("\n" + "="*50)
print("If you see ✅ symbols above, the system should work!")
print("If you see ❌ symbols, please install Ollama models:")
print("  ollama pull phi3:mini")
print("  ollama pull llama3.2:1b")
print("="*50)
