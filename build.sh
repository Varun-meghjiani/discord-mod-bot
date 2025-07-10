#!/bin/bash
echo "Setting up Python 3.11 environment..."

# Force Python 3.11
export PYTHON_VERSION=3.11

# Install Python 3.11 if not available
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    apt-get update && apt-get install -y python3.11 python3.11-pip
fi

# Use Python 3.11
alias python=python3.11
alias pip=pip3.11

echo "Python version:"
python --version

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build complete!" 