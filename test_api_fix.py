#!/usr/bin/env python3
"""
Quick test to verify the API fix works
"""

import requests
import time
import json

print("🔍 Testing API with fixed attribute handling...")

def test_api():
    try:
        # Check if server is running
        try:
            response = requests.get("http://localhost:8000/api/status", timeout=5)
            if response.status_code != 200:
                print("❌ Server not running. Please start with: quick_start.bat")
                return
        except requests.exceptions.RequestException:
            print("❌ Server not running. Please start with: quick_start.bat")
            return
        
        print("✅ Server is running")
        
        # Start a simple debate
        debate_request = {
            "question": "Is water wet?",
            "max_rounds": 1  # Just one round to test quickly
        }
        
        print("   Starting simple debate...")
        response = requests.post("http://localhost:8000/api/debate/start", json=debate_request)
        if response.status_code != 200:
            print(f"❌ Failed to start debate: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        debate_response = response.json()
        debate_id = debate_response["debate_id"]
        print(f"✅ Debate started: {debate_id}")
        
        # Monitor debate briefly
        print("   Monitoring for 60 seconds...")
        start_time = time.time()
        while time.time() - start_time < 60:
            response = requests.get(f"http://localhost:8000/api/debate/{debate_id}/status")
            if response.status_code != 200:
                print(f"❌ Status check failed: {response.status_code}")
                break
            
            status = response.json()
            print(f"   Status: {status['status']} ({status['progress']*100:.1f}%)")
            
            if status["status"] == "completed":
                print("✅ Debate completed successfully!")
                result = status["result"]
                print(f"   Final status: {result['final_status']}")
                print(f"   Total rounds: {result['total_rounds']}")
                print(f"   Consensus: {result['consensus_reached']}")
                print(f"   Rounds processed: {len(result['rounds'])}")
                
                # Check if we can access round data
                if result['rounds']:
                    first_round = result['rounds'][0]
                    print(f"   First round responses: {len(first_round['responses'])}")
                    print(f"   First round consensus: {first_round['consensus_analysis']['average_similarity']:.2f}")
                
                return True
            
            elif status["status"] == "failed":
                print("❌ Debate failed!")
                if "error" in status:
                    print(f"   Error: {status['error']}")
                return False
            
            time.sleep(3)
        
        print("❌ Test timed out")
        return False
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n✅ API fix verification PASSED")
    else:
        print("\n❌ API fix verification FAILED")
