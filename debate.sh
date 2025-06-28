#!/bin/bash

# LLM Debate System - Unix Launcher

echo "🎯 LLM Debate System - Unix Launcher"
echo "====================================="

# Check if Python is available
if ! command -v python &> /dev/null; then
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python is not installed or not in PATH"
        echo "Please install Python from: https://python.org/"
        exit 1
    else
        PYTHON_CMD="python3"
    fi
else
    PYTHON_CMD="python"
fi

# Function to show help
show_help() {
    echo ""
    echo "LLM Debate System - Usage:"
    echo ""
    echo "  ./debate.sh                              # Interactive CLI mode"
    echo "  ./debate.sh \"Your question here\"         # Direct question mode"
    echo "  ./debate.sh --web                        # Launch web interface"
    echo "  ./debate.sh --api                        # Launch API server"
    echo "  ./debate.sh --skip-check                 # Skip model check"
    echo "  ./debate.sh --help                       # Show this help"
    echo ""
    echo "Examples:"
    echo "  ./debate.sh \"What are the benefits of AI?\""
    echo "  ./debate.sh --web"
    echo "  ./debate.sh --skip-check \"Climate change solutions\""
    echo ""
}

# Parse command line arguments
WEB_MODE=0
API_MODE=0
SKIP_CHECK=0
ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --web)
            WEB_MODE=1
            shift
            ;;
        --api)
            API_MODE=1
            shift
            ;;
        --skip-check)
            SKIP_CHECK=1
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Launch the appropriate mode
if [ $WEB_MODE -eq 1 ]; then
    echo "🌐 Launching Web Interface..."
    $PYTHON_CMD run.py --web
elif [ $API_MODE -eq 1 ]; then
    echo "🔌 Launching API Server..."
    $PYTHON_CMD run.py --api
else
    # CLI mode
    if [ $SKIP_CHECK -eq 1 ]; then
        $PYTHON_CMD run.py --skip-check "${ARGS[@]}"
    else
        $PYTHON_CMD run.py "${ARGS[@]}"
    fi
fi

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Application exited with errors"
    read -p "Press Enter to continue..."
fi
