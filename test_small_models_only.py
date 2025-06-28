"""
Test the debate system with small models only
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import LLMDebateSystem

async def test_small_models():
    """Test the system with small models configuration"""
    print("🧪 Testing LLM Debate System with Small Models")
    print("=" * 50)
    
    # Create system with small models forced
    system = LLMDebateSystem(
        use_dynamic_config=True, 
        prefer_small_models=True, 
        max_size_gb=3.0,  # Even more restrictive
        lightweight_mode=True  # Most memory efficient
    )
    
    try:
        print("🔧 Initializing system with small models...")
        if await system.initialize():
            print("✅ System initialized successfully!")
            
            print(f"\n📋 Active Configuration:")
            if system.orchestrator_config:
                print(f"  🧠 Orchestrator: {system.orchestrator_config.model}")
                print(f"  👥 Debaters:")
                for debater in system.debater_configs:
                    print(f"    • {debater.model} ({debater.personality})")
            
            # Test a simple question
            print(f"\n🎯 Testing with a simple question...")
            result = await system.conduct_debate("Should we use renewable energy?", max_rounds=2)
            
            print(f"\n✅ Debate completed!")
            print(f"Status: {result.final_status}")
            print(f"Rounds: {result.total_rounds}")
            
            if result.final_summary:
                print(f"Summary: {result.final_summary[:200]}...")
            
        else:
            print("❌ System initialization failed")
            print("\n💡 Ensure you have these small models installed:")
            print("  ollama pull llama3.2:3b")
            print("  ollama pull gemma2:2b") 
            print("  ollama pull phi3:mini")
            print("  ollama pull tinyllama:1.1b")
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Always cleanup
        await system.cleanup()

if __name__ == "__main__":
    asyncio.run(test_small_models())
