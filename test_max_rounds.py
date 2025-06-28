#!/usr/bin/env python3
"""
Test script to verify max rounds functionality
"""

import asyncio
import logging

# Configure logging to see debug info
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_max_rounds():
    print("🧪 Testing Max Rounds Functionality")
    print("=" * 40)
    
    # Setup small models
    print("🔧 Configuring for small models...")
    from dynamic_config import create_small_model_config_only
    from config import Config
    
    orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
    
    if orchestrator_config and len(debater_configs) >= 2:
        Config.ORCHESTRATOR_MODEL = orchestrator_config
        Config.DEBATER_MODELS = debater_configs[:2]  # Use only 2 debaters for faster testing
        print(f"✅ Using: {orchestrator_config.model} + {len(Config.DEBATER_MODELS)} debaters")
    else:
        print("❌ Small model setup failed")
        return
    
    # Test the system
    from main import LLMDebateSystem
    system = LLMDebateSystem()
    
    print("🚀 Initializing...")
    if await system.initialize():
        print("✅ Ready!")
        
        # Test with max_rounds=2 (should stop after 2 rounds)
        print(f"\n🎭 Testing with max_rounds=2...")
        question = "Should we use solar power more?"
        
        print(f"Question: {question}")
        result = await system.conduct_debate(question, max_rounds=2)
        
        print(f"\n📊 Results:")
        print(f"• Status: {result.final_status}")
        print(f"• Total rounds: {result.total_rounds}")
        print(f"• Expected: Should stop at round 2")
        
        if result.total_rounds <= 2:
            print("✅ MAX ROUNDS TEST PASSED")
        else:
            print("❌ MAX ROUNDS TEST FAILED - exceeded limit")
        
        # Print summary
        system.print_debate_summary(result)
        
        await system.cleanup()
    else:
        print("❌ Initialization failed")

if __name__ == "__main__":
    asyncio.run(test_max_rounds())
