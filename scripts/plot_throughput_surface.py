#!/usr/bin/env python3
"""
plot_throughput_surface.py: Multi-dimensional visualization suite for CHIP-KNN design space.

Generates dark-mode, pastel-themed graphical representations of KNN accelerator throughput
across dimension (D) and processing element (PE) counts from sweep_summary.csv:
1. 3D Surface & Wireframe: Continuous feature throughput landscape across (D, PE).
2. 2D Heatmap & Contour: Discrete configuration matrix with iso-throughput contours.
3. Scaling Profiles: Throughput scaling per dimension with physical saturation markers.
4. Architectural Efficiency: Throughput per kLUT (logic efficiency) across the space.
5. Comprehensive Dashboard: Multi-panel synthesis of all key design space trade-offs.

Aesthetic follows code49 dark-mode pastel system (Base16 / JetBrains Mono).
"""

import os
import sys
import argparse
import csv
import numpy as np

# Matplotlib configuration (headless friendly)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

# ==============================================================================
# Theme & Color Palette Definitions
# ==============================================================================
THEME = {
    "bg_primary": "#1d1f21",       # Deep dark grey/black
    "bg_secondary": "#282a2e",     # Cards, panels, plot faces
    "border": "#373b41",           # Separators, spines, grids
    "text_muted": "#969896",       # Captions, secondary labels
    "text_secondary": "#c5c8c6",   # Axis labels, subtitles
    "text_primary": "#f0f0f0",     # Titles, major annotations
    
    # Pastel Accents
    "accent_purple": "#bdb2ff",    # Primary accent (soft lavender)
    "accent_magenta": "#daa9ff",   # Secondary accent (soft magenta)
    "accent_pink": "#f8cfd2",      # Glow / tertiary
    "accent_green": "#caffbf",     # Success / Peak
    "accent_yellow": "#fdffb6",    # Highlights
    "accent_red": "#ffadad",       # Saturation / limits
    "accent_cyan": "#9bf6ff",      # Sky blue / info
    "accent_blue": "#a0c4ff",      # Blue
}

# Custom pastel sequential colormap
PASTEL_CMAP = LinearSegmentedColormap.from_list(
    "pastel_throughput",
    [
        (0.00, THEME["bg_secondary"]),
        (0.20, "#373b41"),
        (0.40, THEME["accent_blue"]),
        (0.65, THEME["accent_purple"]),
        (0.85, THEME["accent_magenta"]),
        (1.00, THEME["accent_green"]),
    ],
    N=256
)

def apply_theme():
    """Apply global matplotlib style rules matching code49 aesthetic."""
    plt.rcParams.update({
        "figure.facecolor": THEME["bg_primary"],
        "figure.edgecolor": THEME["border"],
        "axes.facecolor": THEME["bg_secondary"],
        "axes.edgecolor": THEME["border"],
        "axes.labelcolor": THEME["text_secondary"],
        "axes.titlecolor": THEME["text_primary"],
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.labelsize": 10,
        "axes.labelweight": "normal",
        "axes.grid": True,
        "grid.color": THEME["border"],
        "grid.linestyle": ":",
        "grid.alpha": 0.6,
        "xtick.color": THEME["text_muted"],
        "ytick.color": THEME["text_muted"],
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "text.color": THEME["text_primary"],
        "font.family": "sans-serif",
        "font.sans-serif": ["JetBrains Mono", "DejaVu Sans Mono", "Inter", "sans-serif"],
        "figure.titlesize": 15,
        "figure.titleweight": "bold",
        "savefig.facecolor": THEME["bg_primary"],
        "savefig.edgecolor": THEME["border"],
    })


