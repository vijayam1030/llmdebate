#!/usr/bin/env python3
"""
Unified startup script for LLM Debate System
Starts both frontend and backend with Pinggy tunnels
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

from cloudflared_tunnel import start_cloudflared_tunnel, get_cloudflared_url, stop_cloudflared_tunnel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AppLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
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
                "--host", "127.0.0.1", 
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
                    logger.info(f"Backend: {line.strip()}")
            
            threading.Thread(target=monitor_backend, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            raise
    
    def start_frontend(self):
        """Start the Angular frontend server"""
        logger.info("Starting frontend server...")
        
        try:
            project_dir = Path(__file__).parent / "angular-ui"
            
            # Check if ng command is available
            ng_commands = ["ng", "ng.cmd", "npx ng"]
            ng_cmd = None
            
            for cmd in ng_commands:
                try:
                    result = subprocess.run([cmd, "--version"], 
                                          capture_output=True, 
                                          text=True, 
                                          timeout=5)
                    if result.returncode == 0:
                        ng_cmd = cmd
                        logger.info(f"Found Angular CLI: {cmd}")
                        break
                except:
                    continue
            
            if not ng_cmd:
                logger.error("Angular CLI not found! Please install it with: npm install -g @angular/cli")
                raise Exception("Angular CLI not found")
            
            # Start Angular with ng serve and disable host check for tunnels
            cmd = [
                ng_cmd, "serve", 
                "--host", "0.0.0.0", 
                "--port", "4201",
                "--disable-host-check",  # Allow external hosts (tunnels)
                "--public-host", "localhost"  # Set public host
            ]
            
            self.frontend_process = subprocess.Popen(
                cmd,
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            logger.info("Frontend server started on port 4201")
            
            # Monitor frontend output in background
            def monitor_frontend():
                for line in self.frontend_process.stdout:
                    if "compiled successfully" in line.lower() or "build at:" in line.lower():
                        logger.info(f"Frontend: {line.strip()}")
            
            threading.Thread(target=monitor_frontend, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            if "Angular CLI not found" in str(e):
                logger.error("Please run: npm install -g @angular/cli")
                logger.error("Or use npm commands directly in the angular-ui folder")
            raise
    
    def wait_for_services(self):
        """Wait for both services to be ready"""
        logger.info("Waiting for services to start...")
        
        # Wait for backend
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
        
        if not backend_ready:
            logger.warning("Backend may not be fully ready yet")
        
        # Wait for frontend
        frontend_ready = False
        for i in range(60):  # Wait up to 60 seconds
            try:
                import requests
                response = requests.get("http://localhost:4201", timeout=2)
                if response.status_code == 200:
                    frontend_ready = True
                    logger.info("Frontend is ready!")
                    break
            except:
                pass
            time.sleep(1)
        
        if not frontend_ready:
            logger.warning("Frontend may not be fully ready yet")
        
        return backend_ready, frontend_ready
    
    def start_tunnels(self):
        """Start Cloudflare tunnels for both services"""
        logger.info("Starting Cloudflare tunnels...")
        
        try:
            from cloudflared_tunnel import start_cloudflare_tunnels, get_cloudflare_urls
            
            self.tunnel_urls = start_cloudflare_tunnels(
                backend_port=8001,
                frontend_port=4201
            )
            
            # Wait a bit for tunnels to establish
            time.sleep(5)
            
            # Get the actual URLs
            urls = get_cloudflare_urls()
            
            # Also update the backend API's knowledge of Cloudflare URLs
            try:
                import requests
                # Send the URLs to the backend so it can return them in status
                requests.post(
                    "http://localhost:8001/api/internal/set-cloudflare-urls", 
                    json=urls,
                    timeout=5
                )
            except Exception as e:
                logger.warning(f"Could not update backend with Cloudflare URLs: {e}")
            
            logger.info("=" * 60)
            logger.info("🚀 LLM DEBATE SYSTEM STARTED SUCCESSFULLY!")
            logger.info("=" * 60)
            logger.info(f"📱 Frontend URL: {urls.get('frontend', 'Not available')}")
            logger.info(f"🔗 Backend API URL: {urls.get('backend', 'Not available')}")
            logger.info(f"🏠 Local Frontend: http://localhost:4201")
            logger.info(f"🏠 Local Backend: http://localhost:8001")
            logger.info("=" * 60)
            logger.info("Press Ctrl+C to stop all services")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Failed to start tunnels: {e}")
    
    def run(self):
        """Main run method"""
        try:
            logger.info("🚀 Starting LLM Debate System...")
            
            # Kill any existing ngrok processes
            try:
                subprocess.run(["taskkill", "/f", "/im", "ngrok.exe"], 
                             capture_output=True, check=False)
                logger.info("Stopped any existing ngrok processes")
            except:
                pass
            
            # Start backend
            self.start_backend()
            time.sleep(3)  # Give backend time to start
            
            # Start frontend
            self.start_frontend()
            time.sleep(5)  # Give frontend time to start
            
            # Wait for services to be ready
            self.wait_for_services()
            
            # Start tunnels
            self.start_tunnels()
            
            self.is_running = True
            
            # Keep the main thread alive
            while self.is_running:
                time.sleep(1)
                
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    logger.error("Backend process died unexpectedly")
                    break
                    
                if self.frontend_process and self.frontend_process.poll() is not None:
                    logger.error("Frontend process died unexpectedly")
                    break
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all processes"""
        logger.info("Shutting down services...")
        
        self.is_running = False
        
        # Stop tunnels
        try:
            stop_cloudflared_tunnel()
        except Exception as e:
            logger.error(f"Error stopping tunnels: {e}")
        
        # Stop backend
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            except Exception as e:
                logger.error(f"Error stopping backend: {e}")
        
        # Stop frontend
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            except Exception as e:
                logger.error(f"Error stopping frontend: {e}")
        
        logger.info("All services stopped")
    
    def cleanup_handler(self, signum, frame):
        """Signal handler for cleanup"""
        self.cleanup()
        sys.exit(0)

def main():
    """Main entry point"""
    launcher = AppLauncher()
    launcher.run()

if __name__ == "__main__":
    main()