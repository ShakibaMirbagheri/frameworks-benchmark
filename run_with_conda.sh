#!/bin/bash

# Run benchmarks with conda environment
# Usage: ./run_with_conda.sh [test_name]
# Example: ./run_with_conda.sh test_langchain.py
#          ./run_with_conda.sh   (runs all benchmarks)

CONDA_ENV="test"

echo "======================================"
echo "AI Framework Benchmark Runner"
echo "Using Conda Environment: $CONDA_ENV"
echo "======================================"
echo ""

# Find conda
if command -v conda &> /dev/null; then
    CONDA_CMD="conda"
elif [ -f "$HOME/anaconda3/bin/conda" ]; then
    CONDA_CMD="$HOME/anaconda3/bin/conda"
elif [ -f "$HOME/miniconda3/bin/conda" ]; then
    CONDA_CMD="$HOME/miniconda3/bin/conda"
else
    echo "❌ Error: conda not found"
    echo "Please activate your conda environment manually:"
    echo "  conda activate $CONDA_ENV"
    echo "  python run_benchmark.py"
    exit 1
fi

echo "✅ Found conda: $CONDA_CMD"
echo ""

# Check if specific test file provided
if [ -n "$1" ]; then
    echo "Running: $1"
    echo ""
    $CONDA_CMD run -n $CONDA_ENV python "$1"
else
    echo "Running all benchmarks..."
    echo ""
    $CONDA_CMD run -n $CONDA_ENV python run_benchmark.py
fi

