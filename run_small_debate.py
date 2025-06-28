"""
Run LLM Debate System with guaranteed small models only
"""

import asyncio
import sys
from main import LLMDebateSystem

async def run_small_model_debate():
    """Run debate system with forced small model configuration"""
    
    print("🎯 LLM Debate System - Small Models Only")
    print("=" * 50)
    
    # Force small model configuration by updating config first
    print("🔧 Setting up small model configuration...")
    from dynamic_config import create_small_model_config_only
    from config import Config
    
    # Create small model config and update global config
    orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
    
    if not orchestrator_config or len(debater_configs) < 2:
        print("❌ Failed to create small model configuration")
        print("💡 Ensure you have small models installed:")
        print("  ollama pull llama3.2:3b")
        print("  ollama pull gemma2:2b") 
        print("  ollama pull phi3:mini")
        print("  ollama pull tinyllama:1.1b")
        return
    
    # Update global config with small models
    Config.ORCHESTRATOR_MODEL = orchestrator_config
    Config.DEBATER_MODELS = debater_configs
    
    print(f"✅ Small model configuration created!")
    print(f"🧠 Orchestrator: {orchestrator_config.model}")
    print(f"👥 Debaters: {[d.model for d in debater_configs]}")
    
    # Create system with simple constructor
    system = LLMDebateSystem()
    
    # Initialize system
    print("🔧 Initializing with small models...")
    if not await system.initialize():
        print("❌ System initialization failed.")
        return
    
    print("✅ System initialized successfully!")
    print(f"\nActive Configuration:")
    print(f"  🧠 Orchestrator: {Config.ORCHESTRATOR_MODEL.model}")
    print(f"  👥 Debaters: {', '.join([d.model for d in Config.DEBATER_MODELS])}")
    
    # Get question from command line or interactive input
    if len(sys.argv) > 1:
        question = ' '.join(sys.argv[1:])
    else:
        question = input("\n🤔 Enter your debate question: ").strip()
    
    if not question:
        print("❌ No question provided")
        return
    
    print(f"\n🚀 Starting debate: {question}")
    print("=" * 60)
    
    try:
        # Conduct debate with max 3 rounds
        result = await system.conduct_debate(question, max_rounds=3)
        
        # Print results
        system.print_debate_summary(result)
        
    except Exception as e:
        print(f"❌ Debate error: {e}")
        return

if __name__ == "__main__":
    try:
        asyncio.run(run_small_model_debate())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
