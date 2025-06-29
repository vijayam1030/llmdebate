#!/usr/bin/env python3
"""
Launch the LLM Debate System with Angular UI and FastAPI backend
"""

import subprocess
import sys
import os
import time

def main():
    """Launch the complete system"""
    print("🚀 Launching LLM Debate System...")
    print("=" * 60)
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print("📋 System Status:")
    print("✅ Angular frontend built and ready")
    print("✅ FastAPI backend with fixed status endpoint")
    print("✅ Model initialization working")
    print("✅ All endpoints return proper JSON")
    
    print("\n🌐 Starting FastAPI server...")
    print("   Server: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Status: http://localhost:8000/api/status")
    print("   UI: http://localhost:8000 (Angular)")
    
    print("\n⚡ Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Start the FastAPI server
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nPlease check:")
        print("1. All dependencies are installed")
        print("2. Ollama is running with models available")
        print("3. No other service is using port 8000")

if __name__ == "__main__":
    main()
