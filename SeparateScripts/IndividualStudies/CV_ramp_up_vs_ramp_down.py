"""
CV Ramp Up vs Ramp Down Analysis

This script compares 1/C^2 measurements for CV ramp-up (25V to -900V) and 
ramp-down (-900V to -25V) configurations.

For each configuration, it plots the mean 1/C^2 vs absolute voltage,
with min-max spread shown as a filled region.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

# Plot style configuration
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

# Apply RC_PLOT_STYLE first
plt.rcParams.update(RC_PLOT_STYLE)

# Define the base directory and configuration
BASE_DIR = Path("CV_ramp_up_vs_ramp_down")
OPEN_CORRECTION = 5.0276597281666e-11

# Configuration definitions
CONFIGS = {
    "ramp_up": {
        "files": [
            # "200123_UR2_2e14/200123_UR2_2e14_600min_CV_0_-25_-900.csv",
            # "200123_UR2_2e14/200123_UR2_2e14_600min_CV_2_-25_-900.csv",
            # "200123_UR2_2e14/200123_UR2_2e14_600min_CV_4_-25_-900.csv"
            # "100332_LL2_5e13/100332_LL2_5e13_600min_CV_0_-25_-900.csv",
            # "100332_LL2_5e13/100332_LL2_5e13_600min_CV_2_-25_-900.csv",
            # "100332_LL2_5e13/100332_LL2_5e13_600min_CV_4_-25_-900.csv"
            "200um_UIRAD_GR/200um_UIRAD_GR_Laser2692_CV_0_-25_-900.csv",
            "200um_UIRAD_GR/200um_UIRAD_GR_Laser2692_CV_2_-25_-900.csv",
            "200um_UIRAD_GR/200um_UIRAD_GR_Laser2692_CV_4_-25_-900.csv"
        ],
        "color": "blue",
        "label": "-20V to -900V"
    },
    "ramp_down": {
        "files": [
            # "200123_UR2_2e14/200123_UR2_2e14_600min_CV_1_-900_-25.csv",
            # "200123_UR2_2e14/200123_UR2_2e14_600min_CV_3_-900_-25.csv",
            # "200123_UR2_2e14/200123_UR2_2e14_600min_CV_5_-900_-25.csv"
            # "100332_LL2_5e13/100332_LL2_5e13_600min_CV_1_-900_-25.csv",
            # "100332_LL2_5e13/100332_LL2_5e13_600min_CV_3_-900_-25.csv",
            # "100332_LL2_5e13/100332_LL2_5e13_600min_CV_5_-900_-25.csv"
            "200um_UIRAD_GR/200um_UIRAD_GR_Laser2692_CV_1_-900_-25.csv",
            "200um_UIRAD_GR/200um_UIRAD_GR_Laser2692_CV_3_-900_-25.csv",
            "200um_UIRAD_GR/200um_UIRAD_GR_Laser2692_CV_5_-900_-25.csv"
        ],
        "color": "green",
        "label": "-900V to -20V"
    }
}


def read_csv_data(file_path: Path) -> pd.DataFrame:
    """
    Read CSV data from a specific file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame containing the CSV data with processed columns
    """
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    # Read the CSV file
    df = pd.read_csv(file_path, delimiter=";")
    
    # Calculate absolute voltage
    df["voltage_abs"] = df["set voltage (V)"].abs()
    
    # Calculate 1/C^2 for corrected capacitance
    df["inv_c2"] = 1 / (abs(df["serial capacitance"]) - OPEN_CORRECTION)**2
    
    # Sort by voltage (ascending)
    df = df.sort_values("voltage_abs")
    
    return df


def load_configuration_data(config_name: str, config_info: Dict) -> pd.DataFrame:
    """
    Load and combine data from all files of a configuration.
    
    Args:
        config_name: Name of the configuration
        config_info: Dictionary containing file paths and plotting info
        
    Returns:
        Combined DataFrame with all runs
    """
    all_data = []
    
    for file_name in config_info["files"]:
        file_path = BASE_DIR / file_name
        
        print(f"Loading: {file_path}")
        
        # Read the CSV data
        df = read_csv_data(file_path)
        
        # Add configuration identifier
        df["Config"] = config_name
        
        all_data.append(df)
    
    # Combine all files
    combined_df = pd.concat(all_data, ignore_index=True)
    
    return combined_df


def calculate_statistics(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate mean, min, and max for inv_c2 at each voltage.
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        Tuple of (voltages, means, mins, maxs)
    """
    # Group by absolute voltage and calculate statistics
    grouped = df.groupby("voltage_abs")["inv_c2"].agg(["mean", "min", "max"])
    
    # Sort by voltage (low to high)
    grouped = grouped.sort_index()
    
    voltages = grouped.index.values
    means = grouped["mean"].values
    mins = grouped["min"].values
    maxs = grouped["max"].values
    
    return voltages, means, mins, maxs


