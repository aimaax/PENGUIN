"""
TCT Voltage Steps Comparison Analysis

This script compares CCE measurements for 200um diodes with GR connected and without GR connected

For each configuration, it plots the mean CCE2[a.u.] vs absolute voltage,
with ±1 standard deviation shown as a filled region.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple

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
    "marker.size": 3,
    "line.width": 1,
    "legend.size": 3,
}

# Apply RC_PLOT_STYLE
plt.rcParams.update(RC_PLOT_STYLE)

# ===================================================================================================
# Configuration
# ===================================================================================================

raw_CC_CCE = "CC"
include_uncertainty = False
plot_all = True
thicknesses = [120, 200]

TCT_corr_factor = {
    "260113": 0.9538,
    "260114": 0.9538,
    "251215": 0.8490,
    "251216": 0.8731,
    "250325": 1.0333,  # 25.03.2025
    "250326": 1.0540,  # 26.03.2025
    "250327": 1.0970,  # 27.03.2025
    "250328": 1.1165,  # 28.03.2025
    "250407": 1.0211,  # 07.04.2025
    "250408": 1.0240,  # 08.04.2025
    "250409": 1.0586,  # 09.04.2025
    "250424": 0.9700,  # 24.04.2025
    "250425": 0.9423,  # 25.04.2025
    "250428": 0.8618,  # 28.04.2025
    "250429": 0.8777,  # 29.04.2025
    "250527": 0.9926,  # 27.05.2025
    "250528": 1.0430,  # 28.05.2025 
    "250529": 1.0767,  # 29.05.2025 
    "250602": 1.0537,  # 02.06.2025 
    "260202": 0.9166
}

FULLCHARGE_CC_DICT = {
        # 120: 56,  # fC
        120: 66.33, # new
        # 200: 102,  # fC
        200: 108.99, # new
        300: 143  # fC
    }

ConvFactor = pow(10,3)/(50*pow(10,(53/20)))


# Define the base directory and folder structure
# BASE_DIR = Path("TCT_200um_GR_vs_no_GR")
BASE_DIR = Path("UIRAD_Measurements/TCT")


# Configuration definitions
CONFIGS = {
    # "GR": {
    #     "files": [
    #         "200um_UIRAD_GR_253_260113_Laser2692_1.csv",
    #         "200um_UIRAD_GR_253_260113_Laser2692_2.csv",
    #         "200um_UIRAD_GR_253_260113_Laser2692_3.csv"
    #     ],
    #     "color": "blue",
    #     "label": "GR"
    # },
    # "No GR": {
    #     "files": [
    #         "200um_UIRAD_NO_GR_253_260114_Laser2692_1.csv",
    #         "200um_UIRAD_NO_GR_253_260114_Laser2692_2.csv",
    #         "200um_UIRAD_NO_GR_253_260114_Laser2692_3.csv"
    #     ],
    #     "color": "green",
    #     "label": "No GR"
    # },
    "120um": {
        "files": [
            "120um_UIRAD_253_251216_Laser2620.csv",
            "120um_UIRAD_300141_UR1_253_260202_Laser2692.csv",
            "120um_UIRAD_300141_UR1_253_260202_Laser2692_2.csv",
            "120um_UIRAD_300141_UR2_253_260202_Laser2692.csv",
            "120um_UIRAD_300141_UR2_253_260202_Laser2692_2.csv",
        ],
        "color": "blue",
        "label": "120um unirad"
    },
    # "120_LF": {
    #     "files": [
    #         "All_Low_Fluence_Noadd/300053_LL2_1e13_253_250425_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300053_UL_1e13_253_250326_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300053_UR2_1e13_253_250407_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300055_LL1_1e14_253_250529_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/300055_UL_1e14_253_250327_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300055_UR1_1e14_253_250409_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300055_UR2_1e14_253_250429_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300057_LL1_2e14_253_250602_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/300057_UL_2e14_253_250328_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300057_UR1_2e14_253_250409_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/300057_UR2_2e14_253_250429_Laser2333_noadd.csv",
    #     ],
    #     "color": "cornflowerblue",
    #     "label": "120um LF"
    # },
    "200um": {
        "files": [
            "200um_UIRAD_253_251215_Laser2620.csv",
            "200um_UIRAD_201294_LL1_253_260202_Laser2692.csv",
            "200um_UIRAD_201294_LL1_253_260202_Laser2692_2.csv",
            "200um_UIRAD_201289_UR2_253_260202_Laser2692.csv",
            "200um_UIRAD_201289_UR2_253_260202_Laser2692_3.csv",
        ],
        "color": "green",
        "label": "200um unirad"
    },
    # "200_LF": {
    #     "files": [
    #         "All_Low_Fluence_Noadd/200123_LL1_2e14_253_250602_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/200123_UL_2e14_253_250328_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200123_UR1_2e14_253_250409_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200123_UR2_2e14_253_250429_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200142_LL2_5e13_253_250428_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200142_LR_5e13_253_250528_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/200142_UR1_5e13_253_250326_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200142_UR2_5e13_253_250408_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200154_LL1_1e14_253_250428_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200154_LL2_1e14_253_250529_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/200154_UR1_1e14_253_250327_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200154_UR2_1e14_253_250408_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200169_LL1_1e13_253_250425_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200169_LL2_1e13_253_250407_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/200169_LR_1e13_253_250528_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/200169_UL_1e13_253_250325_Laser2333_noadd.csv",
    #     ],
    #     "color": "#3CB371",
    #     "label": "200um LF"
    # },
    # "300um": {
    #     "files": [
    #         "300um_UIRAD_253_251215_Laser2620.csv",
    #         ""
    #     ],
    #     "color": "orange",
    #     "label": "300um unirad"
    # },
    # "300_LF": {
    #     "files": [
    #         "All_Low_Fluence_Noadd/100228_LL1_1e13_253_250527_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/100228_UL_1e13_253_250325_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100228_UR1_1e13_253_250407_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100228_UR2_1e13_253_250424_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100237_LR_1e14_253_250529_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/100237_UL_1e14_253_250327_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100237_UR1_1e14_253_250408_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100237_UR2_1e14_253_250428_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100332_LL2_5e13_253_250425_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100332_LR_5e13_253_250528_Laser2455_noadd.csv",
    #         "All_Low_Fluence_Noadd/100332_UR1_5e13_253_250326_Laser2333_noadd.csv",
    #         "All_Low_Fluence_Noadd/100332_UR2_5e13_253_250408_Laser2333_noadd.csv",
    #     ],
    #     "color": "#FFD700",
    #     "label": "300um LF"
    # }
}


def read_csv_data(file_path: Path) -> pd.DataFrame:
    """
    Read CSV data from a specific folder.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame containing the CSV data
    """
    # Read the CSV file
    df = pd.read_csv(file_path)

    # Find the date split by searching for splits containing "25" or "26" (year)
    splits = file_path.stem.split("_")
    date_key: str | None = None
    for split in splits:
        try: 
            float_split = float(split)
            if float_split > 10000 and "25" in split or "26" in split:
                date_key = split
                break
        except:
            continue
    if date_key is None:
        raise ValueError(f"Could not find date (containing '25' or '26') in filename: {file_path.stem}")
    
    # Convert voltage to absolute value and ensure CCE2 is numeric
    df["Voltage_Abs"] = df["Voltage"].abs()
    df["CCE2[a.u.]"] = pd.to_numeric(df["CCE2[a.u.]"], errors="coerce")
    df["CC_corr"] = df["CCE2[a.u.]"] * TCT_corr_factor[date_key] * ConvFactor
    
    return df


def load_configuration_data(config_name: str, config_info: Dict) -> pd.DataFrame:
    """
    Load and combine data from both runs of a configuration.
    
    Args:
        config_name: Name of the configuration
        config_info: Dictionary containing folder names and plotting info
        
    Returns:
        Combined DataFrame with all runs, including file identifier
    """
    all_data = []
    
    for file_name in config_info["files"]:
        # Skip empty strings
        if not file_name or not file_name.strip():
            continue
        
        file_path = BASE_DIR / file_name
        
        # Validate that the path is a file, not a directory
        if not file_path.is_file():
            print(f"Warning: Skipping {file_path} - not a valid file")
            continue
        
        print(f"Loading: {file_path}")
        
        # Read the CSV data
        df = read_csv_data(file_path)
        
        # Add file identifier for tracking individual files when plotting
        df["file_id"] = file_name
        
        all_data.append(df)
    
    # Check if we have any data
    if not all_data:
        raise ValueError(f"No valid files found for configuration: {config_name}")
    
    # Combine all runs
    combined_df = pd.concat(all_data, ignore_index=True)
    
    return combined_df

def calculate_statistics(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate mean and standard deviation for CCE2 at each voltage.
    
    Args:
        df: DataFrame containing the data
        
    Returns:
        Tuple of (voltages, means, stds)
    """
    # Group by absolute voltage and calculate statistics
    if raw_CC_CCE == "CC":
        grouped = df.groupby("Voltage_Abs")["CC_corr"].agg(["mean", "std"])
    else:
        grouped = df.groupby("Voltage_Abs")["CCE2[a.u.]"].agg(["mean", "std"])
    
    # Sort by voltage (low to high)
    grouped = grouped.sort_index()
    
    voltages = grouped.index.values
    means = grouped["mean"].values
    stds = grouped["std"].values
    # print(f"  Voltages: {voltages}")
    # print(f"  Means: {means}")
    # print(f"  Std: {stds}")
    
    # Replace NaN stds with 0 (if only one measurement at a voltage)
    stds = np.nan_to_num(stds, nan=0.0)
    
    return voltages, means, stds


