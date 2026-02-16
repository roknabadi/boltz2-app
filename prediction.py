"""
Boltz-2 prediction pipeline: input validation, YAML generation,
subprocess execution, and result parsing.
"""

import glob
import json
import os
import re
import subprocess

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")
MIN_SEQ_LENGTH = 10
MAX_SEQ_LENGTH = 2500
PREDICTION_TIMEOUT = 1800  # 30 minutes

OLIGOMER_NAMES = {
    1: "monomer", 2: "dimer", 3: "trimer", 4: "tetramer",
    5: "pentamer", 6: "hexamer", 7: "heptamer", 8: "octamer",
}

# ---------------------------------------------------------------------------
# Input parsing / validation
# ---------------------------------------------------------------------------

def parse_fasta(fasta_text: str) -> tuple[str, str]:
    """Return (header, sequence) from FASTA or raw sequence text."""
    lines = fasta_text.strip().split("\n")
    header = ""
    parts: list[str] = []

    for line in lines:
        line = line.strip()
        if line.startswith(">"):
            header = line[1:].strip()
        elif line:
            parts.append("".join(c for c in line if c.isalpha()).upper())

    sequence = "".join(parts)

    # Raw sequence (no > header)
    if not header and not any(l.startswith(">") for l in lines):
        sequence = "".join(c for c in fasta_text if c.isalpha()).upper()
        header = "protein"

    # Sanitise header for filenames
    if header:
        header = "".join(c if c.isalnum() or c == "_" else "_" for c in header)[:30]

    return header, sequence


def validate_protein(sequence: str) -> tuple[bool, str]:
    """Return (ok, cleaned_sequence_or_error)."""
    seq = sequence.upper().replace(" ", "").replace("\n", "")
    bad = set(seq) - VALID_AMINO_ACIDS
    if bad:
        return False, f"Invalid amino acids: {', '.join(sorted(bad))}"
    if len(seq) < MIN_SEQ_LENGTH:
        return False, f"Sequence too short (minimum {MIN_SEQ_LENGTH} residues)"
    if len(seq) > MAX_SEQ_LENGTH:
        return False, f"Sequence too long ({len(seq)} aa). Max {MAX_SEQ_LENGTH} due to GPU memory."
    return True, seq


def validate_smiles(smiles: str) -> tuple[bool, str]:
    """Basic SMILES plausibility check. Empty string is valid (optional)."""
    if not smiles or not smiles.strip():
        return True, ""
    smiles = smiles.strip()
    allowed = set("CNOPSFIBrcnosp[]()=#@+-.0123456789\\/Hhelakbr")
    bad = set(smiles) - allowed
    if bad:
        return False, f"Invalid SMILES characters: {', '.join(sorted(bad))}"
    return True, smiles


def oligomer_name(n: int) -> str:
    return OLIGOMER_NAMES.get(n, f"{n}-mer")


# ---------------------------------------------------------------------------
# YAML generation
# ---------------------------------------------------------------------------

def create_boltz_yaml(
    sequence: str,
    output_dir: str,
    *,
    ligand_smiles: str | None = None,
    protein_name: str = "protein",
    cyclic: bool = False,
    num_copies: int = 1,
) -> str:
    """Write a Boltz-2 input YAML and return its path."""
    chain_ids = [chr(ord("A") + i) for i in range(num_copies)]

    lines = ["version: 1", "sequences:", "  - protein:"]

    if num_copies > 1:
        id_list = ", ".join(f'"{c}"' for c in chain_ids)
        lines.append(f"      id: [{id_list}]")
    else:
        lines.append(f'      id: "{chain_ids[0]}"')

    lines.append(f"      sequence: {sequence}")
    if cyclic:
        lines.append("      cyclic: true")

    if ligand_smiles:
        lig_id = chr(ord("A") + num_copies)
        lines += [
            "  - ligand:",
            f'      id: "{lig_id}"',
            f'      smiles: "{ligand_smiles}"',
        ]

    yaml_text = "\n".join(lines) + "\n"
    yaml_path = os.path.join(output_dir, "input.yaml")
    with open(yaml_path, "w") as fh:
        fh.write(yaml_text)
    return yaml_path


# ---------------------------------------------------------------------------
# Boltz-2 runner
# ---------------------------------------------------------------------------

def _build_command(yaml_path: str, output_dir: str, sampling_steps: int,
                   seq_len: int) -> list[str]:
    """Assemble the `boltz predict` CLI invocation."""
    cmd = [
        "boltz", "predict", yaml_path,
        "--out_dir", output_dir,
        "--sampling_steps", str(sampling_steps),
        "--accelerator", "gpu",
        "--override",
        "--use_msa_server",
    ]
    if seq_len > 1000:
        cmd += ["--recycling_steps", "1", "--diffusion_samples", "1"]
    elif seq_len > 500:
        cmd += ["--recycling_steps", "2", "--diffusion_samples", "1"]
    return cmd


