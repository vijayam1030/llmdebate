#!/usr/bin/env python3
"""
Quick test of DirectOllamaLLM
"""

import asyncio
from dynamic_config import create_small_model_config_only
from ollama_integration import DirectOllamaLLM

async def test_direct_llm():
    """Test DirectOllamaLLM implementation"""
    print("🧪 Testing DirectOllamaLLM...")
    
    try:
        # Get small model config
        orchestrator_config, debater_configs = await create_small_model_config_only(3.0)
        
        if not orchestrator_config:
            print("❌ No orchestrator config available")
            return
        
        # Create a DirectOllamaLLM instance
        llm = DirectOllamaLLM(orchestrator_config)
        
        # Test it
        print(f"📡 Testing model: {orchestrator_config.model}")
        response = await llm.ainvoke("What are the benefits of renewable energy? Answer in 2-3 sentences.")
        
        print(f"✅ Response received: {response[:100]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_llm())
