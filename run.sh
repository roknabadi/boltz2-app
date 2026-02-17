#!/bin/bash
# Boltz-2 Structure Prediction App — setup and launch

echo "══════════════════════════════════════════════════════════"
echo "  Boltz-2 Structure Prediction App"
echo "══════════════════════════════════════════════════════════"
echo ""

# Detect environment
if [ -d "/teamspace" ] || [ -n "$LIGHTNING_CLOUDSPACE_ID" ] || [ -n "$LIGHTNING_CLUSTER_ID" ]; then
    echo "✓ Lightning AI Studio detected"
else
    echo "Running locally"
    if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ] && [ ! -d "venv" ]; then
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
pip install -r requirements.txt -q || echo "⚠ Some dependencies failed — check errors above"

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
echo "Starting app on port 7860"
echo "Open Port Viewer → + New Port → 7860"
echo "══════════════════════════════════════════════════════════"
echo ""
exec python app.py