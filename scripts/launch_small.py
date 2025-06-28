"""
Simple launcher that configures small models and runs the debate system
"""

import asyncio
import sys

async def main():
    print("🎯 LLM Debate System - Small Model Launcher")
    print("=" * 50)
    
    # Set up small model configuration
    print("🔧 Configuring small models...")
    
    try:
        from dynamic_config import create_small_model_config_only
        from config import Config
        from main import LLMDebateSystem
        
        # Create small model config
        orchestrator_config, debater_configs = await create_small_model_config_only(4.0)
        
        if not orchestrator_config or len(debater_configs) < 2:
            print("❌ Failed to create small model configuration")
            print("💡 Install small models:")
            print("  ollama pull llama3.2:3b")
            print("  ollama pull gemma2:2b") 
            print("  ollama pull phi3:mini")
            print("  ollama pull tinyllama:1.1b")
            return
        
        # Update global config
        Config.ORCHESTRATOR_MODEL = orchestrator_config
        Config.DEBATER_MODELS = debater_configs
        
        print(f"✅ Configuration ready!")
        print(f"🧠 Orchestrator: {orchestrator_config.model}")
        print(f"👥 Debaters: {[d.model for d in debater_configs]}")
        
        # Create and initialize system
        system = LLMDebateSystem()
        
        print("\n🚀 Initializing system...")
        if not await system.initialize():
            print("❌ System initialization failed")
            return
        
        print("✅ System ready!")
        
        # Get question from command line or interactive
        if len(sys.argv) > 1:
            question = ' '.join(sys.argv[1:])
            print(f"\n🤔 Debating: {question}")
            
            result = await system.conduct_debate(question)
            
            print(f"\n✅ Debate completed!")
            print(f"Status: {result.final_status.value}")
            print(f"Rounds: {result.total_rounds}")
            
            if result.final_summary:
                print(f"\n📋 Summary:")
                print(result.final_summary)
        else:
            print("\n🎮 Interactive Mode")
            print("Type your questions (or 'quit' to exit):")
            
            while True:
                question = input("\n🤔 Question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not question:
                    continue
                
                try:
                    result = await system.conduct_debate(question, max_rounds=3)
                    print(f"\n✅ Status: {result.final_status.value}")
                    if result.final_summary:
                        print(f"📋 Summary: {result.final_summary[:200]}...")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        # Cleanup
        await system.cleanup()
        print("\n👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
