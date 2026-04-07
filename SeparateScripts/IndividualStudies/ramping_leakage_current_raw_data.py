"""
Script to plot ramping recording data with dual y-axes.
Plots time on x-axis, voltage on left y-axis, and current on right y-axis.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import sys

# ===================================================================================================
# Plot Style Configuration
# ===================================================================================================

# Plot style configuration matching CV_ramp_up_vs_ramp_down.py
RC_PLOT_STYLE = {
    "mathtext.default": "regular",
    "figure.figsize": (4.5, 3),
    "font.size": 8,
    "axes.labelsize": "medium",
    "axes.unicode_minus": False,
    "xtick.labelsize": "medium",
    "ytick.labelsize": "medium",
    "legend.handlelength": 1.5,
    "legend.borderpad": 0.5,
    "legend.frameon": False,
    "legend.loc": "best",
    "legend.framealpha": 0.9,
    "xtick.direction": "in",
    "xtick.major.size": 4,
    "xtick.minor.size": 1,
    "xtick.major.pad": 6,
    "xtick.top": True,
    "xtick.major.top": True,
    "xtick.major.bottom": True,
    "xtick.minor.top": True,
    "xtick.minor.bottom": True,
    "xtick.minor.visible": True,
    "ytick.direction": "in",
    "ytick.major.size": 4,
    "ytick.minor.size": 1,
    "ytick.major.pad": 6,
    "ytick.right": True,
    "ytick.major.left": True,
    "ytick.major.right": True,
    "ytick.minor.left": True,
    "ytick.minor.right": True,
    "ytick.minor.visible": True,
    "grid.alpha": 0.8,
    "grid.linestyle": ":",
    "axes.linewidth": 1,
    "savefig.transparent": False,
}

PLOT_STYLE = {
    "axes.font.size": 10,
    "axes.textonaxis.size": 6.5,
    "axes.textbox.size": 8,
    "axes.border.width": 1,
    "axes.tick.major.label.size": 9,
    "axes.tick.major.size": 4,
    "axes.tick.major.width": 1,
    "axes.tick.minor.size": 2,
    "axes.tick.minor.width": 1,
    "marker.size": 4,
    "line.width": 1,
    "legend.size": 3,
}

# Apply RC_PLOT_STYLE
plt.rcParams.update(RC_PLOT_STYLE)

# ===================================================================================================
# Configuration
# ===================================================================================================

# Path to the CSV file
CSV_FILE = Path("Ramping_Recordings/100228_LL1_1e13_53min_CV_ramping_recording.csv")

# Output file path (optional - set to None to not save)
OUTPUT_FILE = None  # Set to a path like "ramping_plot.png" to save the figure

# ===================================================================================================
# Main Script
# ===================================================================================================

def plot_ramping_recording(csv_path: Path, output_path: Path | None = None) -> None:
    """
    Read CSV file and create a dual-axis plot with time, voltage, and current.
    
    Args:
        csv_path: Path to the CSV file containing time, voltage, and current columns
        output_path: Optional path to save the figure. If None, only displays the plot.
    """
    # Validate file exists
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Read the CSV file
    print(f"Reading data from: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")
    
    # Validate required columns exist
    required_columns = ["time", "voltage", "current"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Extract data
    time = df["time"].values
    voltage = df["voltage"].values
    current = df["current"].values
    
    # Print data summary
    print(f"Data loaded: {len(df)} data points")
    print(f"Time range: {time.min():.2f} to {time.max():.2f}")
    print(f"Voltage range: {voltage.min():.4f} to {voltage.max():.4f} V")
    print(f"Current range: {current.min():.2e} to {current.max():.2e} A")
    
    # Create figure and primary axis with dpi=300
    fig, ax1 = plt.subplots(dpi=300)
    
    # Plot voltage on left y-axis
    color_voltage = "steelblue"
    ax1.set_xlabel("Time [s]", fontsize=9, fontweight="bold")
    ax1.set_ylabel("Voltage [V]", fontsize=9, fontweight="bold", color=color_voltage)
    line1 = ax1.plot(time, voltage, color=color_voltage, linewidth=PLOT_STYLE["line.width"], label="Voltage")
    ax1.tick_params(
        axis="y",
        labelcolor=color_voltage,
        labelsize=8,
        which="major",
        size=PLOT_STYLE["axes.tick.major.size"],
        width=PLOT_STYLE["axes.tick.major.width"]
    )
    ax1.tick_params(
        axis="y",
        which="minor",
        size=PLOT_STYLE["axes.tick.minor.size"],
        width=PLOT_STYLE["axes.tick.minor.width"]
    )
    ax1.tick_params(
        axis="x",
        labelsize=8,
        which="major",
        size=PLOT_STYLE["axes.tick.major.size"],
        width=PLOT_STYLE["axes.tick.major.width"]
    )
    ax1.tick_params(
        axis="x",
        which="minor",
        size=PLOT_STYLE["axes.tick.minor.size"],
        width=PLOT_STYLE["axes.tick.minor.width"]
    )
    
    # Grid with same style as CV_ramp_up_vs_ramp_down.py
    ax1.grid(True, alpha=0.8, linestyle=":", linewidth=0.3)
    
    # Create secondary axis for current
    ax2 = ax1.twinx()
    color_current = "coral"
    ax2.set_ylabel("Current [A]", fontsize=9, fontweight="bold", color=color_current)
    line2 = ax2.plot(time, current, color=color_current, linewidth=PLOT_STYLE["line.width"], label="Current")
    ax2.tick_params(
        axis="y",
        labelcolor=color_current,
        labelsize=8,
        which="major",
        size=PLOT_STYLE["axes.tick.major.size"],
        width=PLOT_STYLE["axes.tick.major.width"]
    )
    ax2.tick_params(
        axis="y",
        which="minor",
        size=PLOT_STYLE["axes.tick.minor.size"],
        width=PLOT_STYLE["axes.tick.minor.width"]
    )
    
    # Set spine (border) width using PLOT_STYLE
    for spine in ax1.spines.values():
        spine.set_linewidth(PLOT_STYLE["axes.border.width"])
    for spine in ax2.spines.values():
        spine.set_linewidth(PLOT_STYLE["axes.border.width"])
    
    
    # Add legend combining both axes with same style as CV_ramp_up_vs_ramp_down.py
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    legend = ax1.legend(
        lines,
        labels,
        fontsize=7,
        markerscale=3.5 / 3,
        frameon=True,
        loc="upper center",
        borderaxespad=1,
        fancybox=True,
        framealpha=0.7,
        handlelength=1.6
    )
    
    # Set legend frame properties
    legend.get_frame().set_linewidth(0.3)
    legend.get_frame().set_edgecolor("black")
    
    # Adjust layout
    plt.tight_layout()
    
    # Save or show the plot
    if output_path is not None:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\nPlot saved to: {output_path}")
    
    plt.show()
    
    print("\nPlotting complete!")


# ===================================================================================================
# Execute script
# ===================================================================================================

if __name__ == "__main__":
    try:
        plot_ramping_recording(CSV_FILE, OUTPUT_FILE)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)