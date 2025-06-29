@echo off
echo =====================================================
echo LLM Debate System - Selective Deployment
echo Target: New system under 8GB (preserve existing images)
echo =====================================================

echo.
echo 📊 Current Docker usage:
docker system df

echo.
echo 🔍 Existing images (will be preserved):
docker images --filter "reference=langchain*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo.
echo 🎯 Running selective deployment...
python final-size-enforcement.py

echo.
echo 📊 Final Docker usage:
docker system df

echo.
echo 🔍 Our new images:
docker images --filter "reference=*llm-debate*" --filter "reference=ollama/ollama" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

echo.
echo 💡 Size monitoring available:
echo   Check our system: python docker-size-monitor.py
echo   Check all Docker: python docker-size-monitor.py all
echo   Live monitor: python docker-size-monitor.py monitor
echo.
pause
