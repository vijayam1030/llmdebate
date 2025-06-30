#!/usr/bin/env python3
"""
Backend-only startup script for LLM Debate System
Use this when Angular CLI is not available
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from pinggy_tunnel import start_pinggy_tunnels, stop_pinggy_tunnels, get_pinggy_urls

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendLauncher:
    def __init__(self):
        self.backend_process = None
        self.tunnel_urls = {}
        self.is_running = False
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.cleanup_handler)
        signal.signal(signal.SIGTERM, self.cleanup_handler)
    
    def start_backend(self):
        """Start the FastAPI backend server"""
        logger.info("Starting backend server...")
        
        try:
            # Change to the project directory
            project_dir = Path(__file__).parent
            
            # Start backend with python.exe
            cmd = [
                "python.exe", "-m", "uvicorn", 
                "api.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8001"
            ]
            
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            logger.info("Backend server started on port 8001")
            
            # Monitor backend output in background
            def monitor_backend():
                for line in self.backend_process.stdout:
                    if "system initialized successfully" in line.lower():
                        logger.info(f"Backend: {line.strip()}")
            
            threading.Thread(target=monitor_backend, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            raise
    
    def wait_for_backend(self):
        """Wait for backend to be ready"""
        logger.info("Waiting for backend to start...")
        
        backend_ready = False
        for i in range(60):  # Wait up to 60 seconds
            try:
                import requests
                response = requests.get("http://localhost:8001/api/status", timeout=2)
                if response.status_code == 200:
                    backend_ready = True
                    logger.info("Backend is ready!")
                    break
            except:
                pass
            time.sleep(1)
        
        return backend_ready
    
    def start_tunnel(self):
        """Start Pinggy tunnel for backend only"""
        logger.info("Starting Pinggy tunnel for backend...")
        
        try:
            # Only start backend tunnel
            self.tunnel_urls = start_pinggy_tunnels(
                backend_port=8001,
                frontend_port=None  # Skip frontend tunnel
            )
            
            # Wait a bit for tunnel to establish
            time.sleep(5)
            
            # Get the actual URLs
            urls = get_pinggy_urls()
            
            logger.info("=" * 60)
            logger.info("🚀 LLM DEBATE BACKEND STARTED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"🔗 Backend API URL: {urls.get('backend', 'Not available')}")
            logger.info(f"🏠 Local Backend: http://localhost:8001")
            logger.info("=" * 60)
            logger.info("📱 To start frontend manually:")
            logger.info("   cd angular-ui")
            logger.info("   npm start")
            logger.info("=" * 60)
            logger.info("Press Ctrl+C to stop the backend")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
    
    def run(self):
        """Main run method"""
        try:
            logger.info("🚀 Starting LLM Debate Backend...")
            
            # Start backend
            self.start_backend()
            time.sleep(3)  # Give backend time to start
            
            # Wait for backend to be ready
            if not self.wait_for_backend():
                logger.warning("Backend may not be fully ready")
            
            # Start tunnel
            self.start_tunnel()
            
            self.is_running = True
            
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
                
                # Check if process is still running
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("Backend process died unexpectedly")
                    break
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all processes"""
        logger.info("Shutting down backend...")
        
        self.is_running = False
        
        # Stop tunnel
        try:
            stop_pinggy_tunnels()
        except Exception as e:
            logger.error(f"Error stopping tunnel: {e}")
        
        # Stop backend
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
        
        logger.info("Backend stopped")
    
    def cleanup_handler(self, signum, frame):
        """Signal handler for cleanup"""
        self.cleanup()
        sys.exit(0)

def main():
    """Main entry point"""
    launcher = BackendLauncher()
    launcher.run()

if __name__ == "__main__":
    main()