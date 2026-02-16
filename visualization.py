"""
Visualization helpers: 3Dmol.js viewer, PAE heatmap, pLDDT line chart,
and confidence-file discovery in Boltz output directories.
"""

import base64
import glob
import json
import os
from typing import Optional

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ---------------------------------------------------------------------------
# AlphaFold-style pLDDT colour thresholds
# ---------------------------------------------------------------------------
PLDDT_COLORS = {
    90: "#0053d6",  # very high — blue
    70: "#65cbf3",  # confident — cyan
    50: "#ffdb13",  # low — yellow
    0:  "#ff7d45",  # very low — orange
}

def _plddt_color(score: float) -> str:
    for threshold in (90, 70, 50):
        if score >= threshold:
            return PLDDT_COLORS[threshold]
    return PLDDT_COLORS[0]


# ---------------------------------------------------------------------------
# 3D viewer (3Dmol.js in an iframe)
# ---------------------------------------------------------------------------

_VIEWER_TEMPLATE = """<!DOCTYPE html>
<html><head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://3dmol.org/build/3Dmol-min.js"></script>
<style>
  body {{ margin:0; padding:0; overflow:hidden }}
  #viewer {{ width:100%; height:100%; position:absolute; top:0; left:0 }}
  #cbar {{ position:absolute; right:10px; top:50%; transform:translateY(-50%);
           width:20px; height:200px; border-radius:4px; border:1px solid #ccc;
           background:linear-gradient(to bottom,#0053d6 0%,#65cbf3 33%,#ffdb13 66%,#ff7d45 100%) }}
  #cbar-labels {{ position:absolute; right:35px; top:50%; transform:translateY(-50%);
                  height:200px; display:flex; flex-direction:column; justify-content:space-between;
                  font:500 12px Arial; color:#fff }}
  #cbar-title {{ position:absolute; right:60px; top:50%;
                 transform:translateY(-50%) rotate(-90deg);
                 font:500 12px Arial; color:#fff; white-space:nowrap }}
</style></head><body>
<div id="viewer"></div>
<div id="cbar"></div>
<div id="cbar-labels"><span>100</span><span>90</span><span>70</span><span>50</span><span>0</span></div>
<div id="cbar-title">pLDDT Score</div>
<script>
$(function(){{
  var v=$3Dmol.createViewer('viewer',{{backgroundColor:'#1a1a2e'}});
  var d="{data}";
  d=d.replace(/\\\\n/g,'\\n');
  v.addModel(d,"{fmt}");
  v.setStyle({{}},{{cartoon:{{
    colorfunc:function(a){{
      var b=a.b;
      if(b>90) return '#0053d6';
      if(b>70) return '#65cbf3';
      if(b>50) return '#ffdb13';
      return '#ff7d45';
    }}, arrows:true, tubes:true
  }}}});
  v.setStyle({{resn:['LIG','UNK','UNL']}},{{
    stick:{{colorscheme:'purpleCarbon',radius:0.2}},
    sphere:{{scale:0.25}}
  }});
  v.zoomTo(); v.render(); v.spin('y',0.5);
}});
</script></body></html>"""


def viewer_html(structure_text: str, fmt: str = "cif") -> str:
    """Return an <iframe> embedding a 3Dmol.js viewer for *structure_text*."""
    escaped = (structure_text
               .replace("\\", "\\\\")
               .replace("`", "\\`").replace("$", "\\$")
               .replace("\r\n", "\\n").replace("\r", "\\n").replace("\n", "\\n")
               .replace("'", "\\'").replace('"', '\\"'))
    inner = _VIEWER_TEMPLATE.format(data=escaped, fmt=fmt)
    b64 = base64.b64encode(inner.encode()).decode()
    return (f'<iframe src="data:text/html;base64,{b64}" '
            f'style="width:100%;height:500px;border:none;border-radius:12px;'
            f'background:#1a1a2e" sandbox="allow-scripts allow-same-origin"></iframe>')


# ---------------------------------------------------------------------------
# Confidence plots
# ---------------------------------------------------------------------------

