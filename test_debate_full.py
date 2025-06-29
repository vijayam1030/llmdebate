#!/usr/bin/env python3
"""
Test a full debate to see where it fails
"""

import sys
import os
import asyncio
import requests
import time
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔍 Testing full debate flow...")

async def test_debate():
    try:
        # First test if the API is running
        print("1. Testing API availability...")
        try:
            response = requests.get("http://localhost:8000/api/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"✅ API is running")
                print(f"   System initialized: {status['initialized']}")
                print(f"   Models loaded: {status['models_loaded']}")
            else:
                print(f"❌ API returned {response.status_code}")
                return
        except requests.exceptions.RequestException as e:
            print(f"❌ API not available: {e}")
            print("   Make sure to run: quick_start.bat or start_full_system.bat")
            return
        
        # Start a debate
        print("\n2. Starting a test debate...")
        debate_request = {
            "question": "Should AI be regulated by governments?",
            "max_rounds": 2
        }
        
        response = requests.post("http://localhost:8000/api/debate/start", json=debate_request)
        if response.status_code != 200:
            print(f"❌ Failed to start debate: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        debate_response = response.json()
        debate_id = debate_response["debate_id"]
        print(f"✅ Debate started with ID: {debate_id}")
        
        # Monitor the debate
        print("\n3. Monitoring debate progress...")
        max_wait = 300  # 5 minutes max
        start_time = time.time()
        last_status = ""
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(f"http://localhost:8000/api/debate/{debate_id}/status")
                if response.status_code != 200:
                    print(f"❌ Status check failed: {response.status_code}")
                    print(f"   Response: {response.text}")
                    break
                
                status = response.json()
                current_status = status["status"]
                progress = status["progress"]
                
                if current_status != last_status:
                    print(f"   Status: {current_status} ({progress*100:.1f}%)")
                    if status.get("current_round"):
                        print(f"   Round: {status['current_round']}/{status.get('total_rounds', '?')}")
                    last_status = current_status
                
                if current_status == "completed":
                    print("✅ Debate completed successfully!")
                    result = status["result"]
                    print(f"   Final status: {result['final_status']}")
                    print(f"   Consensus reached: {result['consensus_reached']}")
                    print(f"   Total rounds: {result['total_rounds']}")
                    if result.get('final_summary'):
                        print(f"   Summary preview: {result['final_summary'][:100]}...")
                    return
                
                elif current_status == "failed":
                    print("❌ Debate failed!")
                    if "error" in status:
                        print(f"   Error: {status['error']}")
                    return
                
                elif current_status == "running":
                    # Continue monitoring
                    pass
                else:
                    print(f"   Unknown status: {current_status}")
                
                time.sleep(3)  # Check every 3 seconds
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error checking status: {e}")
                break
        
        print(f"❌ Debate timed out after {max_wait} seconds")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_debate())

print("\n" + "="*50)
print("Test completed. Check the output above for results.")
print("="*50)
