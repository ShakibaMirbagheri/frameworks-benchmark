#!/bin/bash

# Setup script for AI Framework Benchmark Suite

echo "=========================================="
echo "AI Framework Benchmark - Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "Virtual environment created successfully!"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config.yaml and add your OpenAI API key"
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo "3. Run the benchmark:"
echo "   python run_benchmark.py"
echo ""
echo "To run individual tests:"
echo "   python test_crewai.py"
echo "   python test_langgraph.py"
echo "   python test_dspy.py"
echo "   python test_langchain.py"
echo ""

