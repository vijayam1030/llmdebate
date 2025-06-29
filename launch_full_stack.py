#!/usr/bin/env python3
"""
Cross-platform launcher for the LLM Debate System
Builds Angular frontend and starts FastAPI backend
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        print(f"Running: {command}")
        result = subprocess.run(command, shell=shell, cwd=cwd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔧 Checking prerequisites...")
    
    # Check Python
    try:
        python_version = subprocess.check_output([sys.executable, "--version"], text=True).strip()
        print(f"✅ {python_version}")
    except Exception:
        print("❌ Python not found!")
        return False
    
    # Check Node.js
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"✅ Node.js {node_version}")
    except Exception:
        print("❌ Node.js not found! Please install Node.js")
        return False
    
    # Check npm
    try:
        npm_version = subprocess.check_output(["npm", "--version"], text=True).strip()
        print(f"✅ npm {npm_version}")
    except Exception:
        print("❌ npm not found! Please install npm")
        return False
    
    return True

def setup_angular():
    """Setup and build Angular frontend"""
    print("\n📦 Setting up Angular frontend...")
    
    angular_dir = Path("angular-ui")
    if not angular_dir.exists():
        print("❌ Angular directory not found!")
        return False
    
    # Install dependencies if needed
    node_modules = angular_dir / "node_modules"
    if not node_modules.exists():
        print("Installing npm dependencies...")
        if not run_command("npm install", cwd=angular_dir):
            return False
    
    # Build Angular
    print("Building Angular application...")
    if not run_command("npm run build", cwd=angular_dir):
        return False
    
    print("✅ Angular build completed!")
    return True

def setup_python():
    """Setup Python environment"""
    print("\n🐍 Setting up Python backend...")
    
    # Check if virtual environment exists
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print("Creating Python virtual environment...")
        if not run_command(f"{sys.executable} -m venv .venv"):
            return False
    
    # Get the correct python executable for the venv
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
    
    # Install dependencies
    requirements_file = Path("system") / "requirements.txt"
    if requirements_file.exists():
        print("Installing Python dependencies...")
        if not run_command(f"{pip_exe} install -r {requirements_file}"):
            return False
    
    print("✅ Python setup completed!")
    return True

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting LLM Debate System...")
    print("\n🌐 Server will be available at:")
    print("   • Main UI: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/docs")
    print("   • Status: http://localhost:8000/api/status")
    print("\n⚡ Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Get the correct python executable for the venv
    venv_dir = Path(".venv")
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"
    
    # Start the server
    command = f"{python_exe} -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
    try:
        subprocess.run(command, shell=True, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")

def main():
    """Main launcher function"""
    print("=" * 50)
    print("   LLM Debate System - Full Stack Launcher")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met!")
        return 1
    
    # Setup Angular
    if not setup_angular():
        print("\n❌ Angular setup failed!")
        return 1
    
    # Setup Python
    if not setup_python():
        print("\n❌ Python setup failed!")
        return 1
    
    # Start server
    start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
