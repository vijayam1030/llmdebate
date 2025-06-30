#!/usr/bin/env python3
"""
Test script to verify Pinggy URL detection
"""

from pinggy_tunnel import get_tunnel

# Test the tunnel instance
tunnel = get_tunnel()

# Manually set URLs based on the detected ports from your logs
tunnel.backend_url = "https://4.a.pinggy.io"
tunnel.frontend_url = "https://5.a.pinggy.io"

print("Testing Pinggy URL detection:")
print(f"Backend URL: {tunnel.backend_url}")
print(f"Frontend URL: {tunnel.frontend_url}")

# Test the get_pinggy_urls function
from pinggy_tunnel import get_pinggy_urls
urls = get_pinggy_urls()
print(f"URLs from function: {urls}")