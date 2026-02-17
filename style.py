"""
Gradio theme and CSS for the Boltz-2 app.

Colors and layout are defined via CSS custom properties so they only
appear once.  The old stylesheet had ~540 lines with dozens of
duplicate `color: #1a1a1a !important` rules and 8+ accordion blocks
doing the same thing.  This consolidates everything into ~130 lines.
"""

import gradio as gr

# ---------------------------------------------------------------------------
# Theme (Gradio's built-in knobs)
# ---------------------------------------------------------------------------

THEME = gr.themes.Soft(
    primary_hue=gr.themes.colors.violet,
    secondary_hue=gr.themes.colors.teal,
    neutral_hue=gr.themes.colors.gray,
).set(
    color_accent="#b54ce5",
    color_accent_soft="rgba(181, 76, 229, 0.1)",
    button_primary_background_fill="linear-gradient(90deg, #b54ce5 0%, #8081e9 50%, #5bc5dc 100%)",
    button_primary_background_fill_hover="linear-gradient(90deg, #a040d0 0%, #7070d8 50%, #4fb5d0 100%)",
    block_background_fill="#ffffff",
    block_label_background_fill="#f8f9fc",
    body_background_fill="linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%)",
    background_fill_primary="#ffffff",
    background_fill_secondary="#f8f9fc",
    border_color_primary="#e0e0e0",
    input_background_fill="#ffffff",
)

# ---------------------------------------------------------------------------
# CSS — all custom-property colours live in :root, everything else
# references them so a palette change is a one-liner.
# ---------------------------------------------------------------------------

