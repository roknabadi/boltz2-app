"""
Boltz-2 Structure Prediction App
Gradio interface for protein structure prediction — deploy on Lightning AI.
"""

import os
import shutil
import tempfile
from datetime import datetime

import gradio as gr
import numpy as np

from style import CSS, THEME
from prediction import (
    parse_fasta,
    validate_protein,
    validate_smiles,
    create_boltz_yaml,
    run_prediction,
    oligomer_name,
)
from visualization import (
    viewer_html,
    plot_pae,
    plot_plddt,
    find_confidence_files,
    load_plddt,
    load_pae,
)

# ---------------------------------------------------------------------------
# Example data
# ---------------------------------------------------------------------------

EXAMPLE_PROTEIN = """>insulin_human
MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAED
LQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN"""

EXAMPLE_LIGAND = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin


# ---------------------------------------------------------------------------
# Main prediction generator (yields partial UI updates)
# ---------------------------------------------------------------------------


def _error(msg: str, logs: str = ""):
    """Yield tuple for an error state."""
    return (None, f"❌ **Error:** {msg}", "", None, None, None, logs or msg)


def predict_structure(
    protein_text, ligand_smiles, _use_msa, sampling_steps, num_copies, cyclic
):
    """
    Generator that yields ``(viewer, status, metrics, file, pae_img,
    plddt_img, logs)`` tuples as prediction progresses.
    """
    logs: list[str] = []

    def log(msg):
        logs.append(f"[{datetime.now():%H:%M:%S}] {msg}")
        print(msg)

    def state(status="⏳ Running..."):
        return (None, status, "", None, None, None, "\n".join(logs))

    # -- validate protein --------------------------------------------------
    if not protein_text or not protein_text.strip():
        yield _error("Please provide a protein sequence.")
        return

    log("Parsing protein sequence…")
    yield state("⏳ Validating input…")

    header, sequence = parse_fasta(protein_text)
    ok, result = validate_protein(sequence)
    if not ok:
        yield _error(result)
        return
    sequence = result
    log(f"Sequence OK: {len(sequence)} residues")

    # -- validate ligand ---------------------------------------------------
    if ligand_smiles and ligand_smiles.strip():
        ok, result = validate_smiles(ligand_smiles)
        if not ok:
            yield _error(result)
            return
        ligand_smiles = result
        log(f"Ligand: {ligand_smiles[:50]}…")
    else:
        ligand_smiles = None
        log("No ligand — protein-only prediction")

    # -- set up job --------------------------------------------------------
    num_copies = int(num_copies or 1)
    job_dir = tempfile.mkdtemp(prefix="boltz_")
    log(f"Job dir: {job_dir}")

    try:
        yaml_path = create_boltz_yaml(
            sequence,
            job_dir,
            ligand_smiles=ligand_smiles,
            protein_name=header or "protein",
            cyclic=cyclic,
            num_copies=num_copies,
        )
        with open(yaml_path) as fh:
            for line in fh:
                log(f"  {line.rstrip()}")

        oname = oligomer_name(num_copies)
        oligo = f" × {num_copies} ({oname})" if num_copies > 1 else ""
        cyc = " (cyclic)" if cyclic else ""
        log(
            f"Starting Boltz-2: {len(sequence)} aa{oligo}{cyc}, "
            f"{sampling_steps} steps, MSA enabled"
        )
        yield state(
            f"⏳ **Running Boltz-2…**\n\nSequence: {len(sequence)} aa"
            f"{oligo}{cyc}\n\nThis may take several minutes."
        )

        # -- run Boltz-2 ---------------------------------------------------
        success, result, metrics, raw_log = run_prediction(
            yaml_path,
            job_dir,
            sampling_steps=sampling_steps,
            seq_len=len(sequence),
        )

        # Append trimmed Boltz output to our logs
        if raw_log:
            logs.append("\n--- Boltz-2 Output ---")
            for line in raw_log.split("\n")[-50:]:
                if line.strip() and not any(
                    x in line for x in ["%|", "it/s]", "━"]
                ):
                    logs.append(line)

        if not success:
            logs.append(f"FAILED: {result}")
            yield (
                None,
                f"❌ **Prediction failed:** {result}",
                "",
                None,
                None,
                None,
                "\n".join(logs),
            )
            return

        log("✅ Prediction complete — processing results…")
        yield state("⏳ Processing results…")

        # -- read structure ------------------------------------------------
        structure_text = open(result).read()
        fmt = "cif" if result.endswith(".cif") else "pdb"

        # -- confidence plots ----------------------------------------------
        conf = find_confidence_files(os.path.dirname(result))
        if not conf["pae"] and not conf["plddt"]:
            conf = find_confidence_files(job_dir)

        # Debug: log what we found and list the actual output directory
        log(
            f"Confidence files: pae={conf['pae']}, plddt={conf['plddt']}, json={conf['confidence_json']}"
        )
        struct_dir = os.path.dirname(result)
        try:
            import glob as _g

            all_files = _g.glob(os.path.join(struct_dir, "*"))
            log(
                f"Files in {struct_dir}: {[os.path.basename(f) for f in all_files]}"
            )
        except Exception:
            pass

        pae_img = plddt_img = None
        plddt_scores = None

        if conf["pae"] or conf["confidence_json"]:
            pae_matrix = load_pae(
                npz_path=conf["pae"],
                json_path=conf["confidence_json"],
            )
            if pae_matrix is not None:
                pae_img = plot_pae(pae_matrix, os.path.join(job_dir, "pae.png"))
                log(f"Created PAE plot: shape={pae_matrix.shape}")

        plddt_scores = load_plddt(
            npz_path=conf["plddt"],
            json_path=conf["confidence_json"],
            cif_path=result if fmt == "cif" else None,
        )
        if plddt_scores is not None:
            plddt_img = plot_plddt(
                plddt_scores, os.path.join(job_dir, "plddt.png")
            )
            log(
                f"pLDDT: min={plddt_scores.min():.1f} max={plddt_scores.max():.1f} "
                f"mean={plddt_scores.mean():.1f}"
            )

        # -- 3D viewer -----------------------------------------------------
        log("Building 3D viewer…")
        yield state("⏳ Creating 3D visualisation…")
        html = viewer_html(structure_text, fmt)

        # -- metrics markdown ----------------------------------------------
        md = "### 📊 Prediction Metrics\n\n"
        fmt_map = {
            "plddt": "pLDDT Score",
            "ptm": "pTM Score",
            "confidence": "Confidence",
            "affinity": "Predicted Affinity (log IC50)",
            "binding_probability": "Binding Probability",
        }
        for key, label in fmt_map.items():
            if key in metrics:
                v = metrics[key]
                if isinstance(v, list):
                    v = sum(v) / len(v)
                if key == "binding_probability":
                    md += f"**{label}:** {v:.2%}\n\n"
                else:
                    md += f"**{label}:** {v:.2f}\n\n"
        if plddt_scores is not None and "plddt" not in metrics:
            md += f"**Mean pLDDT:** {np.mean(plddt_scores):.1f}\n\n"
        if not metrics and plddt_scores is None:
            md += "*Detailed metrics not available*\n"

        # -- status --------------------------------------------------------
        status = f"✅ **Prediction completed!**\n\n"
        status += f"📏 **Length:** {len(sequence)} aa\n\n"
        if num_copies > 1:
            status += f"🔢 **Oligomer:** {oname} ({num_copies} chains)\n\n"
        if ligand_smiles:
            status += "💊 **Ligand:** included\n\n"
        status += f"📁 **Format:** {fmt.upper()}\n"

        # -- copy structure for download -----------------------------------
        out_file = os.path.join(job_dir, f"structure.{fmt}")
        shutil.copy(result, out_file)
        log("✅ Done!")

        yield (html, status, md, out_file, pae_img, plddt_img, "\n".join(logs))

    except Exception as exc:
        logs.append(f"Exception: {exc}")
        yield _error(str(exc), "\n".join(logs))


