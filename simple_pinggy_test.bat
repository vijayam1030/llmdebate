@echo off
echo Testing Pinggy tunnel to localhost:4201...
echo.
echo Watch for the public URL in the output:
echo.

ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:4201 a.pinggy.io

pause