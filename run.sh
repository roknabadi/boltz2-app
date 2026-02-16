#!/bin/bash
# Lightning AI Studio Launch Script for Boltz-2 Structure Prediction App
# 
# This script sets up and launches the Gradio app in a Lightning AI Studio
#
# Usage: bash run.sh

set -e

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║         Boltz-2 Structure Prediction App                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Check if running in Lightning AI Studio
if [ -n "$LIGHTNING_CLOUDSPACE_ID" ]; then
    echo "✓ Running in Lightning AI Studio"
else
    echo "⚠ Not detected as Lightning AI Studio - running locally"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Ensure CUDA kernels are available (critical for Boltz-2)
echo "📦 Installing CUDA kernel optimizations..."
pip install cuequivariance-ops-torch-cu12 -q 2>/dev/null || echo "⚠ CUDA kernels not installed (will use fallback)"

# Check for GPU
echo ""
if python -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo "✓ GPU detected - predictions will be fast!"
else
    echo "⚠ No GPU detected - predictions will be slower"
fi

# Launch the app
echo ""
echo "🚀 Launching Boltz-2 Structure Prediction App..."
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " App will be available at: http://localhost:7860"
echo " In Lightning AI Studio, click 'Open App' to view"
echo "═══════════════════════════════════════════════════════════════"
echo ""

python app.py
