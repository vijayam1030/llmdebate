#!/usr/bin/env python3
"""
Simple test to verify LLM call works
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Testing simple LLM call...")

async def test_simple_llm():
    try:
        print("1. Importing modules...")
        from backend.ollama_integration import CustomOllamaLLM
        
        print("2. Creating LLM instance...")
        llm = CustomOllamaLLM(model="phi3:mini")
        
        print("3. Making test call...")
        response = await llm.ainvoke("Say 'Hello World' and nothing else.")
        
        print(f"✅ LLM Response: '{response}'")
        print(f"   Length: {len(response)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if asyncio.run(test_simple_llm()):
    print("\n✅ Simple LLM test passed!")
else:
    print("\n❌ Simple LLM test failed!")
