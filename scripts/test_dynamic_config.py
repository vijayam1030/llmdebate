"""
Quick test script to validate the dynamic configuration system
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_dynamic_config():
    """Test the dynamic configuration system"""
    print("🧪 Testing Dynamic Configuration System")
    print("=" * 50)
    
    try:
        from ollama_integration import ollama_manager
        from dynamic_config import create_dynamic_debate_config
        
        # Check Ollama connection
        print("1. Checking Ollama connection...")
        connected = await ollama_manager.check_ollama_connection()
        if not connected:
            print("❌ Ollama not connected. Please start Ollama with: ollama serve")
            return False
        print("✅ Ollama is connected")
        
        # Get available models
        print("\n2. Getting available models...")
        available_models = await ollama_manager.list_available_models()
        print(f"Found {len(available_models)} models:")
        for model in available_models:
            print(f"  • {model}")
        
        if not available_models:
            print("❌ No models available. Please install some models first.")
            print("💡 Suggested commands:")
            print("  ollama pull llama3.1:8b")
            print("  ollama pull mistral:7b")
            print("  ollama pull phi3:medium")
            return False
        
        # Test dynamic configuration
        print("\n3. Creating dynamic configuration...")
        orchestrator_config, debater_configs = await create_dynamic_debate_config()
        
        if not orchestrator_config:
            print("❌ Could not create orchestrator configuration")
            return False
        
        if len(debater_configs) < 2:
            print(f"❌ Insufficient debaters (found {len(debater_configs)}, need at least 2)")
            return False
        
        print("✅ Dynamic configuration created successfully!")
        print(f"\n📋 Configuration Summary:")
        print(f"  🧠 Orchestrator: {orchestrator_config.model}")
        print(f"  👥 Debaters ({len(debater_configs)}):")
        for i, debater in enumerate(debater_configs, 1):
            print(f"    {i}. {debater.model} ({debater.personality})")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_main_system():
    """Test the main LLM debate system"""
    print("\n🎯 Testing Main System Initialization")
    print("=" * 50)
    
    try:
        from main import LLMDebateSystem
        
        # Test with dynamic config
        print("Testing with dynamic configuration...")
        system = LLMDebateSystem(use_dynamic_config=True)
        
        success = await system.initialize()
        if success:
            print("✅ System initialized successfully with dynamic config!")
            
            if hasattr(system, 'orchestrator_config') and system.orchestrator_config:
                print(f"  🧠 Active orchestrator: {system.orchestrator_config.model}")
            if hasattr(system, 'debater_configs') and system.debater_configs:
                print(f"  👥 Active debaters: {', '.join([d.model for d in system.debater_configs])}")
            
            return True
        else:
            print("❌ System initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing main system: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 LLM Debate System - Configuration Test")
    print("=" * 60)
    
    # Test dynamic config
    config_success = await test_dynamic_config()
    
    if config_success:
        # Test main system
        system_success = await test_main_system()
        
        if system_success:
            print("\n🎉 All tests passed! The system is ready to use.")
            print("\n🚀 Next steps:")
            print("  python main.py                    # Interactive mode")
            print("  python run.py                     # Smart launcher")
            print("  debate.bat                        # Windows launcher")
            print("  ./debate.sh                       # Unix launcher")
        else:
            print("\n⚠️ Configuration works but system initialization failed")
    else:
        print("\n❌ Configuration test failed")
        print("Please check your Ollama installation and available models")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal test error: {e}")
        sys.exit(1)