def create_comparison_plot(all_data: Dict[str, pd.DataFrame]) -> None:
    """
    Create a comparison plot with mean ± 1 std for all configurations, or all raw data if plot_all is True.
    
    Args:
        all_data: Dictionary mapping config names to their DataFrames
    """
    # Create figure and axis with dpi=300
    fig, ax = plt.subplots(dpi=300)
    
    # Plot each configuration
    for config_name, df in all_data.items():
        config_info = CONFIGS[config_name]
        
        if plot_all:
            # Plot each file's data as a separate line
            if raw_CC_CCE == "CC":
                y_column = "CC_corr"
            else:
                y_column = "CCE2[a.u.]"
            
            # Group by file and plot each file's data
            for file_id, file_df in df.groupby("file_id"):
                # Sort by voltage for proper line plotting
                file_df_sorted = file_df.sort_values("Voltage_Abs")
                
                ax.plot(
                    file_df_sorted["Voltage_Abs"].values,
                    file_df_sorted[y_column].values,
                    color=config_info["color"],
                    linestyle="--",
                    marker="o",
                    markersize=4,
                    linewidth=PLOT_STYLE["line.width"],
                    alpha=1 if config_name in ("120um", "200um", "300um") else 0.7,
                    label=config_info["label"] if file_id == df["file_id"].iloc[0] else ""  # Only label first file to avoid duplicate labels
                )
        else:
            # Calculate statistics and plot mean ± std
            voltages, means, stds = calculate_statistics(df)
            
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
            
            if include_uncertainty:
                # Plot the filled region for ±1 std
                ax.fill_between(
                    voltages,
                    means - stds,
                    means + stds,
                    color=config_info["color"],
                    alpha=0.3,
                    linewidth=0
                )

    # Plot fullcharge line in horizontal line with 5% uncertainty
    for thickness in thicknesses:
        fullcharge = FULLCHARGE_CC_DICT[thickness]
        color = "blue" if thickness == 120 else "green" if thickness == 200 else "orange"
        fullcharge_upper = fullcharge * (1 + 0.05)
        fullcharge_lower = fullcharge * (1 - 0.05)
        ax.axhline(y=fullcharge, color=color, linestyle="--", linewidth=1, alpha=0.7)
        ax.fill_between([0, 900], fullcharge_lower, fullcharge_upper, color=color, alpha=0.2, linewidth=0)
    ax.set_xlim(0, 900)
    # ax.set_ylim(65, 120)
    
    # Apply PLOT_STYLE settings manually
    # Axis labels
    ax.set_xlabel("Voltage [V]", 
                  fontsize=9, 
                  fontweight="bold")
    ax.set_ylabel("CCE2 [a.u.]" if raw_CC_CCE == "raw" else "Collected Charge [fC]", 
                  fontsize=9, 
                  fontweight="bold")
    
    # Tick parameters using PLOT_STYLE
    ax.tick_params(
        axis="both", 
        which="major",
        labelsize=8,
        size=PLOT_STYLE["axes.tick.major.size"],
        width=PLOT_STYLE["axes.tick.major.width"]
    )
    ax.tick_params(
        axis="both",
        which="minor",
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
    print("TCT Voltage Steps Comparison Analysis")
    print("=" * 60)
    print()
    
    # Load data for all configurations
    all_data = {}
    
    for config_name, config_info in CONFIGS.items():
        print(f"\nLoading {config_info['label']}...")
        df = load_configuration_data(config_name, config_info)
        all_data[config_name] = df
        
        # Print summary statistics
        voltages, means, stds = calculate_statistics(df)
        print(f"  Voltage range: {voltages.min():.0f}V to {voltages.max():.0f}V")
        print(f"  Number of voltage points: {len(voltages)}")
        print(f"  CCE2 range: {means.min():.2f} to {means.max():.2f}")
        voltage_600_idx = np.where(voltages == 600)[0]
        if len(voltage_600_idx) > 0:
            mean_at_600 = means[voltage_600_idx[0]]
            std_at_600 = stds[voltage_600_idx[0]]
            print(f"  Mean at 600V: {mean_at_600:.2f} fC")
            print(f"  Std at 600V: {std_at_600:.2f} fC")
        else:
            print("  No data at 600V")
    
    print("\n" + "=" * 60)
    print("Creating comparison plot...")
    print("=" * 60)
    
    # Create the comparison plot
    fig = create_comparison_plot(all_data)
    
    # Save the figure
    output_path = BASE_DIR / "TCT_voltage_steps_comparison.png"
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"\nPlot saved to: {output_path}")
    
    # Display the plot
    plt.show()
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()