def load_sweep_data(csv_path):
    """
    Parse sweep_summary.csv and return structured records.
    Filters valid numerical configurations.
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"Sweep summary file not found: {csv_path}")

    records = []
    with open(csv_path, "r") as cf:
        reader = csv.DictReader(cf)
        for row in reader:
            try:
                dim = int(row["Dim"])
                pe = int(row["PE"])
                status = row.get("Status", "UNKNOWN")
                
                # Throughput in Mfeat/s
                tp_est = float(row.get("Est_Throughput_Mfeat_s", 0.0) or 0.0)
                
                # Simulation throughput if available
                sim_tp = float(row.get("Sim_Throughput_Mfeat_s", 0.0) or 0.0) if row.get("Sim_Throughput_Mfeat_s", "-") != "-" else None
                
                # Implementation metrics
                impl_lut = float(row.get("Impl_LUT", 0) or 0) if row.get("Impl_LUT", "-") != "-" else None
                wns = float(row.get("WNS_ns", 0) or 0) if row.get("WNS_ns", "-") != "-" else None
                fmax = float(row.get("Fmax_MHz", 0) or 0) if row.get("Fmax_MHz", "-") != "-" else None

                records.append({
                    "config": row.get("Config", f"D{dim}_PE{pe}"),
                    "dim": dim,
                    "pe": pe,
                    "status": status,
                    "tp_mfeat": tp_est,
                    "sim_tp_mfeat": sim_tp,
                    "impl_lut": impl_lut,
                    "wns_ns": wns,
                    "fmax_mhz": fmax
                })
            except (ValueError, KeyError):
                continue
                
    return records


# ==============================================================================
# Plot 1: 3D Surface & Measured Scatter Landscape
# ==============================================================================
def plot_3d_surface(records, out_path, dpi=300):
    """
    Render 3D surface plot of throughput as a function of log2(Dimension) and PE count.
    """
    fig = plt.figure(figsize=(11, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(THEME["bg_primary"])

    dims = np.array([r["dim"] for r in records])
    pes = np.array([r["pe"] for r in records])
    tps = np.array([r["tp_mfeat"] for r in records])

    # Transform dimensions to log2 space for uniform visual spacing (2, 16, 64 -> 1, 4, 6)
    log_dims = np.log2(dims)
    
    # Dense mesh for interpolation
    grid_log_d = np.linspace(log_dims.min(), log_dims.max(), 50)
    grid_pe = np.linspace(pes.min(), pes.max(), 50)
    mesh_log_d, mesh_pe = np.meshgrid(grid_log_d, grid_pe)

    # Grid interpolation (cubic or linear fallback)
    mesh_tp = griddata((log_dims, pes), tps, (mesh_log_d, mesh_pe), method="cubic")
    if np.isnan(mesh_tp).any():
        mesh_tp_linear = griddata((log_dims, pes), tps, (mesh_log_d, mesh_pe), method="linear")
        mesh_tp = np.where(np.isnan(mesh_tp), mesh_tp_linear, mesh_tp)

    # Plot interpolated surface
    surf = ax.plot_surface(
        mesh_log_d, mesh_pe, mesh_tp,
        cmap=PASTEL_CMAP,
        alpha=0.82,
        antialiased=True,
        rstride=1, cstride=1,
        edgecolor=THEME["border"],
        linewidth=0.15,
        shade=True
    )

    # Wireframe overlay for structural clarity
    ax.plot_wireframe(
        mesh_log_d, mesh_pe, mesh_tp,
        color=THEME["accent_purple"],
        alpha=0.15,
        rstride=4, cstride=4,
        linewidth=0.6
    )

    # Scatter actual hardware bitstream data points
    success_mask = np.array([r["status"] == "BITSTREAM_SUCCESS" for r in records])
    ax.scatter(
        log_dims[success_mask], pes[success_mask], tps[success_mask],
        color=THEME["accent_green"],
        edgecolor=THEME["bg_primary"],
        s=65,
        alpha=1.0,
        depthshade=False,
        label="Bitstream Verified (HW)"
    )

    # Highlight peak design point
    best_idx = np.argmax(tps[success_mask])
    best_r = np.array(records)[success_mask][best_idx]
    ax.text(
        np.log2(best_r["dim"]), best_r["pe"], best_r["tp_mfeat"] + 250,
        f"★ Peak: {best_r['tp_mfeat']:.0f} Mfeat/s\n(D={best_r['dim']}, PE={best_r['pe']})",
        color=THEME["accent_green"],
        fontsize=9,
        fontweight="bold",
        ha="center"
    )

    # Axis formatting
    ax.set_xticks(np.log2([2, 16, 64]))
    ax.set_xticklabels(["2", "16", "64"])
    ax.set_yticks(np.arange(pes.min(), pes.max() + 1, 1))
    
    ax.set_xlabel("\nDimension (D)", color=THEME["text_secondary"], labelpad=8)
    ax.set_ylabel("\nProcessing Elements (PE)", color=THEME["text_secondary"], labelpad=8)
    ax.set_zlabel("\nThroughput (Mfeat/s)", color=THEME["text_secondary"], labelpad=10)

    # 3D Pane and Grid styling
    for pane in [ax.xaxis.pane, ax.yaxis.pane, ax.zaxis.pane]:
        pane.set_facecolor(THEME["bg_secondary"])
        pane.set_edgecolor(THEME["border"])
        pane.set_alpha(0.7)

    # Colorbar
    cbar = fig.colorbar(surf, ax=ax, shrink=0.55, aspect=14, pad=0.08)
    cbar.set_label("Throughput (Mfeat/s)", color=THEME["text_secondary"], size=10)
    cbar.ax.tick_params(labelsize=8, colors=THEME["text_muted"])
    cbar.outline.set_edgecolor(THEME["border"])

    ax.set_title("CHIP-KNN DESIGN SPACE: 3D THROUGHPUT SURFACE\n", pad=20)
    ax.view_init(elev=26, azim=-128)
    ax.legend(loc="upper left", facecolor=THEME["bg_secondary"], edgecolor=THEME["border"], fontsize=8)

    plt.subplots_adjust(left=0.05, right=0.92, top=0.92, bottom=0.08)
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[plot_throughput_surface] Saved 3D surface plot to {out_path}")


# ==============================================================================
# Plot 2: 2D Heatmap Matrix with Iso-Throughput Contours
# ==============================================================================
def plot_2d_heatmap(records, out_path, dpi=300):
    """
    Render 2D heatmap matrix showing throughput per (D, PE) cell with numerical values.
    """
    unique_dims = sorted(list(set(r["dim"] for r in records)))
    unique_pes = sorted(list(set(r["pe"] for r in records)))

    grid = np.full((len(unique_pes), len(unique_dims)), np.nan)
    status_grid = {}

    for r in records:
        d_idx = unique_dims.index(r["dim"])
        p_idx = unique_pes.index(r["pe"])
        grid[p_idx, d_idx] = r["tp_mfeat"]
        status_grid[(p_idx, d_idx)] = r["status"]

    fig, ax = plt.subplots(figsize=(8, 7))

    # Heatmap imshow
    im = ax.imshow(
        grid,
        cmap=PASTEL_CMAP,
        aspect="auto",
        origin="lower",
        interpolation="nearest"
    )

    # Iso-throughput contours
    valid_mask = ~np.isnan(grid)
    if np.sum(valid_mask) > 4:
        X, Y = np.meshgrid(np.arange(len(unique_dims)), np.arange(len(unique_pes)))
        contours = ax.contour(
            X, Y, grid,
            levels=5,
            colors=THEME["text_muted"],
            linewidths=0.8,
            alpha=0.6
        )
        ax.clabel(contours, inline=True, fontsize=8, fmt="%.0f")

    # Annotate cells with values and status
    for p_idx in range(len(unique_pes)):
        for d_idx in range(len(unique_dims)):
            val = grid[p_idx, d_idx]
            if not np.isnan(val):
                status = status_grid.get((p_idx, d_idx), "")
                badge = "★ " if val == np.nanmax(grid) else ""
                text_col = THEME["bg_primary"] if val > np.nanmax(grid) * 0.7 else THEME["text_primary"]
                ax.text(
                    d_idx, p_idx,
                    f"{badge}{val:,.0f}\nMfeat/s",
                    ha="center", va="center",
                    color=text_col,
                    fontsize=9,
                    fontweight="bold"
                )

    ax.set_xticks(range(len(unique_dims)))
    ax.set_xticklabels([f"D={d}" for d in unique_dims])
    ax.set_yticks(range(len(unique_pes)))
    ax.set_yticklabels([f"PE={p}" for p in unique_pes])

    ax.set_xlabel("Feature Dimension (D)")
    ax.set_ylabel("Processing Elements (PE)")
    ax.set_title("THROUGHPUT DESIGN SPACE MATRIX (Mfeat/s)")

    cbar = fig.colorbar(im, ax=ax, shrink=0.8, aspect=15)
    cbar.set_label("Throughput (Mfeat/s)", color=THEME["text_secondary"])
    cbar.ax.tick_params(colors=THEME["text_muted"])
    cbar.outline.set_edgecolor(THEME["border"])

    plt.subplots_adjust(left=0.05, right=0.92, top=0.92, bottom=0.08)
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[plot_throughput_surface] Saved 2D heatmap to {out_path}")


# ==============================================================================
# Plot 3: Throughput Scaling Curves per Dimension
# ==============================================================================
def plot_scaling_curves(records, out_path, dpi=300):
    """
    Render 1D throughput scaling profiles vs PE count for each dimension.
    """
    fig, ax = plt.subplots(figsize=(9, 6))

    dim_colors = {
        2: THEME["accent_red"],       # Red / Coral (dense)
        16: THEME["accent_purple"],   # Lavender (sweet spot)
        64: THEME["accent_cyan"]      # Sky blue (deep)
    }

    unique_dims = sorted(list(set(r["dim"] for r in records)))
    for d in unique_dims:
        sub = [r for r in records if r["dim"] == d]
        sub = sorted(sub, key=lambda x: x["pe"])
        pes = [r["pe"] for r in sub]
        tps = [r["tp_mfeat"] for r in sub]
        col = dim_colors.get(d, THEME["accent_blue"])

        # Plot curve
        ax.plot(
            pes, tps,
            color=col,
            marker="o",
            markersize=7,
            linewidth=2.2,
            label=f"Dimension D={d}"
        )

        # Highlight endpoints
        max_r = sub[-1]
        ax.annotate(
            f"{max_r['tp_mfeat']:,.0f} Mf/s (PE={max_r['pe']})",
            xy=(max_r["pe"], max_r["tp_mfeat"]),
            xytext=(10, -5 if d == 2 else 5),
            textcoords="offset points",
            color=col,
            fontsize=8.5,
            fontweight="bold"
        )

    # Physical saturation boundary note for D=2
    d2_max = max((r for r in records if r["dim"] == 2), key=lambda x: x["pe"])
    ax.scatter(
        [d2_max["pe"]], [d2_max["tp_mfeat"]],
        s=140, facecolors="none", edgecolors=THEME["accent_yellow"], linewidths=1.8,
        label="D=2 Saturation Ceiling (80.4% LUT)"
    )

    ax.set_xlabel("Processing Elements (PE)")
    ax.set_ylabel("Peak Feature Throughput (Million features/s)")
    ax.set_title("KNN FEATURE THROUGHPUT SCALING ON ULTRA96-V2")
    ax.set_xticks(range(1, max(r["pe"] for r in records) + 1))
    
    ax.legend(facecolor=THEME["bg_secondary"], edgecolor=THEME["border"], loc="upper left")
    plt.subplots_adjust(left=0.05, right=0.92, top=0.92, bottom=0.08)
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[plot_throughput_surface] Saved scaling curves to {out_path}")


# ==============================================================================
# Plot 4: Architectural Logic Efficiency (Mfeat/s per kLUT)
# ==============================================================================
def plot_logic_efficiency(records, out_path, dpi=300):
    """
    Analyze logic efficiency: Million features/sec delivered per 1,000 routed CLB LUTs.
    """
    valid = [r for r in records if r["impl_lut"] and r["impl_lut"] > 0]
    if not valid:
        print("[plot_throughput_surface] No implementation LUT data found; skipping efficiency plot.")
        return

    fig, ax = plt.subplots(figsize=(9, 6))

    dim_colors = {
        2: THEME["accent_red"],
        16: THEME["accent_purple"],
        64: THEME["accent_cyan"]
    }

    unique_dims = sorted(list(set(r["dim"] for r in valid)))
    for d in unique_dims:
        sub = sorted([r for r in valid if r["dim"] == d], key=lambda x: x["pe"])
        pes = [r["pe"] for r in sub]
        # Efficiency = Throughput / (Impl_LUT / 1000)
        eff = [r["tp_mfeat"] / (r["impl_lut"] / 1000.0) for r in sub]
        col = dim_colors.get(d, THEME["accent_blue"])

        ax.plot(
            pes, eff,
            color=col,
            marker="s",
            markersize=6,
            linewidth=2.0,
            label=f"D={d}"
        )

    ax.set_xlabel("Processing Elements (PE)")
    ax.set_ylabel("Efficiency (Mfeat/s per 1,000 Routed LUTs)")
    ax.set_title("ARCHITECTURAL LOGIC EFFICIENCY (THROUGHPUT / kLUT)")
    ax.set_xticks(range(1, max(r["pe"] for r in valid) + 1))
    ax.legend(facecolor=THEME["bg_secondary"], edgecolor=THEME["border"], loc="upper left")

    plt.subplots_adjust(left=0.05, right=0.92, top=0.92, bottom=0.08)
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[plot_throughput_surface] Saved logic efficiency plot to {out_path}")


# ==============================================================================
# Plot 5: Comprehensive 4-Panel Dashboard
# ==============================================================================
def plot_dashboard(records, out_path, dpi=300):
    """
    Create a unified multi-panel dashboard combining 3D surface, 2D matrix,
    scaling profiles, and hardware resource utilization.
    """
    fig = plt.figure(figsize=(18, 12))
    
    # 1. 3D Surface Panel (Top-Left)
    ax1 = fig.add_subplot(221, projection="3d")
    ax1.set_facecolor(THEME["bg_primary"])
    dims = np.array([r["dim"] for r in records])
    pes = np.array([r["pe"] for r in records])
    tps = np.array([r["tp_mfeat"] for r in records])
    log_dims = np.log2(dims)

    grid_log_d = np.linspace(log_dims.min(), log_dims.max(), 35)
    grid_pe = np.linspace(pes.min(), pes.max(), 35)
    m_log_d, m_pe = np.meshgrid(grid_log_d, grid_pe)
    m_tp = griddata((log_dims, pes), tps, (m_log_d, m_pe), method="linear")

    surf = ax1.plot_surface(
        m_log_d, m_pe, m_tp,
        cmap=PASTEL_CMAP,
        alpha=0.85,
        rstride=1, cstride=1,
        edgecolor=THEME["border"],
        linewidth=0.1
    )
    ax1.scatter(log_dims, pes, tps, color=THEME["accent_green"], s=35, depthshade=False)
    ax1.set_xticks(np.log2([2, 16, 64]))
    ax1.set_xticklabels(["2", "16", "64"])
    ax1.set_xlabel("D", labelpad=5)
    ax1.set_ylabel("PE", labelpad=5)
    ax1.set_zlabel("Mfeat/s", labelpad=5)
    ax1.set_title("A. 3D Throughput Landscape", pad=12)
    ax1.view_init(elev=24, azim=-125)

    # 2. 2D Heatmap Matrix (Top-Right)
    ax2 = fig.add_subplot(222)
    unique_dims = sorted(list(set(r["dim"] for r in records)))
    unique_pes = sorted(list(set(r["pe"] for r in records)))
    mat = np.full((len(unique_pes), len(unique_dims)), np.nan)
    for r in records:
        mat[unique_pes.index(r["pe"]), unique_dims.index(r["dim"])] = r["tp_mfeat"]
    im = ax2.imshow(mat, cmap=PASTEL_CMAP, origin="lower", aspect="auto")
    for p_idx in range(len(unique_pes)):
        for d_idx in range(len(unique_dims)):
            val = mat[p_idx, d_idx]
            if not np.isnan(val):
                ax2.text(d_idx, p_idx, f"{val:,.0f}", ha="center", va="center", fontsize=8.5,
                         color=THEME["bg_primary"] if val > np.nanmax(mat)*0.7 else THEME["text_primary"],
                         fontweight="bold")
    ax2.set_xticks(range(len(unique_dims)))
    ax2.set_xticklabels([f"D={d}" for d in unique_dims])
    ax2.set_yticks(range(len(unique_pes)))
    ax2.set_yticklabels([f"PE={p}" for p in unique_pes])
    ax2.set_xlabel("Dimension (D)")
    ax2.set_ylabel("Processing Elements (PE)")
    ax2.set_title("B. Throughput Design Space Matrix (Mfeat/s)")

    # 3. Scaling Profiles (Bottom-Left)
    ax3 = fig.add_subplot(223)
    dim_colors = {2: THEME["accent_red"], 16: THEME["accent_purple"], 64: THEME["accent_cyan"]}
    for d in unique_dims:
        sub = sorted([r for r in records if r["dim"] == d], key=lambda x: x["pe"])
        ax3.plot([r["pe"] for r in sub], [r["tp_mfeat"] for r in sub],
                 marker="o", color=dim_colors.get(d, THEME["accent_blue"]), linewidth=2, label=f"D={d}")
    ax3.set_xlabel("Processing Elements (PE)")
    ax3.set_ylabel("Throughput (Mfeat/s)")
    ax3.set_title("C. Throughput Scaling per Dimension")
    ax3.legend(facecolor=THEME["bg_secondary"], edgecolor=THEME["border"])

    # 4. Routed LUT Utilization vs PE (Bottom-Right)
    ax4 = fig.add_subplot(224)
    for d in unique_dims:
        sub = sorted([r for r in records if r["dim"] == d and r["impl_lut"]], key=lambda x: x["pe"])
        if sub:
            luts_pct = [(r["impl_lut"] / 70560.0) * 100.0 for r in sub]
            ax4.plot([r["pe"] for r in sub], luts_pct,
                     marker="s", color=dim_colors.get(d, THEME["accent_blue"]), linewidth=2, label=f"D={d}")
    ax4.axhline(80.0, color=THEME["accent_yellow"], linestyle="--", linewidth=1.2, label="80% Congestion Warning")
    ax4.set_xlabel("Processing Elements (PE)")
    ax4.set_ylabel("Routed CLB LUT Utilization (%)")
    ax4.set_title("D. Physical Resource Footprint (Ultra96-V2)")
    ax4.legend(facecolor=THEME["bg_secondary"], edgecolor=THEME["border"])

    fig.suptitle("CHIP-KNN DESIGN SPACE EXPLORATION DASHBOARD (ULTRA96-V2)", y=0.98, fontsize=16)
    plt.subplots_adjust(top=0.92, bottom=0.08, left=0.06, right=0.96, hspace=0.28, wspace=0.25)
    plt.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close()
    print(f"[plot_throughput_surface] Saved dashboard to {out_path}")


# ==============================================================================
# CLI Entry Point
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(description="Generate dark-mode pastel throughput plots for CHIP-KNN design space.")
    parser.add_argument("--csv", default="sweeps/sweep_summary.csv", help="Path to sweep_summary.csv")
    parser.add_argument("--out-dir", default="plots", help="Directory where generated figures are saved")
    parser.add_argument("--dpi", type=int, default=300, help="Output image DPI resolution")
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    apply_theme()

    records = load_sweep_data(args.csv)
    if not records:
        print(f"[plot_throughput_surface] Error: No valid data found in {args.csv}")
        sys.exit(1)

    print(f"[plot_throughput_surface] Loaded {len(records)} design configurations from {args.csv}")

    # Generate all representations
    plot_3d_surface(records, os.path.join(args.out_dir, "throughput_3d_surface.png"), dpi=args.dpi)
    plot_2d_heatmap(records, os.path.join(args.out_dir, "throughput_heatmap_matrix.png"), dpi=args.dpi)
    plot_scaling_curves(records, os.path.join(args.out_dir, "throughput_scaling_curves.png"), dpi=args.dpi)
    plot_logic_efficiency(records, os.path.join(args.out_dir, "throughput_logic_efficiency.png"), dpi=args.dpi)
    plot_dashboard(records, os.path.join(args.out_dir, "throughput_dashboard.png"), dpi=args.dpi)

    print(f"\n[plot_throughput_surface] All plots generated in '{args.out_dir}/'")

if __name__ == "__main__":
    main()
