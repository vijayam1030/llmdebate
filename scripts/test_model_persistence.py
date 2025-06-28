"""
Test script to verify that models stay loaded between debates
and are only cleaned up when the application exits.
"""

import asyncio
import sys
import time
from main import LLMDebateSystem
from ollama_integration import ollama_manager

async def test_model_persistence():
    """Test that models persist across multiple debates"""
    print("🧪 Testing Model Persistence")
    print("=" * 50)
    
    system = LLMDebateSystem()
    
    # Initialize system
    print("📥 Initializing system...")
    if not await system.initialize():
        print("❌ System initialization failed")
        return
    
    print("✅ System initialized")
    
    # Check loaded models after initialization
    loaded_before = await ollama_manager.get_loaded_models()
    print(f"📊 Models loaded after init: {len(loaded_before)}")
    for model in loaded_before:
        print(f"  • {model}")
    
    # Run first debate
    print("\n🎭 Running first debate...")
    start_time = time.time()
    result1 = await system.conduct_debate("What is the best programming language?", max_rounds=2)
    first_duration = time.time() - start_time
    print(f"✅ First debate completed in {first_duration:.1f}s")
    print(f"   Status: {result1.final_status.value}")
    print(f"   Rounds: {result1.total_rounds}")
    
    # Check loaded models after first debate
    loaded_after_first = await ollama_manager.get_loaded_models()
    print(f"\n📊 Models loaded after first debate: {len(loaded_after_first)}")
    for model in loaded_after_first:
        print(f"  • {model}")
    
    # Verify models are still loaded
    if len(loaded_after_first) == len(loaded_before):
        print("✅ Models persisted after first debate")
    else:
        print("❌ Models were unloaded after first debate")
    
    # Run second debate (should be faster due to model persistence)
    print("\n🎭 Running second debate...")
    start_time = time.time()
    result2 = await system.conduct_debate("What are the benefits of renewable energy?", max_rounds=2)
    second_duration = time.time() - start_time
    print(f"✅ Second debate completed in {second_duration:.1f}s")
    print(f"   Status: {result2.final_status.value}")
    print(f"   Rounds: {result2.total_rounds}")
    
    # Check loaded models after second debate
    loaded_after_second = await ollama_manager.get_loaded_models()
    print(f"\n📊 Models loaded after second debate: {len(loaded_after_second)}")
    for model in loaded_after_second:
        print(f"  • {model}")
    
    # Performance comparison
    print("\n⚡ Performance Analysis:")
    print(f"   First debate:  {first_duration:.1f}s")
    print(f"   Second debate: {second_duration:.1f}s")
    
    if second_duration < first_duration * 0.8:  # Should be at least 20% faster
        print("✅ Second debate was significantly faster (model persistence working)")
    elif second_duration < first_duration:
        print("✅ Second debate was faster (model persistence likely working)")
    else:
        print("⚠️  Second debate wasn't faster (models may have been reloaded)")
    
    # Final verification
    if (len(loaded_after_first) == len(loaded_before) and 
        len(loaded_after_second) == len(loaded_before)):
        print("\n🎉 MODEL PERSISTENCE TEST PASSED")
        print("   • Models stay loaded between debates")
        print("   • Performance should improve on subsequent debates")
    else:
        print("\n❌ MODEL PERSISTENCE TEST FAILED")
        print("   • Models are being unloaded between debates")
    
    # Cleanup only at the end
    print("\n🧹 Cleaning up models (end of application)...")
    await system.cleanup()
    
    # Verify cleanup worked
    loaded_after_cleanup = await ollama_manager.get_loaded_models()
    print(f"📊 Models loaded after cleanup: {len(loaded_after_cleanup)}")
    
    if len(loaded_after_cleanup) == 0:
        print("✅ Cleanup successful - all models unloaded")
    else:
        print("⚠️  Some models may still be loaded after cleanup")
    
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_model_persistence())
    except KeyboardInterrupt:
        print("\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