def plot_pae(matrix: np.ndarray, out_path: str) -> Optional[str]:
    """Create and save a PAE heatmap. Returns *out_path* on success."""
    if not HAS_MPL:
        return None
    try:
        fig, ax = plt.subplots(figsize=(8, 7))
        im = ax.imshow(matrix, cmap="Greens_r", vmin=0, vmax=30, aspect="equal")

        cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label("Expected Position Error (Å)", fontsize=11)

        n = matrix.shape[0]
        step = 150 if n > 500 else (50 if n > 200 else 25)
        ticks = np.arange(0, n, step)
        ax.set_xticks(ticks); ax.set_xticklabels(ticks + 1)
        ax.set_yticks(ticks); ax.set_yticklabels(ticks + 1)
        ax.set_xlabel("Scored Residue", fontsize=12)
        ax.set_ylabel("Aligned Residue", fontsize=12)

        # Dark theme
        for obj in (ax, fig):
            obj.set_facecolor("#1a1a2e") if hasattr(obj, "set_facecolor") else None
            getattr(obj.patch, "set_facecolor", lambda _: None)("#1a1a2e")
        ax.tick_params(colors="white")
        for lbl in (ax.xaxis.label, ax.yaxis.label):
            lbl.set_color("white")
        cbar.ax.yaxis.set_tick_params(color="white")
        cbar.outline.set_edgecolor("white")
        cbar.ax.yaxis.label.set_color("white")
        plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")
        for sp in ax.spines.values():
            sp.set_edgecolor("white")

        fig.set_facecolor("#1a1a2e")
        ax.set_facecolor("#1a1a2e")
        plt.tight_layout()
        plt.savefig(out_path, dpi=150, facecolor="#1a1a2e",
                    bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        return out_path
    except Exception as exc:
        print(f"PAE plot error: {exc}")
        return None


def plot_plddt(scores: np.ndarray, out_path: str) -> Optional[str]:
    """Create and save a per-residue pLDDT chart. Returns *out_path*."""
    if not HAS_MPL:
        return None
    try:
        fig, ax = plt.subplots(figsize=(10, 4))
        x = np.arange(1, len(scores) + 1)

        ax.fill_between(x, scores, alpha=0.3, color="#65cbf3")
        ax.plot(x, scores, color="#0053d6", linewidth=1.5)

        # Confidence bands
        bands = [(90, 100, "#0053d6", "Very high (>90)"),
                 (70, 90,  "#65cbf3", "Confident (70-90)"),
                 (50, 70,  "#ffdb13", "Low (50-70)"),
                 (0,  50,  "#ff7d45", "Very low (<50)")]
        for lo, hi, c, lbl in bands:
            ax.axhspan(lo, hi, alpha=0.1, color=c, label=lbl)

        ax.set(xlabel="Residue Position", ylabel="pLDDT Score",
               xlim=(1, len(scores)), ylim=(0, 100))
        ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
        ax.grid(True, alpha=0.3, linestyle="--"); ax.set_axisbelow(True)
        ax.set_facecolor("white"); fig.patch.set_facecolor("white")

        plt.tight_layout()
        plt.savefig(out_path, dpi=150, facecolor="white",
                    bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)
        return out_path
    except Exception as exc:
        print(f"pLDDT plot error: {exc}")
        return None


# ---------------------------------------------------------------------------
# Confidence-file discovery
# ---------------------------------------------------------------------------

def find_confidence_files(base_dir: str) -> dict:
    """Search *base_dir* (and parents) for PAE/pLDDT npz and confidence JSON."""
    result = {"pae": None, "plddt": None, "confidence_json": None}
    dirs = [base_dir]
    for _ in range(2):
        p = os.path.dirname(dirs[-1])
        if p:
            dirs.append(p)

    for d in dirs:
        for f in glob.glob(os.path.join(d, "**", "*.npz"), recursive=True):
            name = os.path.basename(f).lower()
            if "pae" in name and not result["pae"]:
                result["pae"] = f
            elif "plddt" in name and not result["plddt"]:
                result["plddt"] = f
        for f in glob.glob(os.path.join(d, "**", "confidence*.json"), recursive=True):
            if not result["confidence_json"]:
                result["confidence_json"] = f
    return result


# ---------------------------------------------------------------------------
# pLDDT score loaders
# ---------------------------------------------------------------------------

def _squeeze_array(arr: np.ndarray) -> np.ndarray:
    """Remove batch dims, flatten, and scale 0-1 → 0-100 if needed."""
    if arr.ndim == 3:
        arr = arr[0]
    if arr.ndim == 2:
        arr = arr.mean(axis=-1) if arr.shape[-1] < arr.shape[0] else arr.mean(axis=0)
    arr = arr.flatten()
    if arr.max() <= 1.0:
        arr = arr * 100
    return arr


def _load_npz(path: str, keys: list[str]) -> Optional[np.ndarray]:
    try:
        data = np.load(path)
        for k in keys:
            if k in data.files:
                return _squeeze_array(data[k])
        return _squeeze_array(data[data.files[0]])
    except Exception:
        return None


def extract_plddt_from_cif(cif_path: str) -> Optional[np.ndarray]:
    """Read per-residue B-factors (= pLDDT) from a CIF file."""
    try:
        by_residue: dict[int, float] = {}
        with open(cif_path) as fh:
            in_atom = False
            headers: list[str] = []
            b_idx = res_idx = -1
            for line in fh:
                line = line.strip()
                if line.startswith("_atom_site."):
                    in_atom = True
                    h = line.split(".")[1]
                    headers.append(h)
                    if "B_iso" in h or "b_factor" in h.lower():
                        b_idx = len(headers) - 1
                    if "label_seq_id" in h:
                        res_idx = len(headers) - 1
                    continue
                if in_atom and line and not line.startswith(("_", "#")):
                    if line.startswith("loop_"):
                        in_atom = False
                        continue
                    parts = line.split()
                    if len(parts) > max(b_idx, res_idx) and b_idx >= 0 and res_idx >= 0:
                        try:
                            rid = int(parts[res_idx])
                            if rid not in by_residue:
                                by_residue[rid] = float(parts[b_idx])
                        except (ValueError, IndexError):
                            pass
        if by_residue:
            return np.array([by_residue[r] for r in sorted(by_residue)])
        return None
    except Exception:
        return None


def load_plddt(*, npz_path: str | None = None,
               json_path: str | None = None,
               cif_path: str | None = None) -> Optional[np.ndarray]:
    """Try CIF → npz → JSON to get pLDDT scores."""
    if cif_path and os.path.exists(cif_path):
        arr = extract_plddt_from_cif(cif_path)
        if arr is not None and len(arr):
            return arr
    if npz_path and os.path.exists(npz_path):
        arr = _load_npz(npz_path, ["plddt", "predicted_lddt", "confidence", "data"])
        if arr is not None:
            return arr
    if json_path and os.path.exists(json_path):
        try:
            with open(json_path) as fh:
                data = json.load(fh)
            for k in ("plddt", "atom_plddt", "confidence", "predicted_lddt"):
                if k in data:
                    arr = np.array(data[k])
                    return arr * 100 if arr.max() <= 1.0 else arr
        except Exception:
            pass
    return None


def load_pae(npz_path: str) -> Optional[np.ndarray]:
    """Load a PAE matrix from an npz file."""
    return _load_npz(npz_path, ["pae", "predicted_aligned_error", "data"])
