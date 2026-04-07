"""
TCT Voltage Steps Comparison Analysis

This script compares CCE measurements across different voltage step configurations:
- 100V steps (red)
- 50V steps (blue)
- Mixed 100V+50V steps (green)

For each configuration, it plots the mean CCE2[a.u.] vs absolute voltage,
with ±1 standard deviation shown as a filled region.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple

# Define the base directory and folder structure
BASE_DIR = Path("TCT_Diff_V_Steps")

# Configuration definitions
CONFIGS = {
    "100V_steps": {
        "folders": [
            "300059_SR_UR2_6e15_253_251124_Laser2620_2000min_1",
            "300059_SR_UR2_6e15_253_251124_Laser2620_2000min_2"
        ],
        "color": "red",
        "label": "100V Steps"
    },
    "50V_steps": {
        "folders": [
            "300059_SR_UR2_6e15_253_251124_Laser2620_2000min_50V_1",
            "300059_SR_UR2_6e15_253_251124_Laser2620_2000min_50V_2"
        ],
        "color": "blue",
        "label": "50V Steps"
    },
    "mixed_steps": {
        "folders": [
            "300059_SR_UR2_6e15_253_251124_Laser2620_2000min_100V_50V_1",
            "300059_SR_UR2_6e15_253_251124_Laser2620_2000min_100V_50V_2"
        ],
        "color": "green",
        "label": "Mixed 100V+50V Steps"
    }
}


def read_csv_data(folder_path: Path, csv_name: str) -> pd.DataFrame:
    """
    Read CSV data from a specific folder.
    
    Args:
        folder_path: Path to the folder containing the CSV
        csv_name: Name of the CSV file
        
    Returns:
        DataFrame containing the CSV data
    """
    csv_path = folder_path / csv_name
    
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Read the CSV file
    df = pd.read_csv(csv_path)
    
    # Convert voltage to absolute value and ensure CCE2 is numeric
    df["Voltage_Abs"] = df["Voltage"].abs()
    df["CCE2[a.u.]"] = pd.to_numeric(df["CCE2[a.u.]"], errors="coerce")
    
    return df


def load_configuration_data(config_name: str, config_info: Dict) -> pd.DataFrame:
    """
    Load and combine data from both runs of a configuration.
    
    Args:
        config_name: Name of the configuration
        config_info: Dictionary containing folder names and plotting info
        
    Returns:
        Combined DataFrame with all runs
    """
    all_data = []
    
    for folder_name in config_info["folders"]:
        folder_path = BASE_DIR / folder_name
        
        # Extract the CSV filename from folder name
        csv_name = f"{folder_name}.csv"
        
        print(f"Loading: {folder_path / csv_name}")
        
        # Read the CSV data
        df = read_csv_data(folder_path, csv_name)
        
        # Add run identifier
        run_num = "1" if folder_name.endswith("_1") else "2"
        df["Run"] = run_num
        df["Config"] = config_name
        
        all_data.append(df)
    
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
    grouped = df.groupby("Voltage_Abs")["CCE2[a.u.]"].agg(["mean", "std"])
    
    # Sort by voltage (low to high)
    grouped = grouped.sort_index()
    
    voltages = grouped.index.values
    means = grouped["mean"].values
    stds = grouped["std"].values
    
    # Replace NaN stds with 0 (if only one measurement at a voltage)
    stds = np.nan_to_num(stds, nan=0.0)
    
    return voltages, means, stds


def create_comparison_plot(all_data: Dict[str, pd.DataFrame]) -> None:
    """
    Create a comparison plot with mean ± 1 std for all configurations.
    
    Args:
        all_data: Dictionary mapping config names to their DataFrames
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot each configuration
    for config_name, df in all_data.items():
        config_info = CONFIGS[config_name]
        
        # Calculate statistics
        voltages, means, stds = calculate_statistics(df)
        
        # Plot the mean line
        ax.plot(
            voltages,
            means,
            color=config_info["color"],
            linewidth=2,
            label=config_info["label"],
            marker="o",
            markersize=6
        )
        
        # Plot the filled region for ±1 std
        ax.fill_between(
            voltages,
            means - stds,
            means + stds,
            color=config_info["color"],
            alpha=0.3
        )
    
    # Set labels and title
    ax.set_xlabel("Absolute Voltage [V]", fontsize=14, fontweight="bold")
    ax.set_ylabel("CCE2 [a.u.]", fontsize=14, fontweight="bold")
    ax.set_title(
        "TCT CCE Comparison: Different Voltage Step Configurations\n" + 
        "Mean ± 1σ",
        fontsize=16,
        fontweight="bold"
    )
    
    # Add grid
    ax.grid(True, alpha=0.3, linestyle="--")
    
    # Add legend
    ax.legend(fontsize=12, loc="best", framealpha=0.9)
    
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