def _find_predictions_dir(output_dir: str) -> str | None:
    """Locate the predictions/ folder Boltz creates."""
    for pattern in ["boltz_results_*"]:
        dirs = sorted(glob.glob(os.path.join(output_dir, pattern)),
                      key=os.path.getmtime, reverse=True)
        if dirs:
            pred = os.path.join(dirs[0], "predictions")
            if os.path.isdir(pred):
                return pred
    direct = os.path.join(output_dir, "predictions")
    return direct if os.path.isdir(direct) else None


def _collect_metrics(json_files: list[str]) -> dict:
    """Read Boltz JSON outputs and collect confidence metrics."""
    metrics: dict = {}
    metric_keys = {
        "confidence": "confidence",
        "plddt": "plddt",
        "ptm": "ptm",
        "affinity_pred_value": "affinity",
        "affinity": "affinity",
        "affinity_probability_binary": "binding_probability",
    }
    for path in json_files:
        try:
            with open(path) as fh:
                data = json.load(fh)
            for src_key, dst_key in metric_keys.items():
                if src_key in data and dst_key not in metrics:
                    metrics[dst_key] = data[src_key]
        except Exception as exc:
            print(f"Warning: failed to read {path}: {exc}")
    return metrics


def _extract_error(output: str, seq_len: int, log_path: str) -> str:
    """Return a human-friendly error from Boltz stderr/stdout."""
    if "CUDA out of memory" in output or "OutOfMemoryError" in output:
        return (f"GPU out of memory. Sequence ({seq_len} aa) is too long for "
                "this GPU. Try shorter or use a bigger GPU.")
    if "No such file or directory" in output:
        return "Input file error — check your sequence format."
    if "KeyError" in output:
        m = re.search(r"KeyError: ['\"]?([^'\"]+)['\"]?", output)
        key = m.group(1) if m else "unknown"
        return f"YAML parsing error: KeyError '{key}' — chain ID format may be wrong."

    lines = output.split("\n")
    # Look for a Python traceback
    tb_start = next((i for i, l in enumerate(lines)
                     if "Traceback" in l), None)
    if tb_start is not None:
        tail = [l for l in lines[tb_start:] if l.strip()][-20:]
        return "Prediction failed:\n" + "\n".join(tail)

    # Fall back to error-ish lines
    errs = [l for l in lines if "Error:" in l or "Exception:" in l]
    if errs:
        return "\n".join(errs[-5:])

    clean = [l for l in lines if l.strip()
             and not any(x in l for x in ["%|", "it/s", "━", "warnings.warn"])]
    return "\n".join(clean[-15:]) or f"Unknown error — see {log_path}"


def run_prediction(yaml_path: str, output_dir: str, *,
                   sampling_steps: int = 50,
                   seq_len: int = 0) -> tuple[bool, str, dict, str]:
    """
    Execute Boltz-2 and return (success, structure_path_or_error, metrics, raw_log).
    """
    os.environ["TORCH_FLOAT32_MATMUL_PRECISION"] = "medium"

    cmd = _build_command(yaml_path, output_dir, sampling_steps, seq_len)
    log_path = os.path.join(output_dir, "boltz_log.txt")
    raw_log = f"Command: {' '.join(cmd)}\n\n"

    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=PREDICTION_TIMEOUT)
        raw_log += (f"Return code: {result.returncode}\n\n"
                    f"=== STDOUT ===\n{result.stdout or '(empty)'}\n\n"
                    f"=== STDERR ===\n{result.stderr or '(empty)'}")
        with open(log_path, "w") as fh:
            fh.write(raw_log)

        pred_dir = _find_predictions_dir(output_dir)
        cif = pdb = json_files = []
        if pred_dir:
            _g = lambda ext: glob.glob(os.path.join(pred_dir, "**", ext), recursive=True)
            cif, pdb, json_files = _g("*.cif"), _g("*.pdb"), _g("*.json")

        structure = (cif or pdb or [None])[0]
        if structure:
            return True, structure, _collect_metrics(json_files), raw_log

        error_text = result.stderr or result.stdout or ""
        return False, _extract_error(error_text, seq_len, log_path), {}, raw_log

    except subprocess.TimeoutExpired:
        return False, "Prediction timed out (>30 min).", {}, raw_log
    except FileNotFoundError:
        return False, "Boltz-2 not found. Ensure 'boltz' is installed and on PATH.", {}, ""
    except Exception as exc:
        return False, f"Error running Boltz-2: {exc}", {}, raw_log
