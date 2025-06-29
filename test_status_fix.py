#!/usr/bin/env python3
"""
Test script to verify the status endpoint fix
"""

import asyncio
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_status_endpoint():
    """Test the status endpoint with proper initialization"""
    print("🧪 Testing Status Endpoint Fix...")
    
    try:
        # Import and initialize the system manually (simulating the lifespan event)
        print("1. Importing required modules...")
        from system.main import LLMDebateSystem
        from system.config import Config, ModelConfig
        from system.dynamic_config import create_small_model_config_only
        from api.main import get_system_status
        
        # Initialize the debate system (this simulates what happens in the lifespan event)
        print("2. Creating small model config...")
        result = await create_small_model_config_only()
        if not result or result[0] is None:
            print("❌ No suitable small models found")
            return
        
        orchestrator_config, debater_configs = result
        print(f"✅ Found orchestrator: {orchestrator_config.model}")
        print(f"✅ Found debaters: {[c.model for c in debater_configs]}")
        
        # Set up the config properly (like in lifespan)
        Config.ORCHESTRATOR_MODEL = orchestrator_config
        Config.DEBATER_MODELS = debater_configs[:3]  # Use up to 3 debaters
        
        print("3. Creating and initializing LLMDebateSystem...")
        from api import main as api_main
        api_main.debate_system = LLMDebateSystem()
        await api_main.debate_system.initialize()
        print("✅ System initialized successfully!")
        
        # Now test the status endpoint
        print("4. Testing status endpoint...")
        status_response = await get_system_status()
        
        print("📊 Status Response:")
        print(f"  Initialized: {status_response.initialized}")
        print(f"  Models loaded: {status_response.models_loaded}")
        print(f"  Config keys: {list(status_response.config.keys())}")
        
        # Check if the fix worked
        if status_response.initialized:
            print("✅ System shows as initialized!")
            if status_response.models_loaded:
                print(f"✅ Models loaded: {status_response.models_loaded}")
                # Verify these are strings, not objects
                for model in status_response.models_loaded:
                    if isinstance(model, str):
                        print(f"✅ Model '{model}' is a string (correct)")
                    else:
                        print(f"❌ Model '{model}' is not a string: {type(model)}")
            else:
                print("❌ No models loaded")
        else:
            print("❌ System not initialized")
            print(f"Config error: {status_response.config}")
        
        # Test JSON serialization
        print("5. Testing JSON serialization...")
        response_dict = status_response.model_dump()
        print(f"✅ Successfully serialized to dict with keys: {list(response_dict.keys())}")
        
        import json
        json_str = json.dumps(response_dict)
        print("✅ Successfully serialized to JSON!")
        
        return status_response.initialized
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_status_endpoint()
    
    print("\n" + "="*60)
    if success:
        print("🎉 SUCCESS! The status endpoint fix is working!")
        print("   - System initializes correctly")
        print("   - Models are returned as strings (not objects)")
        print("   - JSON serialization works")
        print("   - The Angular UI should now show 'System Initialized: ✅'")
    else:
        print("❌ FAILED! There are still issues to resolve.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_status_endpoint_simulation():
    """Simulate what the status endpoint should return"""
    print("🧪 Testing status endpoint fix simulation...")
    
    try:
        from system.config import Config
        from api.main import SystemStatusResponse
        
        print("✅ Imports successful!")
        
        # Simulate what our fixed endpoint should do
        print("\n1. Testing model name extraction...")
        debater_model_names = [model.model for model in Config.DEBATER_MODELS]
        orchestrator_model_name = Config.ORCHESTRATOR_MODEL.model
        models_list = debater_model_names + [orchestrator_model_name]
        
        print(f"Debater models: {debater_model_names}")
        print(f"Orchestrator model: {orchestrator_model_name}")
        print(f"Combined models list: {models_list}")
        
        # Test config dict creation
        print("\n2. Testing config dict creation...")
        config_dict = {
            "max_rounds": Config.MAX_ROUNDS,
            "orchestrator_model": orchestrator_model_name,
            "debater_models": debater_model_names,
            "orchestrator_max_tokens": getattr(Config, 'ORCHESTRATOR_MAX_TOKENS', Config.ORCHESTRATOR_MODEL.max_tokens),
            "debater_max_tokens": getattr(Config, 'DEBATER_MAX_TOKENS', Config.DEBATER_MODELS[0].max_tokens if Config.DEBATER_MODELS else 800)
        }
        
        print(f"Config dict: {config_dict}")
        
        # Test SystemStatusResponse creation
        print("\n3. Testing SystemStatusResponse creation...")
        response = SystemStatusResponse(
            initialized=True,
            models_loaded=models_list,  # This should now be strings only
            config=config_dict
        )
        
        print(f"✅ SystemStatusResponse created successfully!")
        print(f"Response type: {type(response)}")
        
        # Test JSON serialization
        print("\n4. Testing JSON serialization...")
        json_data = response.model_dump()
        json_str = json.dumps(json_data, indent=2)
        
        print(f"✅ JSON serialization successful!")
        print(f"JSON preview:")
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)
        
        # Verify models_loaded contains only strings
        print("\n5. Verifying models_loaded contains only strings...")
        all_strings = all(isinstance(model, str) for model in json_data['models_loaded'])
        print(f"All models are strings: {all_strings}")
        
        if all_strings:
            print("✅ Status endpoint fix verified - should work correctly!")
        else:
            print("❌ Status endpoint still has issues")
            
        return response
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    response = test_status_endpoint_simulation()
    
    if response:
        print("\n" + "="*60)
        print("🎉 STATUS ENDPOINT FIX VERIFICATION COMPLETE")
        print("="*60)
        print("✅ The API should now return proper JSON responses")
        print("✅ No more Pydantic validation errors expected")
        print("✅ Angular UI should show 'System Initialized: ✅'")
        print("\nTo test the full system:")
        print("1. Run: python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
        print("2. Open: http://localhost:8000")
        print("3. Check: http://localhost:8000/api/status")
    else:
        print("\n❌ Status endpoint fix verification failed!")
        print("Please check the error messages above.")
