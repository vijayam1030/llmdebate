#!/usr/bin/env python3
"""
Development mode launcher - runs Angular dev server separately
"""

import subprocess
import sys
import os
import time
import threading

def start_fastapi_server():
    """Start FastAPI server for API only"""
    print("🚀 Starting FastAPI server on port 8000...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "api/main.py"])

def start_angular_dev():
    """Start Angular development server"""
    print("🅰️ Starting Angular dev server on port 4200...")
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "angular-ui"))
    subprocess.run(["ng", "serve", "--host", "0.0.0.0", "--port", "4200"])

if __name__ == "__main__":
    print("🔧 Starting development mode...")
    print("   FastAPI (API): http://localhost:8000/api")
    print("   Angular (UI): http://localhost:4200")
    print("   Note: You'll need to handle CORS for this setup")
    
    # Start both servers in parallel
    fastapi_thread = threading.Thread(target=start_fastapi_server)
    angular_thread = threading.Thread(target=start_angular_dev)
    
    fastapi_thread.start()
    time.sleep(2)  # Give FastAPI time to start
    angular_thread.start()
    
    # Wait for both threads
    fastapi_thread.join()
    angular_thread.join()
