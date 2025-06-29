#!/usr/bin/env python3
"""
Test individual components to isolate the issue
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Testing individual components...")

async def test_components():
    try:
        print("1. Testing configuration...")
        from system.config import Config
        print(f"✅ MAX_ROUNDS: {Config.MAX_ROUNDS}")
        print(f"✅ CONSENSUS_THRESHOLD: {Config.CONSENSUS_THRESHOLD}")
        
        print("\n2. Testing dynamic config...")
        from system.dynamic_config import create_small_model_config_only
        orchestrator_config, debater_configs = await create_small_model_config_only()
        
        if not orchestrator_config:
            print("❌ No models found")
            return
            
        print(f"✅ Found {len(debater_configs)} debater models")
        
        print("\n3. Testing model loading...")
        from backend.ollama_integration import model_factory
        
        # Set the config properly
        from system.config import ModelConfig
        Config.ORCHESTRATOR_MODEL = orchestrator_config
        Config.DEBATER_MODELS = debater_configs
        
        await model_factory.initialize_all_models()
        print("✅ Models loaded successfully")
        
        print("\n4. Testing simple LLM call...")
        from backend.ollama_integration import CustomOllamaLLM
        
        # Test a simple LLM call
        llm = CustomOllamaLLM(model=orchestrator_config.model)
        simple_prompt = "Please say 'Hello, this is a test' and nothing else."
        
        print("   Making test LLM call...")
        response = await llm.ainvoke(simple_prompt)
        print(f"✅ LLM Response: {response[:100]}...")
        
        print("\n5. Testing debater agent...")
        from backend.agents import DebaterAgent
        from backend.models import MCPContext
        
        mcp_context = MCPContext()
        agent = DebaterAgent(debater_configs[0], mcp_context)
        
        test_question = "Should AI be regulated?"
        print(f"   Testing agent with question: {test_question}")
        
        response = await agent.generate_initial_response(test_question)
        print(f"✅ Agent Response: {response.response[:100]}...")
        print(f"   Agent: {response.debater_name}")
        print(f"   Model: {response.model}")
        
        print("\n6. Testing consensus engine...")
        from backend.consensus_engine import consensus_engine
        
        # Create dummy responses for testing
        dummy_responses = [
            type('obj', (object,), {'response': 'AI should be regulated for safety'})(),
            type('obj', (object,), {'response': 'AI regulation is necessary for public welfare'})(),
            type('obj', (object,), {'response': 'We need AI regulation to prevent misuse'})()
        ]
        
        consensus_analysis = consensus_engine.analyze_consensus(dummy_responses)
        print(f"✅ Consensus Analysis: {consensus_analysis.average_similarity:.3f}")
        print(f"   Consensus reached: {consensus_analysis.consensus_reached}")
        
        print("\n7. Testing simple debate workflow...")
        from backend.debate_workflow import debate_workflow
        
        print("   Running minimal debate...")
        try:
            result = await debate_workflow.conduct_debate(
                question="Should AI be regulated?",
                max_rounds=1  # Just one round to test
            )
            print(f"✅ Debate Result: {result.final_status}")
            print(f"   Total rounds: {result.total_rounds}")
            print(f"   Consensus reached: {result.consensus_reached}")
            if result.final_summary:
                print(f"   Summary: {result.final_summary[:100]}...")
            else:
                print("   No summary generated")
                
        except Exception as e:
            print(f"❌ Debate failed: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_components())

print("\n" + "="*50)
print("Component testing completed.")
print("="*50)
