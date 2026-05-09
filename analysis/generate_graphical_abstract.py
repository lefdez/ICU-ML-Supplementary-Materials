"""
Generate a graphical abstract (1600x1200 px) for the JCM manuscript.
Summarizes the systematic review and meta-analysis key findings.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import os

# ── Configuration ──────────────────────────────────────────────
DPI = 200
W_IN = 1600 / DPI
H_IN = 1200 / DPI

# MDPI-friendly colour palette
C_BG       = "#FFFFFF"
C_HEADER   = "#1B4F72"
C_ACCENT   = "#2E86C1"
C_LIGHT    = "#D6EAF8"
C_GREEN    = "#27AE60"
C_YELLOW   = "#F1C40F"
C_RED      = "#E74C3C"
C_GRAY     = "#7F8C8D"
C_TEXT     = "#2C3E50"

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(OUT_DIR, "graphical_abstract_jcm.png")

# ── Create figure ──────────────────────────────────────────────
fig = plt.figure(figsize=(W_IN, H_IN), dpi=DPI, facecolor=C_BG)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

# ── Title banner ───────────────────────────────────────────────
title_box = FancyBboxPatch((1, 88), 98, 11, boxstyle="round,pad=0.5",
                           facecolor=C_HEADER, edgecolor="none")
ax.add_patch(title_box)
ax.text(50, 94.5, "Machine Learning Models for Predicting\nUnplanned Readmission & Mortality in the ICU",
        ha="center", va="center", fontsize=8.5, fontweight="bold", color="white",
        linespacing=1.4)
ax.text(50, 89.5, "Systematic Review and Meta-Analysis (PRISMA 2020)",
        ha="center", va="center", fontsize=6, color="#AED6F1", style="italic")

# ── Left column: PRISMA flow (simplified) ─────────────────────
# Identification
prisma_x = 25
box_w = 28
bh = 5.5

def draw_box(x, y, w, h, text, fc=C_LIGHT, fs=5.5, fw="normal"):
    b = FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.3",
                       facecolor=fc, edgecolor=C_ACCENT, linewidth=0.8)
    ax.add_patch(b)
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight=fw,
            color=C_TEXT, linespacing=1.3)

def draw_arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=C_ACCENT, lw=1.0))

ax.text(prisma_x, 85, "Study Selection", ha="center", fontsize=7, fontweight="bold", color=C_HEADER)

draw_box(prisma_x, 80, box_w, bh, "Identified: 4,105 records\n(Scopus, WoS, PubMed, IEEE)", fc="#EBF5FB")
draw_arrow(prisma_x, 77.2, prisma_x, 74.3)
draw_box(prisma_x, 71.5, box_w, bh, "Screened: 2,213\n(after duplicates removed)", fc="#D4EFDF")
draw_arrow(prisma_x, 68.7, prisma_x, 65.8)
draw_box(prisma_x, 63, box_w, bh, "Full-text assessed: 13", fc="#FDEBD0")
draw_arrow(prisma_x, 60.2, prisma_x, 57.3)
draw_box(prisma_x, 54.5, box_w, bh, "Included: 8 studies\n(2020\u20132025)", fc=C_LIGHT, fw="bold")

# ── Left column bottom: Risk of Bias ──────────────────────────
ax.text(prisma_x, 48, "Risk of Bias (PROBAST)", ha="center", fontsize=6.5, fontweight="bold", color=C_HEADER)

rob_y = 44.5
rob_data = [("Low Risk", 3, C_GREEN), ("Some Concerns", 5, C_YELLOW), ("High Risk", 0, C_RED)]
bar_w_total = 26
bar_h = 3.5
x_start = prisma_x - bar_w_total / 2
total = 8
for label, count, color in rob_data:
    seg_w = (count / total) * bar_w_total if count > 0 else 0
    if seg_w > 0:
        b = FancyBboxPatch((x_start, rob_y - bar_h/2), seg_w, bar_h,
                           boxstyle="round,pad=0.15", facecolor=color, edgecolor="white", linewidth=0.5)
        ax.add_patch(b)
        if seg_w > 3:
            ax.text(x_start + seg_w/2, rob_y, f"{count}", ha="center", va="center",
                    fontsize=6, fontweight="bold", color="white")
        x_start += seg_w

# Legend for risk of bias
for i, (label, count, color) in enumerate(rob_data):
    lx = prisma_x - 13 + i * 10
    ax.plot(lx, 40.5, "o", markersize=4, color=color)
    ax.text(lx + 1.2, 40.5, f"{label} ({count})", fontsize=4.5, va="center", color=C_TEXT)

# ── Right column: Key Results ─────────────────────────────────
rx = 72
ax.text(rx, 85, "Key Results", ha="center", fontsize=7, fontweight="bold", color=C_HEADER)

# Pooled AUC-ROC highlight box
highlight_box = FancyBboxPatch((rx - 17, 75), 34, 8, boxstyle="round,pad=0.5",
                               facecolor=C_ACCENT, edgecolor="none", alpha=0.1)
ax.add_patch(highlight_box)
ax.text(rx, 81.5, "Pooled AUC-ROC", ha="center", fontsize=6, color=C_ACCENT, fontweight="bold")
ax.text(rx, 78.5, "0.791", ha="center", fontsize=14, fontweight="bold", color=C_HEADER)
ax.text(rx, 75.8, "(95% CI: 0.775\u20130.807 \u00b7 I\u00b2 = 86.5%)", ha="center", fontsize=5, color=C_GRAY)

# ── AUC-ROC Top Models (framed) ───────────────────────────────
ax.text(rx, 72.5, "Top Model Architectures (AUC-ROC)", ha="center", fontsize=6,
        fontweight="bold", color=C_HEADER)

auroc_frame = FancyBboxPatch((rx - 17, 55), 34, 16, boxstyle="round,pad=0.5",
                             facecolor="#EBF5FB", edgecolor=C_ACCENT, linewidth=0.8, alpha=0.45)
ax.add_patch(auroc_frame)

models = [
    ("Transformer", 0.909, C_ACCENT),
    ("CTCL", 0.874, "#2980B9"),
    ("GRU+Attention", 0.868, "#3498DB"),
    ("LR (k=5)", 0.785, "#5DADE2"),
    ("RF (k=4)", 0.780, "#85C1E9"),
    ("XGBoost (k=3)", 0.768, "#AED6F1"),
]

bar_y_start = 69
bar_spacing = 2.5
max_bar = 22
for i, (name, auc, color) in enumerate(models):
    by = bar_y_start - i * bar_spacing
    bw = (auc / 1.0) * max_bar
    b = FancyBboxPatch((rx - 7, by - 0.9), bw, 1.8, boxstyle="round,pad=0.15",
                       facecolor=color, edgecolor="none", alpha=0.85)
    ax.add_patch(b)
    ax.text(rx - 8, by, name, ha="right", va="center", fontsize=4.8, color=C_TEXT)
    ax.text(rx - 7 + bw + 0.6, by, f"{auc:.3f}", ha="left", va="center",
            fontsize=4.8, fontweight="bold", color=C_TEXT)

# ── Precision-Recall (AUC-PRC / AP) Panel ─────────────────────
ax.text(rx, 49.5, "Precision–Recall Metrics (22 entries, 4 studies)", ha="center", fontsize=6,
        fontweight="bold", color=C_HEADER)

prc_box = FancyBboxPatch((rx - 17, 34), 34, 14.5, boxstyle="round,pad=0.5",
                         facecolor="#FEF9E7", edgecolor=C_YELLOW, linewidth=0.8, alpha=0.6)
ax.add_patch(prc_box)

# Mini bar chart for top AUC-PRC models
prc_models = [
    ("CTCL",        0.853, "#E74C3C"),
    ("Transformer", 0.834, "#E67E22"),
    ("RF",          0.829, "#F39C12"),
    ("LR",          0.803, "#F1C40F"),
]
prc_bar_y = 46.5
prc_spacing = 2.5
prc_max_bar = 22
ax.text(rx - 15.5, 47.8, "AUC-PRC (top pooled)", fontsize=5, fontweight="bold", color=C_TEXT)
for i, (name, val, color) in enumerate(prc_models):
    by = prc_bar_y - i * prc_spacing
    bw = (val / 1.0) * prc_max_bar
    b = FancyBboxPatch((rx - 7, by - 0.9), bw, 1.8, boxstyle="round,pad=0.15",
                       facecolor=color, edgecolor="none", alpha=0.75)
    ax.add_patch(b)
    ax.text(rx - 8, by, name, ha="right", va="center", fontsize=4.8, color=C_TEXT)
    ax.text(rx - 7 + bw + 0.6, by, f"{val:.3f}", ha="left", va="center",
            fontsize=4.8, fontweight="bold", color=C_TEXT)

# AP range note
ax.text(rx, 35.5, "AP (composite outcome): 0.063–0.114  |  Gap vs AUC-PRC: >6×",
        ha="center", va="center", fontsize=4.8, color=C_RED, style="italic")

# ── Bottom strip: Summary stats ───────────────────────────────
bottom_box = FancyBboxPatch((1, 1), 98, 10, boxstyle="round,pad=0.5",
                            facecolor="#F8F9FA", edgecolor=C_ACCENT, linewidth=0.5)
ax.add_patch(bottom_box)

stats = [
    ("8", "Studies\nIncluded"),
    ("17", "ML Model\nFamilies"),
    ("78", "AUC-ROC\nMetrics"),
    ("4", "Databases\nSearched"),
    ("2020–2025", "Study\nPeriod"),
]

for i, (val, label) in enumerate(stats):
    sx = 10 + i * 20
    ax.text(sx, 8, val, ha="center", va="center", fontsize=10, fontweight="bold", color=C_HEADER)
    ax.text(sx, 4.5, label, ha="center", va="center", fontsize=4.8, color=C_GRAY, linespacing=1.2)

# ── GRADE box (bottom-left area) ──────────────────────────────
ax.text(prisma_x, 36, "GRADE Certainty", ha="center", fontsize=6.5, fontweight="bold", color=C_HEADER)
grade_box = FancyBboxPatch((prisma_x - 13, 32), 26, 3.5, boxstyle="round,pad=0.3",
                           facecolor="#FADBD8", edgecolor=C_RED, linewidth=0.6)
ax.add_patch(grade_box)
ax.text(prisma_x, 33.8, "⊕○○○  Very Low (all outcomes)", ha="center", va="center",
        fontsize=5.5, fontweight="bold", color=C_RED)

# ── Conclusion box ────────────────────────────────────────────
conclusion_box = FancyBboxPatch((3, 14.5), 94, 13, boxstyle="round,pad=0.5",
                                facecolor="#EBF5FB", edgecolor=C_ACCENT, linewidth=0.8)
ax.add_patch(conclusion_box)
ax.text(50, 25, "Key Conclusions", ha="center", fontsize=7, fontweight="bold", color=C_HEADER)
conclusions = (
    "• Deep learning models (Transformer, CTCL, GRU+Attention) achieve the highest AUC-ROC estimates\n"
    "• Classical models (LR, RF, XGBoost) provide more replicated and robust evidence\n"
    "• High heterogeneity (I² = 86.5%) and predominantly internal validation limit generalizability\n"
    "• Prospective multicenter studies with external validation are needed for clinical utility"
)
ax.text(50, 19, conclusions, ha="center", va="center", fontsize=5.3, color=C_TEXT, linespacing=1.6)

# ── Save ──────────────────────────────────────────────────────
fig.savefig(OUT_FILE, dpi=DPI, bbox_inches="tight", pad_inches=0.05, facecolor=C_BG)
plt.close(fig)
print(f"Graphical abstract saved to: {OUT_FILE}")
print(f"Dimensions: {1600}x{1200} px (approx)")
