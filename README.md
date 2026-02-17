# 🧬 Boltz-2 Structure Prediction App

A Gradio web app for [Boltz-2](https://github.com/jwohlwend/boltz) protein structure prediction, designed for deployment on [Lightning AI Studios](https://lightning.ai).

## ✨ Features

- **Protein structure prediction** — AlphaFold3-level accuracy via Boltz-2
- **Ligand docking** — SMILES input for protein–ligand complex prediction
- **Oligomer support** — dimers, trimers, tetramers, and beyond
- **Cyclic peptides** — toggle for N→C-connected structures
- **Interactive 3D viewer** — pLDDT-colored structures via 3Dmol.js
- **Confidence plots** — PAE heatmaps and per-residue pLDDT charts
- **CIF download** — export structures for further analysis

## 🚀 Deploy on Lightning AI

1. Create a new [Studio](https://lightning.ai) with a **GPU** (L4 or above)
2. Clone the repo in the Studio terminal:
   ```bash
   git clone https://github.com/roknabadi/boltz2-app.git
   cd boltz2-app
   ```
3. Launch:
   ```bash
   bash run.sh
   ```
4. Open the app via the Studio's **"Open App"** button or port `7860`

The first run downloads ~6 GB of model weights. These persist in the Studio, so subsequent runs start immediately. You can share a public URL directly from the Studio UI.

## 💻 Run Locally

Requires a CUDA GPU and Python 3.10+.

```bash
git clone https://github.com/roknabadi/boltz2-app.git
cd boltz2-app
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:7860`.

## 🎯 Usage

**Protein input:** paste a FASTA sequence or raw amino acid string.

**Ligand (optional):** enter a SMILES string to predict a protein–ligand complex.

**Advanced settings:**

| Setting | Default | Notes |
|---|---|---|
| MSA Server | Always on | ColabFold server, required for accuracy |
| Sampling Steps | 50 | Higher → better quality, slower |
| Copies | 1 | >1 for oligomers (dimer, trimer, …) |
| Cyclic | Off | For cyclic peptide prediction |

## ⚡ Performance

| GPU | Typical time |
|---|---|
| L4 | 3–8 min |
| L40S | 1–4 min |
| A100 | 1–3 min |

Sequences >1000 residues automatically reduce recycling steps to stay within GPU memory.

## 📁 Project Structure

```
boltz2-app/
├── app.py              # Gradio UI and prediction orchestration
├── prediction.py       # Input validation, YAML generation, Boltz-2 runner
├── visualization.py    # 3Dmol.js viewer, PAE/pLDDT plots, confidence parsing
├── style.py            # Gradio theme and CSS
├── requirements.txt    # Python dependencies
├── run.sh              # Setup and launch script
├── LICENSE             # MIT License
└── README.md
```

## 🔧 Environment Variables

```bash
export BOLTZ_CACHE=/path/to/cache    # Custom model weight location (~6 GB)
export CUDA_VISIBLE_DEVICES=0        # Select GPU
```

## 🔬 About Boltz-2

[Boltz-2](https://github.com/jwohlwend/boltz) is an open-source structure prediction model from the MIT Jameel Clinic. It supports protein, DNA, RNA, and small molecule complexes, plus binding affinity estimation. MIT licensed.

## 🤝 Acknowledgments

- **Boltz-2**: Jeremy Wohlwend, Gabriele Corso, Saro Passaro, and the MIT Jameel Clinic team
- **3Dmol.js**: Molecular visualization
- **Gradio**: Web interface
- **Lightning AI**: GPU cloud platform

## 📄 License

[MIT](LICENSE)