#!/usr/bin/env python3
"""
Test script to verify the FastAPI server can start without errors
"""

print("Testing FastAPI server import...")

try:
    from api.main import app
    print("✅ FastAPI app imported successfully!")
    print("✅ No @app.on_startup errors!")
    print("\nServer should now start without issues.")
    print("\nTo start the server, run:")
    print("python -m uvicorn api.main:app --host 0.0.0.0 --port 8000")
    
except Exception as e:
    print(f"❌ Error importing FastAPI app: {e}")
    print("Please check the api/main.py file for syntax errors.")
