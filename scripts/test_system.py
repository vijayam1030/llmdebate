"""
Test script for the LLM Debate System
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from main import LLMDebateSystem
from ollama_integration import ollama_manager
from config import Config

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ollama_connection():
    """Test Ollama connection"""
    print("🔌 Testing Ollama connection...")
    
    connected = await ollama_manager.check_ollama_connection()
    if connected:
        print("✅ Ollama is connected and running")
        
        # List available models
        models = await ollama_manager.list_available_models()
        print(f"📋 Available models: {len(models)}")
        for model in models:
            print(f"  • {model}")
        
        return True
    else:
        print("❌ Ollama connection failed")
        print("Please ensure Ollama is running: ollama serve")
        return False

async def test_model_availability():
    """Test if required models are available"""
    print("\n🤖 Testing model availability...")
    
    required_models = Config.get_available_models()
    available_models = await ollama_manager.list_available_models()
    
    all_available = True
    for model in required_models:
        if model in available_models:
            print(f"✅ {model}")
        else:
            print(f"❌ {model} (missing)")
            all_available = False
    
    if not all_available:
        print("\n⚠️ Some models are missing. They will be downloaded automatically when needed.")
        print("To download manually, run:")
        for model in required_models:
            if model not in available_models:
                print(f"  ollama pull {model}")
    
    return all_available

async def test_system_initialization():
    """Test system initialization"""
    print("\n🚀 Testing system initialization...")
    
    try:
        system = LLMDebateSystem()
        success = await system.initialize()
        
        if success:
            print("✅ System initialized successfully")
            return True
        else:
            print("❌ System initialization failed")
            return False
            
    except Exception as e:
        print(f"❌ System initialization error: {e}")
        return False

async def test_simple_debate():
    """Test a simple debate"""
    print("\n🎯 Testing simple debate...")
    
    try:
        system = LLMDebateSystem()
        
        # Use a simple question for testing
        question = "What are the main benefits of renewable energy?"
        print(f"Question: {question}")
        
        # Conduct debate with limited rounds for faster testing
        result = await system.conduct_debate(question, max_rounds=2)
        
        print(f"Status: {result.final_status}")
        print(f"Rounds: {result.total_rounds}")
        print(f"Duration: {result.total_duration:.2f}s" if result.total_duration else "Duration: N/A")
        
        if result.final_summary:
            print(f"Summary: {result.final_summary[:200]}...")
        
        if result.consensus_evolution:
            print(f"Consensus scores: {result.consensus_evolution}")
        
        # Check if we got responses from all debaters
        if result.rounds:
            first_round = result.rounds[0]
            debater_count = len(first_round.debater_responses)
            print(f"Debaters participated: {debater_count}")
            
            for response in first_round.debater_responses:
                print(f"  • {response.debater_name}: {len(response.response)} chars")
        
        print("✅ Simple debate completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Debate test failed: {e}")
        logger.exception("Debate test error:")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 LLM Debate System - Test Suite")
    print("=" * 50)
    
    test_results = []
    
    # Test 1: Ollama connection
    result1 = await test_ollama_connection()
    test_results.append(("Ollama Connection", result1))
    
    if not result1:
        print("\n❌ Cannot continue tests without Ollama connection")
        return False
    
    # Test 2: Model availability
    result2 = await test_model_availability()
    test_results.append(("Model Availability", result2))
    
    # Test 3: System initialization
    result3 = await test_system_initialization()
    test_results.append(("System Initialization", result3))
    
    if not result3:
        print("\n❌ Cannot continue tests without system initialization")
        return False
    
    # Test 4: Simple debate
    result4 = await test_simple_debate()
    test_results.append(("Simple Debate", result4))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready to use.")
        print("\nNext steps:")
        print("  1. Interactive CLI: python main.py")
        print("  2. Web interface: streamlit run streamlit_app.py")
        print("  3. REST API: python api.py")
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
    
    return passed == total

async def main():
    """Main test function"""
    try:
        success = await run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n🛑 Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        logger.exception("Test suite error:")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
