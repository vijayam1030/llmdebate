#!/usr/bin/env python3
"""
Test the debate progress tracking
"""

import asyncio
import aiohttp
import json
import time

async def test_debate_progress():
    """Test starting a debate and monitoring progress"""
    
    base_url = "http://localhost:8000"
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # 1. Check system status
            print("🔍 Checking system status...")
            async with session.get(f"{base_url}/api/status") as response:
                if response.status == 200:
                    status_data = await response.json()
                    print(f"✅ System initialized: {status_data['initialized']}")
                    print(f"✅ Models loaded: {len(status_data['models_loaded'])}")
                else:
                    print("❌ System not ready")
                    return
            
            # 2. Start a debate
            print("\n🚀 Starting debate...")
            debate_request = {
                "question": "Is artificial intelligence beneficial for humanity?",
                "max_rounds": 3
            }
            
            async with session.post(f"{base_url}/api/debate/start", json=debate_request) as response:
                if response.status == 200:
                    start_data = await response.json()
                    debate_id = start_data["debate_id"]
                    print(f"✅ Debate started: {debate_id}")
                else:
                    print("❌ Failed to start debate")
                    return
            
            # 3. Monitor progress
            print("\n📊 Monitoring progress...")
            last_progress = 0
            
            while True:
                await asyncio.sleep(3)  # Check every 3 seconds
                
                async with session.get(f"{base_url}/api/debate/{debate_id}/status") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        
                        progress = status_data["progress"]
                        status = status_data["status"]
                        current_round = status_data.get("current_round", 0)
                        total_rounds = status_data.get("total_rounds", 3)
                        
                        if progress != last_progress:
                            print(f"📈 Progress: {progress:.1%} | Round: {current_round}/{total_rounds} | Status: {status}")
                            last_progress = progress
                        
                        if status in ["completed", "failed"]:
                            print(f"\n🏁 Debate finished with status: {status}")
                            if status == "completed":
                                result = status_data.get("result", {})
                                print(f"✅ Final status: {result.get('final_status', 'unknown')}")
                                print(f"✅ Consensus reached: {result.get('consensus_reached', False)}")
                                print(f"✅ Total rounds: {result.get('total_rounds', 0)}")
                            break
                    else:
                        print("❌ Failed to get debate status")
                        break
            
    except Exception as e:
        print(f"❌ Error testing debate progress: {e}")

if __name__ == "__main__":
    print("🧪 Testing Debate Progress Tracking")
    print("=" * 40)
    asyncio.run(test_debate_progress())