def create_comparison_plot(all_data: Dict[str, pd.DataFrame]) -> None:
    """
    Create a comparison plot with mean and min-max spread for all configurations.
    
    Args:
        all_data: Dictionary mapping config names to their DataFrames
    """
    # Create figure and axis
    fig, ax = plt.subplots(dpi=300)
    
    # Plot each configuration
    for config_name, df in all_data.items():
        config_info = CONFIGS[config_name]
        
        # Calculate statistics
        voltages, means, mins, maxs = calculate_statistics(df)

        print(voltages)
        print(means)
        print(mins)
        print(maxs)
        
        # Plot the mean line
        ax.plot(
            voltages,
            means,
            marker="o",
            markersize=4,
            color=config_info["color"],
            linestyle="--",
            linewidth=PLOT_STYLE["line.width"],
            label=config_info["label"]
        )
        
        # Plot the filled region for min-max spread
        ax.fill_between(
            voltages,
            mins,
            maxs,
            color=config_info["color"],
            alpha=0.3,
            linewidth=0
        )
    
    # Apply PLOT_STYLE settings manually
    # Axis labels
    ax.set_xlabel("Voltage [V]", 
                  fontsize=9, 
                  fontweight="bold")
    ax.set_ylabel(r"$1/Capacitance^2$ [$\dfrac{1}{F^{2}}$]", 
                  fontsize=9, 
                  fontweight="bold")
    
    # Tick parameters using PLOT_STYLE
    ax.tick_params(
        axis='both', 
        which='major',
        labelsize=8,
        size=PLOT_STYLE["axes.tick.major.size"],
        width=PLOT_STYLE["axes.tick.major.width"]
    )
    ax.tick_params(
        axis='both',
        which='minor',
        size=PLOT_STYLE["axes.tick.minor.size"],
        width=PLOT_STYLE["axes.tick.minor.width"]
    )
    
    # Spine (border) width using PLOT_STYLE["axes.border.width"]
    for spine in ax.spines.values():
        spine.set_linewidth(PLOT_STYLE["axes.border.width"])
    
    # Grid
    ax.grid(True, alpha=0.8, linestyle=":", linewidth=0.3)
    
    # Legend using PLOT_STYLE["legend.size"]
    legend = ax.legend(
        fontsize=7, 
        markerscale=3.5 / 3,
        frameon=True, 
        loc="lower right",
        bbox_to_anchor=(0.99, 0.01),
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
    
    return fig


def main() -> None:
    """
    Main function to execute the analysis.
    """
    print("=" * 60)
    print("CV Ramp Up vs Ramp Down Analysis")
    print("=" * 60)
    print()
    
    # Load data for all configurations
    all_data = {}
    
    for config_name, config_info in CONFIGS.items():
        print(f"\nLoading {config_info['label']}...")
        df = load_configuration_data(config_name, config_info)
        all_data[config_name] = df
        
        # Print summary statistics
        voltages, means, mins, maxs = calculate_statistics(df)
        print(f"  Voltage range: {voltages.min():.0f}V to {voltages.max():.0f}V")
        print(f"  Number of voltage points: {len(voltages)}")
        print(f"  1/C^2 range: {means.min():.2e} to {means.max():.2e}")
    
    print("\n" + "=" * 60)
    print("Creating comparison plot...")
    print("=" * 60)
    
    # Create the comparison plot
    fig = create_comparison_plot(all_data)
    
    # Save the figure
    output_path = BASE_DIR / "UIRAD_CV_1overC2.pdf"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")
    
    # Display the plot
    plt.show()
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()