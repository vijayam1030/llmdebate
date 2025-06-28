"""
Quick test to use small models only
"""

import asyncio
from dynamic_config import create_small_model_config_only

async def test_small_models():
    print("🔧 Testing small model configuration...")
    
    try:
        orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
        
        if orchestrator_config and len(debater_configs) >= 2:
            print("✅ Small model configuration successful!")
            print(f"🧠 Orchestrator: {orchestrator_config.model}")
            print(f"👥 Debaters:")
            for debater in debater_configs:
                print(f"  • {debater.model} ({debater.personality})")
            return True
        else:
            print("❌ Failed to create small model configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_small_models())
    if success:
        print("\n🎯 Small model system is ready!")
    else:
        print("\n❌ Small model system needs setup")