# ---------------------------------------------------------------------------
# Gradio layout
# ---------------------------------------------------------------------------


def create_app() -> gr.Blocks:
    with gr.Blocks(
        css=CSS, title="Boltz-2 Structure Prediction", theme=THEME
    ) as app:

        # -- header --------------------------------------------------------
        with gr.Row(elem_classes="header-container"):
            gr.HTML(
                '<h1 style="margin:0;font-size:28px;font-weight:700;'
                "background:linear-gradient(90deg,#b54ce5 0%,#8081e9 50%,#5bc5dc 100%);"
                '-webkit-background-clip:text;-webkit-text-fill-color:transparent">'
                "Boltz-2 Structure Prediction</h1>"
                '<p style="color:#555;margin:4px 0 0;font-size:14px">'
                "Predict 3D protein structures using Boltz-2</p>"
            )

        with gr.Row():
            # ── left: inputs ─────────────────────────────────────────────
            with gr.Column(scale=1):
                gr.Markdown("## 📥 Input")

                with gr.Tabs():
                    with gr.Tab("🧬 Protein Sequence"):
                        protein_input = gr.Textbox(
                            placeholder=(
                                "Paste FASTA or raw amino acid sequence…\n\n"
                                "Example:\n>my_protein\nMKTAYIAKQRQISFVK…"
                            ),
                            lines=12,
                            max_lines=20,
                            show_label=False,
                        )
                        gr.Markdown(
                            "> **Supported formats:** FASTA (header starting with >) "
                            "or raw amino acid sequence (single-letter codes)"
                        )

                    with gr.Tab("💊 Ligand (Optional)"):
                        ligand_input = gr.Textbox(
                            placeholder="SMILES string, e.g. CC(=O)Oc1ccccc1C(=O)O (Aspirin)",
                            lines=3,
                            show_label=False,
                        )
                        gr.Markdown(
                            "> Leave empty for protein-only prediction. "
                            "Include a ligand to predict binding pose and affinity."
                        )

                with gr.Accordion("⚙️ Advanced Settings", open=True):
                    gr.Markdown(
                        "**MSA Server:** always enabled (required for accuracy)"
                    )
                    num_copies = gr.Slider(
                        1,
                        8,
                        value=1,
                        step=1,
                        label="Number of Copies (Oligomer State)",
                        info="1 = monomer, 2 = dimer, 3 = trimer …",
                    )
                    cyclic_input = gr.Checkbox(
                        label="Cyclic peptide (N→C terminus connected)",
                        value=False,
                    )
                    sampling_steps = gr.Slider(
                        10,
                        200,
                        value=50,
                        step=10,
                        label="Sampling Steps",
                        info="More steps → better quality, slower (50 recommended)",
                    )
                    use_msa = gr.Checkbox(value=True, visible=False)

                with gr.Row():
                    predict_btn = gr.Button(
                        "🔬 Predict Structure", variant="primary", scale=2
                    )
                    clear_btn = gr.Button("Clear", variant="secondary", scale=1)

                gr.Markdown("### 📋 Quick Examples")
                with gr.Row():
                    ex_protein = gr.Button(
                        "🧬 Load Insulin", size="sm", elem_classes="example-btn"
                    )
                    ex_ligand = gr.Button(
                        "💊 Add Aspirin", size="sm", elem_classes="example-btn"
                    )

            # ── right: results ───────────────────────────────────────────
            with gr.Column(scale=1):
                gr.Markdown("## 📤 Results")

                status_out = gr.Markdown(
                    "*Waiting for prediction… enter a sequence and click Predict*",
                    elem_classes="status-display",
                )

                viewer_out = gr.HTML(
                    label="3D Structure", elem_classes="molecule-container"
                )

                metrics_out = gr.Markdown(
                    "### 📊 Prediction Metrics\n\n"
                    "*Metrics will appear after prediction*",
                    elem_classes="metrics-display",
                )

                gr.Markdown("### 📈 Confidence Analysis")
                with gr.Tabs():
                    with gr.Tab("PAE Plot"):
                        pae_out = gr.Image(show_label=False, type="filepath")
                    with gr.Tab("pLDDT Plot"):
                        plddt_out = gr.Image(show_label=False, type="filepath")

                download_out = gr.File(label="📥 Download Structure")

                with gr.Accordion("📋 Prediction Logs", open=True):
                    logs_out = gr.Textbox(
                        value="Logs will appear here when prediction starts…",
                        lines=10,
                        max_lines=20,
                        interactive=False,
                        show_label=False,
                        elem_classes="logs-display",
                    )

        # -- footer --------------------------------------------------------
        gr.HTML(
            '<div style="text-align:center;color:#888;font-size:12px;'
            'margin-top:24px;padding:16px">'
            "<p>Powered by <strong>Boltz-2</strong> from MIT Jameel Clinic · "
            "Model released under MIT License</p>"
            '<p><a href="https://github.com/jwohlwend/boltz" target="_blank" '
            'style="color:#b54ce5">GitHub</a> · '
            '<a href="https://jclinic.mit.edu/boltz-1/" target="_blank" '
            'style="color:#b54ce5">Documentation</a></p></div>'
        )

        # -- wiring --------------------------------------------------------
        outputs = [
            viewer_out,
            status_out,
            metrics_out,
            download_out,
            pae_out,
            plddt_out,
            logs_out,
        ]

        predict_btn.click(
            fn=predict_structure,
            inputs=[
                protein_input,
                ligand_input,
                use_msa,
                sampling_steps,
                num_copies,
                cyclic_input,
            ],
            outputs=outputs,
            show_progress="hidden",
        )

        def clear_all():
            return (
                "",
                "",
                None,
                "*Waiting for prediction…*",
                "### 📊 Prediction Metrics\n\n*Metrics will appear after prediction*",
                None,
                None,
                None,
                "Logs will appear here when prediction starts…",
            )

        clear_btn.click(
            fn=clear_all,
            outputs=[
                protein_input,
                ligand_input,
                viewer_out,
                status_out,
                metrics_out,
                download_out,
                pae_out,
                plddt_out,
                logs_out,
            ],
        )
        ex_protein.click(fn=lambda: EXAMPLE_PROTEIN, outputs=protein_input)
        ex_ligand.click(fn=lambda: EXAMPLE_LIGAND, outputs=ligand_input)

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    create_app().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )
