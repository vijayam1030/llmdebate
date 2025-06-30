"""
Pinggy tunnel integration for LLM Debate System
Handles tunneling for both frontend and backend services
"""

import subprocess
import threading
import time
import re
import logging
import signal
import sys
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

class PinggyTunnel:
    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_url: Optional[str] = None
        self.frontend_url: Optional[str] = None
        self.is_running = False
        
    def start_backend_tunnel(self, local_port: int = 8001) -> Optional[str]:
        """Start Pinggy tunnel for backend API"""
        try:
            # Start pinggy tunnel for backend with Windows-compatible settings
            cmd = [
                "ssh", "-p", "443", 
                "-o", "StrictHostKeyChecking=no",  # Skip host key verification
                "-o", "UserKnownHostsFile=NUL",    # Don't save host key on Windows
                "-R0:localhost:{}".format(local_port), 
                "a.pinggy.io"
            ]
            
            self.backend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
            
            # Parse output for the allocated port
            def parse_backend_url():
                for line in self.backend_process.stdout:
                    logger.info(f"Backend tunnel output: {line.strip()}")
                    # Look for the actual public URL in output
                    if "Your public URL:" in line or "Public URL:" in line:
                        url_match = re.search(r'https?://[^\s]+', line)
                        if url_match:
                            self.backend_url = url_match.group(0)
                            logger.info(f"Backend tunnel URL: {self.backend_url}")
                            return
                    # Look for allocated port as fallback
                    match = re.search(r'Allocated port (\d+) for remote forward', line)
                    if match:
                        port = match.group(1)
                        # Try different Pinggy URL formats
                        possible_urls = [
                            f"https://a.pinggy.io:{port}",
                            f"https://{port}-tcp.a.pinggy.io",
                            f"https://tcp-{port}.a.pinggy.io"
                        ]
                        # Use the first format as default
                        self.backend_url = possible_urls[0]
                        logger.info(f"Backend tunnel URL (constructed): {self.backend_url}")
                        return
                    # Also look for direct URL mentions
                    url_match = re.search(r'https?://[\w.-]+\.a\.pinggy\.io', line)
                    if url_match:
                        self.backend_url = url_match.group(0)
                        logger.info(f"Backend tunnel URL: {self.backend_url}")
                        return
            
            # Parse URL in background thread
            url_thread = threading.Thread(target=parse_backend_url, daemon=True)
            url_thread.start()
            
            # Wait for URL to be available
            for _ in range(30):  # Wait up to 30 seconds
                if self.backend_url:
                    return self.backend_url
                time.sleep(1)
                
            logger.warning("Backend tunnel URL not found within timeout")
            return None
            
        except Exception as e:
            logger.error(f"Failed to start backend tunnel: {e}")
            return None
    
    def start_frontend_tunnel(self, local_port: int = 4201) -> Optional[str]:
        """Start Pinggy tunnel for frontend"""
        try:
            # Start pinggy tunnel for frontend with Windows-compatible settings
            cmd = [
                "ssh", "-p", "443", 
                "-o", "StrictHostKeyChecking=no",  # Skip host key verification
                "-o", "UserKnownHostsFile=NUL",    # Don't save host key on Windows
                "-R0:localhost:{}".format(local_port), 
                "a.pinggy.io"
            ]
            
            self.frontend_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
            
            # Parse output for the allocated port
            def parse_frontend_url():
                for line in self.frontend_process.stdout:
                    logger.info(f"Frontend tunnel output: {line.strip()}")
                    # Look for the actual public URL in output
                    if "Your public URL:" in line or "Public URL:" in line:
                        url_match = re.search(r'https?://[^\s]+', line)
                        if url_match:
                            self.frontend_url = url_match.group(0)
                            logger.info(f"Frontend tunnel URL: {self.frontend_url}")
                            return
                    # Look for allocated port as fallback
                    match = re.search(r'Allocated port (\d+) for remote forward', line)
                    if match:
                        port = match.group(1)
                        # Try different Pinggy URL formats
                        possible_urls = [
                            f"https://a.pinggy.io:{port}",
                            f"https://{port}-tcp.a.pinggy.io",
                            f"https://tcp-{port}.a.pinggy.io"
                        ]
                        # Use the first format as default
                        self.frontend_url = possible_urls[0]
                        logger.info(f"Frontend tunnel URL (constructed): {self.frontend_url}")
                        return
                    # Also look for direct URL mentions
                    url_match = re.search(r'https?://[\w.-]+\.a\.pinggy\.io', line)
                    if url_match:
                        self.frontend_url = url_match.group(0)
                        logger.info(f"Frontend tunnel URL: {self.frontend_url}")
                        return
            
            # Parse URL in background thread
            url_thread = threading.Thread(target=parse_frontend_url, daemon=True)
            url_thread.start()
            
            # Wait for URL to be available
            for _ in range(30):  # Wait up to 30 seconds
                if self.frontend_url:
                    return self.frontend_url
                time.sleep(1)
                
            logger.warning("Frontend tunnel URL not found within timeout")
            return None
            
        except Exception as e:
            logger.error(f"Failed to start frontend tunnel: {e}")
            return None
    
    def start_tunnels(self, backend_port: int = 8001, frontend_port: int = 4201) -> Dict[str, Optional[str]]:
        """Start both tunnels and return URLs"""
        logger.info("Starting Pinggy tunnels...")
        
        # Start backend tunnel
        backend_url = self.start_backend_tunnel(backend_port)
        
        # Start frontend tunnel
        frontend_url = self.start_frontend_tunnel(frontend_port)
        
        self.is_running = True
        
        return {
            'backend': backend_url,
            'frontend': frontend_url
        }
    
    def get_urls(self) -> Dict[str, Optional[str]]:
        """Get current tunnel URLs"""
        return {
            'backend': self.backend_url,
            'frontend': self.frontend_url
        }
    
    def stop_tunnels(self):
        """Stop all tunnels"""
        logger.info("Stopping Pinggy tunnels...")
        
        if self.backend_process:
            try:
                self.backend_process.terminate()
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            except Exception as e:
                logger.error(f"Error stopping backend tunnel: {e}")
        
        if self.frontend_process:
            try:
                self.frontend_process.terminate()
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            except Exception as e:
                logger.error(f"Error stopping frontend tunnel: {e}")
        
        self.backend_process = None
        self.frontend_process = None
        self.backend_url = None
        self.frontend_url = None
        self.is_running = False
        
        logger.info("Pinggy tunnels stopped")

# Global tunnel instance
_tunnel_instance: Optional[PinggyTunnel] = None

def get_tunnel() -> PinggyTunnel:
    """Get or create tunnel instance"""
    global _tunnel_instance
    if _tunnel_instance is None:
        _tunnel_instance = PinggyTunnel()
    return _tunnel_instance

def start_pinggy_tunnels(backend_port: int = 8001, frontend_port: int = 4201) -> Dict[str, Optional[str]]:
    """Start Pinggy tunnels for both services"""
    tunnel = get_tunnel()
    return tunnel.start_tunnels(backend_port, frontend_port)

def get_pinggy_urls() -> Dict[str, Optional[str]]:
    """Get current Pinggy tunnel URLs"""
    tunnel = get_tunnel()
    return tunnel.get_urls()

def stop_pinggy_tunnels():
    """Stop all Pinggy tunnels"""
    tunnel = get_tunnel()
    tunnel.stop_tunnels()

# Cleanup on exit
def cleanup_handler(signum, frame):
    """Handle cleanup on exit"""
    stop_pinggy_tunnels()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)