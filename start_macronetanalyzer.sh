#!/bin/bash

# Silent logging
mkdir -p ~/.netcache
echo "$(date) - Starting setup process..." >> ~/.netcache/netsetup.log

# Check for Python
if command -v python3 &> /dev/null; then
    echo "$(date) - Python found: $(python3 --version)" >> ~/.netcache/netsetup.log
elif command -v python &> /dev/null && python --version | grep -q "Python 3"; then
    echo "$(date) - Python found: $(python --version)" >> ~/.netcache/netsetup.log
else
    echo "$(date) - Python not found; installing..." >> ~/.netcache/netsetup.log
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt &> /dev/null; then
            sudo apt update -y >/dev/null 2>&1
            sudo apt install -y python3 python3-pip >/dev/null 2>&1
        elif command -v yum &> /dev/null; then
            sudo yum install -y python3 python3-pip >/dev/null 2>&1
        else
            echo "$(date) - Unsupported Linux package manager. Install Python 3 manually." >> ~/.netcache/netsetup.log
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install python@3.12 >/dev/null 2>&1
        else
            echo "$(date) - Homebrew not found. Install Python 3 manually from https://www.python.org/downloads/" >> ~/.netcache/netsetup.log
            exit 1
        fi
    else
        echo "$(date) - Unsupported platform: $OSTYPE. Install Python 3 manually." >> ~/.netcache/netsetup.log
        exit 1
    fi
    echo "$(date) - Python installed" >> ~/.netcache/netsetup.log
fi

# Run the Python setup script silently
echo "$(date) - Running setup_macronetanalyzer.py..." >> ~/.netcache/netsetup.log
python3 setup_macronetanalyzer.py >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "$(date) - Setup completed successfully" >> ~/.netcache/netsetup.log
else
    echo "$(date) - Setup failed" >> ~/.netcache/netsetup.log
    exit 1
fi