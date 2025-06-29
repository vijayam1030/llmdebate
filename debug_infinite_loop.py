#!/usr/bin/env python3
"""
Debug script to identify infinite loop issues in the debate system
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
import signal

# Add timeout handling
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

async def test_simple_ollama_call():
    """Test a simple Ollama call to see if that's where it hangs"""
    print("Testing simple Ollama call...")
    
    try:
        import httpx
        
        payload = {
            "model": "gemma2:2b",
            "prompt": "Hello, respond with exactly one word: 'working'",
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 5
            }
        }
        
        # Set a 10 second timeout
        timeout = httpx.Timeout(10.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            print("Making request to Ollama...")
            response = await client.post(
                "http://host.docker.internal:11434/api/generate",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Ollama responded: {result.get('response', '').strip()}")
                return True
            else:
                print(f"❌ Ollama error: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_debate_initialization():
    """Test just the debate initialization without actually running it"""
    print("\nTesting debate initialization...")
    
    try:
        from backend.models import DebateState
        from system.config import Config
        
        # Create initial state
        initial_state = DebateState(
            question="Test question",
            max_rounds=1,  # Limit to 1 round
            consensus_threshold=Config.CONSENSUS_THRESHOLD
        )
        
        print(f"✅ DebateState created: {initial_state.question}")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_agents_creation():
    """Test creating agents without calling them"""
    print("\nTesting agent creation...")
    
    try:
        from backend.agents import DebaterAgent, OrchestratorAgent
        from backend.models import MCPContext
        from system.config import Config
        
        # Create MCP context
        mcp_context = MCPContext()
        
        # Create one debater agent
        debater_config = Config.DEBATER_MODELS[0]
        debater_agent = DebaterAgent(debater_config, mcp_context)
        
        # Create orchestrator agent
        orchestrator_agent = OrchestratorAgent(mcp_context)
        
        print(f"✅ Agents created: {debater_agent.config.name}, orchestrator")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_workflow_creation():
    """Test creating the workflow graph without running it"""
    print("\nTesting workflow creation...")
    
    try:
        from backend.debate_workflow import DebateWorkflow
        
        # Create workflow
        workflow = DebateWorkflow()
        
        print(f"✅ Workflow created with {len(workflow.debater_agents)} debaters")
        return True
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def test_single_agent_call():
    """Test calling a single agent with timeout"""
    print("\nTesting single agent call...")
    
    try:
        from backend.agents import DebaterAgent
        from backend.models import MCPContext
        from system.config import Config
        
        # Create agent
        mcp_context = MCPContext()
        debater_config = Config.DEBATER_MODELS[0]
        agent = DebaterAgent(debater_config, mcp_context)
        
        print(f"Testing {agent.config.name} with model {agent.config.model}...")
        
        # Create a task with timeout
        async def call_agent():
            return await agent.generate_initial_response("What is 1+1?")
        
        # Use asyncio.wait_for with timeout
        response = await asyncio.wait_for(call_agent(), timeout=30.0)
        
        print(f"✅ Agent responded: {response.response[:100]}...")
        return True
        
    except asyncio.TimeoutError:
        print("❌ Agent call timed out after 30 seconds - THIS IS THE PROBLEM!")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def run_all_tests():
    """Run all diagnostic tests"""
    print("🔍 Debugging infinite loop issues...")
    print("=" * 50)
    
    tests = [
        ("Ollama Call", test_simple_ollama_call),
        ("Debate Init", test_debate_initialization),
        ("Agents Creation", test_agents_creation),
        ("Workflow Creation", test_workflow_creation),
        ("Single Agent Call", test_single_agent_call),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🧪 Running {test_name}...")
            # Add timeout to each test
            result = await asyncio.wait_for(test_func(), timeout=60.0)
            results[test_name] = result
        except asyncio.TimeoutError:
            print(f"⏰ {test_name} TIMED OUT - This is likely where the infinite loop occurs!")
            results[test_name] = False
            break  # Stop at first timeout
        except Exception as e:
            print(f"💥 {test_name} CRASHED: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    # Identify the problem
    failed_tests = [name for name, result in results.items() if not result]
    if failed_tests:
        print(f"\n🚨 PROBLEM IDENTIFIED: {failed_tests[0]} is where the system hangs!")
        if "Ollama Call" in failed_tests:
            print("💡 SOLUTION: Check Ollama connectivity from Docker container")
        elif "Single Agent Call" in failed_tests:
            print("💡 SOLUTION: Check agent timeout settings and model response times")
        else:
            print("💡 SOLUTION: Check the failed component for infinite loops")
    else:
        print("\n✅ All tests passed - the issue might be in the workflow coordination")

if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
