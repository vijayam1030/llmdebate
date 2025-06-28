"""
Script to help find, download, and test small models under 4GB for the LLM debate system
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def list_recommended_small_models():
    """List recommended models under 4GB"""
    print("🤖 Recommended Small Models (Under 4GB)")
    print("=" * 50)
    
    small_models = [
        {
            "name": "llama3.2:3b",
            "size": "~1.9GB",
            "description": "Latest Llama 3.2 3B - excellent for orchestration and debates",
            "download_cmd": "ollama pull llama3.2:3b"
        },
        {
            "name": "phi3:mini",
            "size": "~2.2GB", 
            "description": "Microsoft Phi-3 Mini - very capable for its size",
            "download_cmd": "ollama pull phi3:mini"
        },
        {
            "name": "qwen2.5:3b",
            "size": "~1.9GB",
            "description": "Qwen 2.5 3B - good analytical capabilities",
            "download_cmd": "ollama pull qwen2.5:3b"
        },
        {
            "name": "gemma2:2b",
            "size": "~1.4GB",
            "description": "Google Gemma 2B - efficient and creative",
            "download_cmd": "ollama pull gemma2:2b"
        },
        {
            "name": "tinyllama:1.1b",
            "size": "~0.6GB",
            "description": "TinyLlama - extremely lightweight for basic debates",
            "download_cmd": "ollama pull tinyllama:1.1b"
        },
        {
            "name": "llama3.2:1b",
            "size": "~0.6GB",
            "description": "Llama 3.2 1B - very small but functional",
            "download_cmd": "ollama pull llama3.2:1b"
        },
        {
            "name": "starcoder2:3b",
            "size": "~1.8GB",
            "description": "StarCoder2 3B - good for analytical discussions",
            "download_cmd": "ollama pull starcoder2:3b"
        }
    ]
    
    for i, model in enumerate(small_models, 1):
        print(f"\n{i}. {model['name']} ({model['size']})")
        print(f"   {model['description']}")
        print(f"   💻 {model['download_cmd']}")

async def check_current_small_models():
    """Check which small models are currently available"""
    try:
        from ollama_integration import ollama_manager
        from dynamic_config import DynamicModelSelector
        
        print("\n🔍 Checking current available models...")
        
        if not await ollama_manager.check_ollama_connection():
            print("❌ Ollama not connected. Please start with: ollama serve")
            return False
        
        selector = DynamicModelSelector()
        available = await selector.scan_available_models()
        
        if not available:
            print("❌ No models found")
            return False
        
        print(f"Found {len(available)} total models")
        
        # Check models under 4GB
        small_models = selector.get_models_under_size_limit(4.0)
        if small_models:
            print(f"\n✅ Models under 4GB ({len(small_models)}):")
            for model in small_models:
                info = selector.get_model_info(model)
                if info:
                    print(f"  • {model} ({info.estimated_params}) - {info.personality_match or 'general'}")
                else:
                    print(f"  • {model} (unknown size)")
        else:
            print("\n❌ No models under 4GB found")
        
        return len(small_models) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_small_model_config():
    """Test creating a configuration with only small models"""
    try:
        from dynamic_config import create_small_model_config_only
        
        print("\n🧪 Testing Small Model Configuration")
        print("=" * 50)
        
        orchestrator, debaters = await create_small_model_config_only(max_size_gb=4.0)
        
        if orchestrator and len(debaters) >= 2:
            print(f"\n✅ Small model configuration successful!")
            print(f"🧠 Orchestrator: {orchestrator.model}")
            print(f"👥 Debaters ({len(debaters)}):")
            for i, debater in enumerate(debaters, 1):
                print(f"   {i}. {debater.model} ({debater.personality})")
            return True
        else:
            print(f"\n❌ Could not create small model configuration")
            print("Need at least 1 orchestrator and 2 debaters under 4GB")
            return False
            
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")
        return False

async def download_essential_small_models():
    """Download essential small models for debate system"""
    print("\n📥 Downloading Essential Small Models")
    print("=" * 50)
    
    essential_models = [
        "llama3.2:3b",     # Best balance of capability/size
        "phi3:mini",       # Very capable Microsoft model
        "gemma2:2b",       # Good creative perspective
        "tinyllama:1.1b"   # Backup lightweight option
    ]
    
    print("This will download approximately 6.1GB total:")
    for model in essential_models:
        print(f"  • {model}")
    
    confirm = input("\nProceed with download? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Download cancelled")
        return False
    
    import subprocess
    
    for model in essential_models:
        print(f"\n📥 Downloading {model}...")
        try:
            result = subprocess.run(
                ["ollama", "pull", model],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            if result.returncode == 0:
                print(f"✅ {model} downloaded successfully")
            else:
                print(f"❌ Failed to download {model}: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"⏱️ Download of {model} timed out")
        except Exception as e:
            print(f"❌ Error downloading {model}: {e}")
    
    return True

async def main():
    """Main function"""
    print("🤖 LLM Debate System - Small Models Helper")
    print("=" * 60)
    
    while True:
        print("\nChoose an option:")
        print("1. List recommended small models (under 4GB)")
        print("2. Check current available small models")
        print("3. Test small model configuration")
        print("4. Download essential small models")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            await list_recommended_small_models()
        elif choice == "2":
            await check_current_small_models()
        elif choice == "3":
            await test_small_model_config()
        elif choice == "4":
            await download_essential_small_models()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
