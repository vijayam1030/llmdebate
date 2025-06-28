"""
Pre-run model checker for the LLM Debate System
This script verifies that all required Ollama models are available locally
"""

import asyncio
import sys
import logging
from typing import List, Dict, Tuple
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import Config
from ollama_integration import ollama_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ModelChecker:
    """Check and manage Ollama model availability"""
    
    def __init__(self):
        self.required_models = Config.get_available_models()
        self.model_info = self._get_model_info()
    
    def _get_model_info(self) -> Dict[str, Dict]:
        """Get detailed information about each required model"""
        model_info = {}
        
        # Orchestrator model
        orchestrator = Config.ORCHESTRATOR_MODEL
        model_info[orchestrator.model] = {
            'role': 'Orchestrator',
            'name': orchestrator.name,
            'personality': orchestrator.personality,
            'size': '70B parameters',
            'critical': True,
            'description': 'Master debate coordinator and consensus analyzer'
        }
        
        # Debater models
        for debater in Config.DEBATER_MODELS:
            size_map = {
                'llama3.1:8b': '8B parameters',
                'mistral:7b': '7B parameters', 
                'phi3:medium': '~14B parameters'
            }
            
            model_info[debater.model] = {
                'role': 'Debater',
                'name': debater.name,
                'personality': debater.personality,
                'size': size_map.get(debater.model, 'Unknown size'),
                'critical': True,
                'description': f'{debater.personality} debater'
            }
        
        return model_info
    
    async def check_ollama_status(self) -> bool:
        """Check if Ollama server is running"""
        print("🔌 Checking Ollama server status...")
        
        try:
            connected = await ollama_manager.check_ollama_connection()
            if connected:
                print("✅ Ollama server is running")
                return True
            else:
                print("❌ Ollama server is not responding")
                print("💡 Please start Ollama with: ollama serve")
                return False
        except Exception as e:
            print(f"❌ Error checking Ollama: {e}")
            return False
    
    async def get_available_models(self) -> List[str]:
        """Get list of currently available models"""
        try:
            return await ollama_manager.list_available_models()
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    async def check_model_availability(self) -> Tuple[List[str], List[str]]:
        """Check which models are available and which are missing"""
        print("\n🤖 Checking model availability...")
        
        available_models = await self.get_available_models()
        
        found_models = []
        missing_models = []
        
        for model in self.required_models:
            info = self.model_info[model]
            if model in available_models:
                print(f"✅ {model} - {info['name']} ({info['size']})")
                found_models.append(model)
            else:
                print(f"❌ {model} - {info['name']} ({info['size']}) - MISSING")
                missing_models.append(model)
        
        return found_models, missing_models
    
    async def estimate_download_sizes(self, missing_models: List[str]) -> Dict[str, str]:
        """Estimate download sizes for missing models"""
        # Approximate sizes based on model names
        size_estimates = {
            'llama3.1:70b': '40GB',
            'llama3.1:8b': '4.7GB',
            'mistral:7b': '4.1GB',
            'phi3:medium': '7.9GB'
        }
        
        return {model: size_estimates.get(model, 'Unknown') for model in missing_models}
    
    async def download_missing_models(self, missing_models: List[str], auto_download: bool = False) -> bool:
        """Download missing models with user confirmation"""
        if not missing_models:
            return True
        
        print(f"\n📥 Found {len(missing_models)} missing models")
        
        # Show download estimates
        size_estimates = await self.estimate_download_sizes(missing_models)
        total_estimated_size = 0
        
        print("\nModels to download:")
        for model in missing_models:
            info = self.model_info[model]
            size = size_estimates[model]
            print(f"  • {model} ({info['name']}) - ~{size}")
            
            # Rough size calculation for total estimate
            if 'GB' in size:
                try:
                    size_num = float(size.replace('GB', ''))
                    total_estimated_size += size_num
                except:
                    pass
        
        if total_estimated_size > 0:
            print(f"\nEstimated total download: ~{total_estimated_size:.1f}GB")
        
        print("\n⚠️  Note: Large models may take significant time to download")
        print("💡 You can also download manually with: ollama pull <model_name>")
        
        if not auto_download:
            response = input("\nDo you want to download missing models now? (y/n): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ Skipping model downloads")
                return False
        
        print("\n🚀 Starting model downloads...")
        success_count = 0
        
        for model in missing_models:
            info = self.model_info[model]
            print(f"\n📦 Downloading {model} ({info['name']})...")
            
            try:
                success = await ollama_manager.pull_model(model)
                if success:
                    print(f"✅ Successfully downloaded {model}")
                    success_count += 1
                else:
                    print(f"❌ Failed to download {model}")
            except Exception as e:
                print(f"❌ Error downloading {model}: {e}")
        
        if success_count == len(missing_models):
            print(f"\n🎉 All {success_count} models downloaded successfully!")
            return True
        else:
            print(f"\n⚠️  Downloaded {success_count}/{len(missing_models)} models")
            return False
    
    def print_model_summary(self):
        """Print a summary of all required models"""
        print("\n📋 Required Models for LLM Debate System:")
        print("=" * 60)
        
        print("\n🧠 ORCHESTRATOR:")
        orchestrator = Config.ORCHESTRATOR_MODEL
        info = self.model_info[orchestrator.model]
        print(f"  Model: {orchestrator.model}")
        print(f"  Role: {info['description']}")
        print(f"  Size: {info['size']}")
        print(f"  Temperature: {orchestrator.temperature}")
        
        print("\n👥 DEBATERS:")
        for i, debater in enumerate(Config.DEBATER_MODELS, 1):
            info = self.model_info[debater.model]
            print(f"\n  {i}. {debater.name}")
            print(f"     Model: {debater.model}")
            print(f"     Personality: {debater.personality}")
            print(f"     Size: {info['size']}")
            print(f"     Temperature: {debater.temperature}")
        
        print("\n" + "=" * 60)
    
    async def run_full_check(self, auto_download: bool = False) -> bool:
        """Run complete model availability check"""
        print("🎯 LLM Debate System - Model Checker")
        print("=" * 50)
        
        # Show model summary
        self.print_model_summary()
        
        # Check Ollama status
        if not await self.check_ollama_status():
            return False
        
        # Check model availability
        found_models, missing_models = await self.check_model_availability()
        
        if not missing_models:
            print(f"\n🎉 All {len(found_models)} required models are available!")
            print("✅ System is ready to run")
            return True
        
        # Handle missing models
        print(f"\n⚠️  Missing {len(missing_models)} required models")
        
        if auto_download or await self.download_missing_models(missing_models, auto_download):
            # Re-check after download
            print("\n🔄 Re-checking model availability...")
            found_models, missing_models = await self.check_model_availability()
            
            if not missing_models:
                print("\n🎉 All models are now available!")
                print("✅ System is ready to run")
                return True
            else:
                print(f"\n❌ Still missing {len(missing_models)} models")
                return False
        
        return False

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check LLM Debate System model availability")
    parser.add_argument("--auto-download", action="store_true", 
                       help="Automatically download missing models without prompting")
    parser.add_argument("--list-models", action="store_true",
                       help="List all required models and exit")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check availability, don't offer to download")
    
    args = parser.parse_args()
    
    checker = ModelChecker()
    
    if args.list_models:
        checker.print_model_summary()
        return 0
    
    try:
        if args.check_only:
            # Check Ollama status
            if not await checker.check_ollama_status():
                return 1
            
            # Check model availability
            found_models, missing_models = await checker.check_model_availability()
            
            if missing_models:
                print(f"\n❌ {len(missing_models)} models are missing")
                print("Run without --check-only to download them")
                return 1
            else:
                print(f"\n✅ All {len(found_models)} models are available")
                return 0
        else:
            # Run full check with optional auto-download
            success = await checker.run_full_check(args.auto_download)
            return 0 if success else 1
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Model checker error:")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
