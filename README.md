# 🧬 Boltz-2 Structure Prediction App

A Gradio web interface for **Boltz-2** protein structure prediction, designed for easy deployment on **Lightning AI**.

## ✨ Features

- **Protein Structure Prediction** — Predict 3D structures with AlphaFold3-level accuracy
- **Ligand Docking** — Include small molecules (SMILES) for protein-ligand complex prediction
- **Oligomer Support** — Model dimers, trimers, tetramers, and beyond
- **Cyclic Peptides** — Predict cyclic peptide structures
- **Interactive 3D Viewer** — Visualize structures colored by pLDDT confidence (AlphaFold-style)
- **Confidence Plots** — PAE heatmaps and per-residue pLDDT charts
- **Download Results** — Export structures in CIF format

## 🚀 Quick Start on Lightning AI

### Option 1: Lightning AI Studio (Recommended)

1. **Create a new Studio** on [Lightning AI](https://lightning.ai)
   - Select a **GPU machine** (A10G or better recommended)
   - Choose **Python 3.10+** environment

2. **Clone this repo** into the Studio:
   ```bash
   git clone https://github.com/roknabadi/boltz2-app.git
   cd boltz2-app
   ```

3. **Run the app**:
   ```bash
   bash run.sh
   ```

4. **Access the app** — Click "Open App" in Lightning AI or visit `http://localhost:7860`

### Option 2: Deploy as a Lightning App

Use the included `lightning.yaml` to deploy:

```bash
lightning run app lightning_app.py --cloud
```

## 📦 Local Installation

```bash
git clone https://github.com/roknabadi/boltz2-app.git
cd boltz2-app

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

The app will be available at `http://localhost:7860`.

## 🎯 Usage

### Protein Input

Enter your protein sequence in FASTA format or as a raw sequence:

```
>my_protein
MKWVTFISLLLLFSSAYSRGVFRRDAHKSEVAHRFKDLGEENFKALVLIAFAQYLQQCPFEDHVK
```

### Ligand Input (Optional)

Provide a SMILES string for protein-ligand complex prediction:

```
CC(=O)Oc1ccccc1C(=O)O
```

### Advanced Settings

| Setting | Default | Description |
|---------|---------|-------------|
| MSA Server | Always on | ColabFold MSA server (required for accuracy) |
| Sampling Steps | 50 | More steps = higher quality, slower runtime |
| Number of Copies | 1 | Set >1 for oligomers (dimer, trimer, etc.) |
| Cyclic | Off | Enable for cyclic peptide prediction |

## 📊 Output

- **Interactive 3D Structure** — Rotatable viewer with pLDDT coloring
- **Confidence Metrics** — pLDDT, pTM, and binding affinity scores
- **PAE Plot** — Predicted Aligned Error heatmap
- **pLDDT Plot** — Per-residue confidence chart
- **Downloadable CIF** — Structure file for further analysis

## ⚡ Performance

| Hardware | Typical Prediction Time |
|----------|------------------------|
| A10G GPU | 2–5 minutes |
| A100 GPU | 1–3 minutes |
| CPU only | 30–60 minutes |

Times vary with sequence length. Sequences >1000 residues automatically reduce recycling steps to stay within GPU memory.

## 📁 Project Structure

```
boltz2-app/
├── app.py              # Gradio UI and prediction orchestration
├── prediction.py       # Input validation, YAML generation, Boltz-2 runner
├── visualization.py    # 3Dmol.js viewer, PAE/pLDDT plots, confidence parsing
├── style.py            # Gradio theme and CSS
├── lightning.yaml      # Lightning AI deployment config
├── lightning_app.py    # Lightning AI app wrapper
├── requirements.txt    # Python dependencies
├── run.sh              # Launch script
├── LICENSE             # MIT License
└── README.md           # This file
```

## 🔧 Configuration

```bash
# Optional: custom cache directory for model weights (~6 GB)
export BOLTZ_CACHE=/path/to/cache

# Optional: select CUDA device
export CUDA_VISIBLE_DEVICES=0
```

## 🔬 About Boltz-2

[Boltz-2](https://github.com/jwohlwend/boltz) is an open-source protein structure prediction model from the MIT Jameel Clinic that approaches AlphaFold3-level accuracy. It supports protein, DNA, RNA, and small molecule complex prediction, plus binding affinity estimation. The model is released under the MIT license.

## 🤝 Acknowledgments

- **Boltz-2**: Jeremy Wohlwend, Gabriele Corso, Saro Passaro, and the MIT Jameel Clinic team
- **3Dmol.js**: Interactive molecular visualization
- **Gradio**: Web interface framework
- **Lightning AI**: Deployment platform

## 📄 License

This project is licensed under the [MIT License](LICENSE).