CSS = """
/* ── force light mode even when system prefers dark ──────────── */
.dark {
    --background-fill-primary: #ffffff !important;
    --background-fill-secondary: #f8f9fc !important;
    --block-background-fill: #ffffff !important;
    --block-label-background-fill: #f8f9fc !important;
    --body-background-fill: linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%) !important;
    --input-background-fill: #ffffff !important;
    --border-color-primary: #e0e0e0 !important;
    --body-text-color: #1a1a1a !important;
    --block-title-text-color: #1a1a1a !important;
    --block-label-text-color: #1a1a1a !important;
    --neutral-50: #f9fafb !important;
    --neutral-100: #f3f4f6 !important;
    --neutral-200: #e5e7eb !important;
    --neutral-700: #374151 !important;
    --neutral-800: #1f2937 !important;
}

/* ── palette ─────────────────────────────────────────────────── */
:root {
    --c-purple:   #b54ce5;
    --c-blue:     #8081e9;
    --c-teal:     #5bc5dc;
    --c-navy:     #012454;
    --c-text:     #1a1a1a;
    --c-muted:    #555555;
    --c-bg:       #f8f9fc;
    --c-surface:  #ffffff;
    --c-accent-bg: #faf8fc;
    --c-gradient: linear-gradient(90deg, var(--c-purple) 0%, var(--c-blue) 50%, var(--c-teal) 100%);
    --color-accent: var(--c-purple) !important;
    --color-accent-soft: rgba(181, 76, 229, 0.1) !important;
}

/* ── global ──────────────────────────────────────────────────── */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, var(--c-bg) 0%, #eef1f8 100%) !important;
}

/* ── header ──────────────────────────────────────────────────── */
.header-container {
    background: var(--c-surface) !important;
    padding: 24px 32px; border-radius: 16px; margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(1,36,84,.1);
    border: 1px solid #e0e0e0;
}

/* ── typography — single rule for dark body text ─────────────── */
.markdown, .markdown *, .prose, .prose *,
.status-display, .status-display *,
.metrics-display, .metrics-display *,
label, .label-wrap span,
.gr-box, .gr-panel, .gr-form, .gr-block,
code, pre { color: var(--c-text) !important; }

h2, .markdown h2, h3, .markdown h3,
.markdown strong, .prose strong,
.metrics-display strong, .status-display strong { color: var(--c-navy) !important; font-weight: 600 !important; }

.markdown em, .prose em, .status-display em,
.metrics-display em { color: #666 !important; }

.info, [class*="info"] { color: var(--c-muted) !important; }

code, pre { background: #f5f5f5 !important; }

/* ── inputs ──────────────────────────────────────────────────── */
textarea, input[type="text"] {
    border: 2px solid #e0e0e0 !important; border-radius: 8px !important;
    font-family: 'Monaco','Menlo','Courier New',monospace !important;
    font-size: 13px !important;
    color: var(--c-text) !important; background: var(--c-surface) !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: var(--c-blue) !important;
    box-shadow: 0 0 0 3px rgba(128,129,233,.1) !important;
}
input, label, button, select, textarea { pointer-events: auto !important; }

/* ── tabs ────────────────────────────────────────────────────── */
.tabs > .tab-nav { background: transparent !important; border-bottom: 2px solid var(--c-navy) !important; }
.tab-nav button, div[role="tablist"] button {
    color: var(--c-navy) !important; font-weight: 600 !important;
    border: none !important; background: transparent !important;
    padding: 10px 20px !important; font-size: 14px !important;
    border-bottom: 3px solid transparent !important;
}
.tab-nav button.selected, .tab-nav button[aria-selected="true"],
div[role="tablist"] button[aria-selected="true"],
[class*="svelte-"] button.selected,
[class*="svelte-"] button[aria-selected="true"] {
    color: var(--c-purple) !important;
    border-bottom: 3px solid var(--c-purple) !important;
    background: rgba(181,76,229,.08) !important;
}

/* ── buttons ─────────────────────────────────────────────────── */
button.primary, .gr-button-primary, button[variant="primary"] {
    background: var(--c-gradient) !important; border: none !important;
    color: white !important; font-weight: 600 !important;
    padding: 12px 32px !important; border-radius: 8px !important; font-size: 16px !important;
    transition: all .3s ease !important;
    box-shadow: 0 4px 15px rgba(181,76,229,.3) !important;
}
button.primary:hover, .gr-button-primary:hover, button[variant="primary"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(181,76,229,.4) !important;
}
button.secondary, button[variant="secondary"] {
    background: var(--c-navy) !important; border: none !important;
    color: white !important; font-weight: 500 !important;
}
.example-btn { background: rgba(1,36,84,.15) !important; color: var(--c-navy) !important; border: 1px solid var(--c-navy) !important; font-size: 13px !important; }
.example-btn:hover { background: var(--c-navy) !important; color: white !important; }

/* ── accordion / settings ────────────────────────────────────── */
.accordion, [class*="accordion"], .gr-accordion,
div[data-testid="accordion"],
.gr-group, .gr-box, .gr-form, .gr-panel {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 1px solid #e0e0e0 !important; border-radius: 8px !important;
}
.accordion > button, [class*="accordion"] > button,
button[aria-expanded], .label-wrap {
    background: #f0f0f5 !important; color: var(--c-navy) !important; font-weight: 600 !important;
}
/* Force ALL nested elements inside accordion to have light backgrounds */
.gr-accordion *, .gr-accordion div,
[class*="accordion"] *, [class*="accordion"] div,
div[data-testid="accordion"] *, div[data-testid="accordion"] div {
    color: var(--c-text) !important;
    background-color: #ffffff !important;
}
/* Re-apply specific backgrounds that need to differ */
.gr-accordion button[aria-expanded], [class*="accordion"] button[aria-expanded] {
    background-color: #f0f0f5 !important;
}
.gr-accordion input[type="range"], [class*="accordion"] input[type="range"] {
    background-color: transparent !important;
}
.gr-accordion input[type="checkbox"], [class*="accordion"] input[type="checkbox"] {
    background-color: transparent !important;
}

input[type="range"] { accent-color: var(--c-purple) !important; }
input[type="checkbox"] { accent-color: #22c55e !important; cursor: pointer !important; }
.gr-accordion input[type="number"] { background: white !important; color: var(--c-text) !important; border: 1px solid #ccc !important; }

/* ── molecule viewer ─────────────────────────────────────────── */
.molecule-container { border: 2px solid rgba(128,129,233,.2); border-radius: 12px; overflow: hidden; }

/* ── logs (terminal look) ────────────────────────────────────── */
.logs-display textarea, .logs-display .gr-textbox textarea {
    font-family: 'Monaco','Menlo','Courier New',monospace !important;
    font-size: 11px !important; line-height: 1.4 !important;
    background: #1e1e2e !important; color: #a6e3a1 !important;
    border: none !important; border-radius: 8px !important; padding: 12px !important;
}
.logs-display, .logs-display > div { background: #1e1e2e !important; border-radius: 8px !important; border: 1px solid #333 !important; }

/* ── hide Gradio progress spinners (we show our own logs) ──── */
.progress-bar, .gr-progress, [class*="progress"],
.wrap.default.generating, .wrap.default.translucent,
.generating, .translucent, .pending, .loading {
    display: none !important; visibility: hidden !important; opacity: 0 !important;
}

/* ── footer ──────────────────────────────────────────────────── */
.footer a { color: var(--c-purple) !important; text-decoration: none; }
"""
