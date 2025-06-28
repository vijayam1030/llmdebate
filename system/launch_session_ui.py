#!/usr/bin/env python3
"""
Simple launcher for the session-based Streamlit UI
"""

import subprocess
import sys
import os

def main():
    """Launch the session-based Streamlit UI"""
    
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Launching LLM Debate System (Session-based UI)")
    print("📍 Using streamlit_app_session.py for true model persistence")
    print("⏱️  This may take a moment to start...")
    print()
    
    try:
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app_session.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
