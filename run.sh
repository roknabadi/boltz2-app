#!/bin/bash
# Boltz-2 Structure Prediction App — setup and launch
set -e

echo "══════════════════════════════════════════════════════════"
echo "  Boltz-2 Structure Prediction App"
echo "══════════════════════════════════════════════════════════"
echo ""

# Detect environment
if [ -n "$LIGHTNING_CLOUDSPACE_ID" ]; then
    echo "✓ Lightning AI Studio detected"
else
    echo "Running locally"
    # Create venv if not in a Studio or existing venv
    if [ -z "$VIRTUAL_ENV" ] && [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python -m venv venv
    fi
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Optional: CUDA kernel optimizations
pip install cuequivariance-ops-torch-cu12 -q 2>/dev/null || true

# GPU check
echo ""
if python -c "import torch; assert torch.cuda.is_available()" 2>/dev/null; then
    echo "✓ GPU available"
else
    echo "⚠ No GPU detected — predictions will be slow"
fi

# Launch
echo ""
echo "Starting app on http://localhost:7860"
echo "══════════════════════════════════════════════════════════"
echo ""
python app.py
