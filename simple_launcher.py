#!/usr/bin/env python3
"""
Simple CLI launcher for LLM Debate System with small models
"""

import asyncio
import sys

async def main():
    print("🎯 LLM Debate System - Simple Launcher")
    print("=" * 40)
    
    # Setup small models
    print("🔧 Configuring for small models...")
    from dynamic_config import create_small_model_config_only
    from config import Config
    
    orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
    
    if orchestrator_config and len(debater_configs) >= 2:
        Config.ORCHESTRATOR_MODEL = orchestrator_config
        Config.DEBATER_MODELS = debater_configs
        print(f"✅ Using: {orchestrator_config.model} + {len(debater_configs)} debaters")
    else:
        print("❌ Small model setup failed")
        return
    
    # Run the system
    from main import LLMDebateSystem
    system = LLMDebateSystem()
    
    print("🚀 Initializing...")
    if await system.initialize():
        print("✅ Ready!")
        
        # Get question
        if len(sys.argv) > 1:
            question = ' '.join(sys.argv[1:])
        else:
            question = input("\n💭 Your question: ")
        
        # Run debate (max 3 rounds)
        print(f"\n🎭 Debating: {question}")
        result = await system.conduct_debate(question, max_rounds=3)
        system.print_debate_summary(result)
        
        await system.cleanup()
    else:
        print("❌ Initialization failed")

if __name__ == "__main__":
    asyncio.run(main())
