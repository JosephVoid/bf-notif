#!/bin/bash

# Function to run commands and log output with date and time stamps
run_and_log() {
    # Check if output file exists, create if it doesn't
    if [ ! -e output.log ]; then
        touch output.log
    fi
    # Run command and append output with date and time stamps to output.log
    {
        echo "[$(date +'%Y-%m-%d %H:%M:%S')] Running command: $@"
        "$@"
    } >> output.log 2>&1
}

# Check if Python 3 and pip are installed
if ! command -v python3 &> /dev/null || ! command -v pip3 &> /dev/null; then
    echo "Python 3 and/or pip3 are not installed. Installing..."
    # Install Python 3 and pip3 (assuming a Linux environment with apt package manager)
    sudo apt update
    sudo apt install python3 python3-pip -y
fi

# Run pip install command
echo "Running pip install command..."
run_and_log pip3 install --no-cache-dir -r requirements.txt

# Run Python command in the background
echo "Running Python command in the background..."
run_and_log python3 -u app.py &

echo "Process started in the background. Check output.log for logs."
