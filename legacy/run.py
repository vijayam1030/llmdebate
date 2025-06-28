"""
Smart launcher for LLM Debate System
Automatically checks models before running the main application
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from check_models import ModelChecker

async def run_model_check() -> bool:
    """Run model availability check"""
    print("🔍 Performing pre-flight model check...\n")
    
    checker = ModelChecker()
    
    # Quick check first
    if not await checker.check_ollama_status():
        return False
    
    found_models, missing_models = await checker.check_model_availability()
    
    if not missing_models:
        print(f"✅ All {len(found_models)} required models are ready!")
        return True
    
    print(f"\n⚠️  Found {len(missing_models)} missing models")
    print("Would you like to:")
    print("1. Download missing models automatically")
    print("2. Continue anyway (may fail during execution)")
    print("3. Exit and download manually")
    
    while True:
        choice = input("\nEnter choice (1/2/3): ").strip()
        
        if choice == "1":
            # Auto-download missing models
            success = await checker.download_missing_models(missing_models, auto_download=True)
            return success
        elif choice == "2":
            # Continue anyway
            print("⚠️  Continuing without all models (may encounter errors)")
            return True
        elif choice == "3":
            # Exit
            print("Manual download commands:")
            for model in missing_models:
                print(f"  ollama pull {model}")
            return False
        else:
            print("Please enter 1, 2, or 3")

def launch_main_app(args):
    """Launch the main application with given arguments"""
    print("\n🚀 Launching LLM Debate System...\n")
    
    # Run the main application
    cmd = [sys.executable, "main.py"] + args
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Application exited with error code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")

def launch_web_interface():
    """Launch the Streamlit web interface"""
    print("\n🌐 Launching Web Interface...\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Web interface exited with error code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 Web interface interrupted by user")

def launch_api_server():
    """Launch the FastAPI server"""
    print("\n🔌 Launching API Server...\n")
    
    try:
        subprocess.run([sys.executable, "api.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ API server exited with error code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 API server interrupted by user")

async def main():
    """Main launcher function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Smart launcher for LLM Debate System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                                    # Interactive CLI with model check
  python run.py "Your question here"              # Direct question with model check
  python run.py --web                             # Launch web interface
  python run.py --api                             # Launch API server
  python run.py --skip-check "Your question"      # Skip model check
        """
    )
    
    parser.add_argument("question", nargs="*", help="Debate question for direct mode")
    parser.add_argument("--web", action="store_true", help="Launch Streamlit web interface")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI server")
    parser.add_argument("--skip-check", action="store_true", help="Skip model availability check")
    parser.add_argument("--check-only", action="store_true", help="Only check models, don't launch app")
    
    args = parser.parse_args()
    
    print("🎯 LLM Debate System - Smart Launcher")
    print("=" * 45)
    
    # Handle special modes
    if args.check_only:
        checker = ModelChecker()
        success = await checker.run_full_check()
        return 0 if success else 1
    
    # Skip model check if requested
    if not args.skip_check:
        model_check_passed = await run_model_check()
        if not model_check_passed:
            print("❌ Model check failed. Exiting.")
            return 1
    else:
        print("⏭️  Skipping model check as requested")
    
    try:
        # Launch appropriate interface
        if args.web:
            launch_web_interface()
        elif args.api:
            launch_api_server()
        else:
            # CLI mode - pass remaining args to main.py
            question_args = args.question if args.question else []
            launch_main_app(question_args)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
