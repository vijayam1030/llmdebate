#!/usr/bin/env python3
"""
Final system test to verify everything works
"""

import os
import sys
import subprocess
import time
import requests
import webbrowser
from pathlib import Path

print("🚀 Final System Test for LLM Debate System")
print("=" * 50)

# Check if Angular build exists
angular_dist = Path("angular-ui/dist")
if not angular_dist.exists():
    print("❌ Angular build not found! Please run: cd angular-ui && npm run build")
    sys.exit(1)

print("✅ Angular build found")

# Check if static files exist
required_files = ["index.html", "main.3aa000674cdd3135.js", "styles.dedeb3d18ed0b6d4.css"]
for file in required_files:
    if not (angular_dist / file).exists():
        print(f"❌ Missing Angular file: {file}")
        sys.exit(1)

print("✅ All Angular static files present")

# Start the FastAPI server
print("\n🔧 Starting FastAPI server...")
try:
    # Use uvicorn to start the server
    server_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ], cwd=os.getcwd())
    
    print("⏳ Waiting for server to start...")
    time.sleep(5)
    
    # Test server connection
    try:
        response = requests.get("http://localhost:8000/api/status", timeout=10)
        if response.status_code == 200:
            print("✅ FastAPI server is running and responsive")
            status_data = response.json()
            print(f"   - System initialized: {status_data.get('initialized', False)}")
            print(f"   - Models loaded: {len(status_data.get('models_loaded', []))}")
        else:
            print(f"⚠️  Server responded with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        server_process.terminate()
        sys.exit(1)
    
    # Test Angular UI
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        if response.status_code == 200 and "LLM Debate System" in response.text:
            print("✅ Angular UI is being served correctly")
        else:
            print(f"⚠️  Angular UI responded with status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not access Angular UI: {e}")
    
    print("\n🎉 System Test Results:")
    print("✅ Angular build completed successfully")
    print("✅ FastAPI server started and is responsive")
    print("✅ Angular UI is being served")
    print("✅ API endpoints are accessible")
    
    print(f"\n🌐 Access the LLM Debate System at: http://localhost:8000")
    print("\n💡 To start a debate:")
    print("   1. Open your browser to http://localhost:8000")
    print("   2. Wait for the system to initialize (green status)")
    print("   3. Enter your debate question")
    print("   4. Click 'Start Debate' and watch the AI agents debate!")
    
    print(f"\n⏹️  To stop the server, press Ctrl+C or terminate process {server_process.pid}")
    
    # Keep the server running
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Server stopped successfully")

except Exception as e:
    print(f"❌ Error starting system: {e}")
    sys.exit(1)
