# WSL2 Port Forwarding Setup Script
# Run as Administrator in PowerShell

# Get WSL IP address
$wslIP = wsl hostname -I | ForEach-Object { $_.Split(' ')[0] }
Write-Host "WSL IP: $wslIP"

# Remove existing port proxies
netsh interface portproxy delete v4tov4 listenport=4200 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=4201 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null

# Add port forwarding for your services
netsh interface portproxy add v4tov4 listenport=4201 listenaddress=0.0.0.0 connectport=4201 connectaddress=$wslIP
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIP

# Show current port proxies
Write-Host "Current port forwarding rules:"
netsh interface portproxy show v4tov4

Write-Host "Setup complete! You can now access:"
Write-Host "Angular: http://localhost:4201"
Write-Host "Backend: http://localhost:8000"