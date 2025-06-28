#!/usr/bin/env python3
"""
Quick test of the 3-round debate system
"""

import asyncio
import sys
from main import LLMDebateSystem
from dynamic_config import create_small_model_config_only
from config import Config

async def quick_test():
    print("🚀 Quick 3-Round Debate Test")
    print("=" * 40)
    
    # Check config
    print(f"📋 Config MAX_ROUNDS: {Config.MAX_ROUNDS}")
    
    # Setup small models  
    print("🔧 Setting up small models...")
    orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
    
    if not orchestrator_config:
        print("❌ Failed to get small model config")
        return
        
    Config.ORCHESTRATOR_MODEL = orchestrator_config
    Config.DEBATER_MODELS = debater_configs
    
    print(f"✅ Models: {orchestrator_config.model} + {len(debater_configs)} debaters")
    
    # Initialize system
    system = LLMDebateSystem()
    if not await system.initialize():
        print("❌ Initialization failed")
        return
        
    print("✅ System ready")
    
    # Quick debate with 3 rounds
    question = "Should we use renewable energy?"
    print(f"\n🎭 Debate question: {question}")
    print("⏱️ Running with MAX 3 ROUNDS...")
    
    try:
        result = await system.conduct_debate(question, max_rounds=3)
        
        print(f"\n📊 RESULTS:")
        print(f"• Status: {result.final_status}")  
        print(f"• Rounds completed: {result.total_rounds}")
        print(f"• Expected: ≤ 3 rounds")
        
        if result.total_rounds <= 3:
            print("✅ SUCCESS: Debate stopped within 3 rounds!")
        else:
            print(f"❌ FAILED: Ran {result.total_rounds} rounds")
            
        await system.cleanup()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(quick_test())
