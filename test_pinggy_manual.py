#!/usr/bin/env python3
"""
Manual test to check Pinggy tunnel output and find correct URL format
"""

import subprocess
import re
import time

def test_pinggy_tunnel():
    print("Testing Pinggy tunnel to see actual output...")
    
    # Start a simple HTTP server on port 8080 for testing
    try:
        import http.server
        import socketserver
        import threading
        
        # Start simple server in background
        def start_server():
            with socketserver.TCPServer(("", 8080), http.server.SimpleHTTPRequestHandler) as httpd:
                print("Started test server on port 8080")
                httpd.serve_forever()
        
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        # Start Pinggy tunnel
        cmd = [
            "ssh", "-p", "443", 
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=NUL",
            "-R0:localhost:8080", 
            "a.pinggy.io"
        ]
        
        print("Starting Pinggy tunnel...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='ignore'
        )
        
        # Read output for 30 seconds
        start_time = time.time()
        while time.time() - start_time < 30:
            line = process.stdout.readline()
            if line:
                print(f"PINGGY OUTPUT: {line.strip()}")
                
                # Look for any URL patterns
                url_patterns = [
                    r'https?://[^\s]+\.a\.pinggy\.io[^\s]*',
                    r'https?://a\.pinggy\.io[^\s]*',
                    r'https?://[^\s]+pinggy[^\s]*',
                    r'tunnel.*https?://[^\s]+',
                    r'URL.*https?://[^\s]+'
                ]
                
                for pattern in url_patterns:
                    match = re.search(pattern, line)
                    if match:
                        print(f"🔗 FOUND URL: {match.group(0)}")
        
        process.terminate()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pinggy_manual()