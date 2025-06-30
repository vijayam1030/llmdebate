import subprocess
import re
import threading
import time
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class CloudflareTunnel:
    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_url: Optional[str] = None
        self.frontend_url: Optional[str] = None
        self.is_running = False
        
    def start_backend_tunnel(self, local_port: int = 8001) -> Optional[str]:
        """Start Cloudflare tunnel for backend API"""
        try:
            local_url = f"http://localhost:{local_port}"
            logger.info(f"Starting Cloudflare tunnel for backend: {local_url}")
            
            self.backend_process = subprocess.Popen(
                ["./cloudflared", "tunnel", "--url", local_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Parse output for the public URL
            def parse_backend_url():
                for line in self.backend_process.stdout:
                    logger.info(f"Backend tunnel output: {line.strip()}")
                    match = re.search(r"https://[\w-]+\.trycloudflare\.com", line)
                    if match:
                        self.backend_url = match.group(0)
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
        """Start Cloudflare tunnel for frontend"""
        try:
            local_url = f"http://localhost:{local_port}"
            logger.info(f"Starting Cloudflare tunnel for frontend: {local_url}")
            
            self.frontend_process = subprocess.Popen(
                ["./cloudflared", "tunnel", "--url", local_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Parse output for the public URL
            def parse_frontend_url():
                for line in self.frontend_process.stdout:
                    logger.info(f"Frontend tunnel output: {line.strip()}")
                    match = re.search(r"https://[\w-]+\.trycloudflare\.com", line)
                    if match:
                        self.frontend_url = match.group(0)
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
        logger.info("Starting Cloudflare tunnels...")
        
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
        logger.info("Stopping Cloudflare tunnels...")
        
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
        
        logger.info("Cloudflare tunnels stopped")

# Global tunnel instance
_tunnel_instance: Optional[CloudflareTunnel] = None

def get_tunnel() -> CloudflareTunnel:
    """Get or create tunnel instance"""
    global _tunnel_instance
    if _tunnel_instance is None:
        _tunnel_instance = CloudflareTunnel()
    return _tunnel_instance

def start_cloudflared_tunnel(local_url="http://localhost:8000"):
    """Legacy function for compatibility"""
    tunnel = get_tunnel()
    if "8001" in local_url:
        return tunnel.start_backend_tunnel(8001)
    elif "4201" in local_url:
        return tunnel.start_frontend_tunnel(4201)
    else:
        # Default to backend
        return tunnel.start_backend_tunnel(8000)

def start_cloudflare_tunnels(backend_port: int = 8001, frontend_port: int = 4201) -> Dict[str, Optional[str]]:
    """Start Cloudflare tunnels for both services"""
    tunnel = get_tunnel()
    return tunnel.start_tunnels(backend_port, frontend_port)

def get_cloudflared_url():
    """Legacy function for compatibility"""
    tunnel = get_tunnel()
    urls = tunnel.get_urls()
    return urls.get('backend') or urls.get('frontend')

def get_cloudflare_urls() -> Dict[str, Optional[str]]:
    """Get current Cloudflare tunnel URLs"""
    tunnel = get_tunnel()
    return tunnel.get_urls()

def stop_cloudflared_tunnel():
    """Stop all Cloudflare tunnels"""
    tunnel = get_tunnel()
    tunnel.stop_tunnels()
