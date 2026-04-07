import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import os
# from config import DEFAULT_DIR_DATA


# ===================================================================================================
# Define parameters for the analysis
# ===================================================================================================

# Campaigns 
# CAMPAIGNS = ["HighFluenceIrrNeutron2023", "LowFluenceIrrNeutron2025"]
CAMPAIGNS = ["LowFluenceIrrNeutron2025"]

# Thicknesses 
THICKNESSES = [100, 200, 300]

# Annealing temperatures 
ANNEALING_TEMPERATURES = [20, 30, 40, 60]

# Chosen voltage to compare pad vs total current
VOLTAGE = 400

# ===================================================================================================




# Read database from /c/Users/MaxAn/Documents/Code/CERN/Particulars_Analysis/particulars-analysis/Database/Diodes_Database.pkl
db = pd.read_pickle("C:/Users/MaxAn/Documents/Code/CERN/Particulars_Analysis/particulars-analysis/Database/Diodes_Database.pkl")

# reset the index
db = db.reset_index()

# Path to the folder containing the data
DATA_DIR = Path("C:/Users/MaxAn/Documents/Code/CERN/Particulars_Analysis/particulars-analysis/Data")

# Print all columns of the database with their types in a structured format
column_info = pd.DataFrame({
    "Column Name": db.columns,
    "Data Type": db.dtypes.values
})
print("\n" + "="*70)
print("Database Schema")
print("="*70)
print(column_info.to_string(index=False))
print("="*70)
print(f"Total columns: {len(db.columns)}")

# Mask to filter database
mask = (
    (db["campaign"].isin(CAMPAIGNS)) &
    (db["thickness"].isin(THICKNESSES)) &
    (db["annealing_temp"].isin(ANNEALING_TEMPERATURES))
)

db = db[mask].reset_index()

# Print unique annealing times per temperature per campaign in a structured format
print("\n\n" + "="*70)
print("Annealing Times by Campaign and Temperature")
print("="*70)

def sort_annealing_times(times):
    """
    Sort annealing times with 'noadd' first, then by numeric value.
    
    Args:
        times: List of annealing time values (can be strings or numbers)
        
    Returns:
        Sorted list with 'noadd' first, then ascending numeric values
    """
    noadd_items = []
    numeric_items = []
    
    for time in times:
        time_str = str(time)
        if time_str == "noadd":
            noadd_items.append(time)
        else:
            # Extract numeric value from string like "6days" or "990min"
            numeric_value = float(''.join(filter(str.isdigit, time_str)))
            numeric_items.append((numeric_value, time))
    
    # Sort numeric items by their numeric value
    numeric_items.sort(key=lambda x: x[0])
    
    # Extract just the original values (without the numeric key)
    sorted_numeric = [item[1] for item in numeric_items]
    
    # Return noadd first, then sorted numeric values
    return noadd_items + sorted_numeric

for campaign in sorted(db["campaign"].unique()):
    print(f"\n{campaign}")
    print("-" * 70)
    
    campaign_data = db[db["campaign"] == campaign]
    
    for temp in sorted(campaign_data["annealing_temp"].unique()):
        temp_data = campaign_data[campaign_data["annealing_temp"] == temp]
        unique_times = temp_data["annealing_time"].unique()
        
        # Sort with custom function (noadd first, then ascending by numeric value)
        sorted_times = sort_annealing_times(unique_times)
        
        # Format times nicely
        times_str = ", ".join([f"{t}" for t in sorted_times])
        
        print(f"  {temp}°C: {times_str}")

print("="*70)


# Annealing temperatures to compare (common or close between HighFluenceIrrNeutron2023 and LowFluenceIrrNeutron2025)

ANNEALING_TIMES_EXCLUDE = ["noadd"]

db = db[~db["annealing_time"].isin(ANNEALING_TIMES_EXCLUDE)]



# ===================================================================================================
# Compare the pad vs total current at chosen voltage
# ===================================================================================================


def extract_numeric_from_time(time_str):
    """
    Extract numeric value from annealing time string.
    
    Args:
        time_str: String like "6days" or "990min"
        
    Returns:
        Numeric value as float
    """
    return float(''.join(filter(str.isdigit, str(time_str))))


def read_iv_file_and_calculate_ratio(file_path: Path, voltage: float) -> float:
    """
    Read IV file and calculate the ratio of pad current to total current at specified voltage.
    
    Args:
        file_path: Path to the IV CSV file
        voltage: Target voltage to extract current values (absolute value)
        
    Returns:
        Ratio of absolute pad current to absolute total current, or None if data not found
    """
    try:
        # Read the IV file
        iv_data = pd.read_csv(file_path, delimiter=";")
        
        # Get absolute voltage values
        iv_data["abs_voltage"] = iv_data["real voltage (V)"].abs()
        
        # Find the row closest to the target voltage
        closest_idx = (iv_data["abs_voltage"] - voltage).abs().idxmin()
        row = iv_data.loc[closest_idx]
        
        # Get absolute current values
        pad_current = abs(row["current (A)"])
        total_current = abs(row["input current (A)"])
        
        
        # Calculate ratio (avoid division by zero)
        if total_current > 0:
            ratio = pad_current / total_current
            
            return ratio
        else:
            return None
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


# Calculate ratios for all samples
print("\n" + "="*70)
print(f"Calculating Pad/Total Current Ratios at {VOLTAGE}V")
print("="*70)

ratios_data = []

for idx, row in db.iterrows():
    # Construct file path
    file_path = os.path.join(DATA_DIR, row["file_IV"])
    
    # Calculate ratio
    ratio = read_iv_file_and_calculate_ratio(file_path, VOLTAGE)
    
    if ratio is not None:
        ratios_data.append({
            "campaign": row["campaign"],
            "annealing_temp": row["annealing_temp"],
            "annealing_time": row["annealing_time"],
            "thickness": row["thickness"],
            "ratio": ratio,
            "file": row["file_IV"]
        })

# Convert to DataFrame
ratios_df = pd.DataFrame(ratios_data)

print(f"Successfully calculated {len(ratios_df)} ratios")


# Group by temperature and annealing time to calculate statistics
grouped = ratios_df.groupby(["annealing_temp", "annealing_time"])["ratio"].agg([
    ("mean", "mean"),
    ("min", "min"),
    ("max", "max"),
    ("count", "count")
]).reset_index()

print(f"\nFound {len(grouped)} unique temperature/time combinations")


# Create sorted labels for x-axis
def create_sort_key(row):
    """
    Create a sort key for ordering by temperature first, then numeric annealing time.
    
    Args:
        row: DataFrame row with annealing_temp and annealing_time
        
    Returns:
        Tuple of (temperature, numeric_time) for sorting
    """
    temp = row["annealing_temp"]
    time_numeric = extract_numeric_from_time(row["annealing_time"])
    return (temp, time_numeric)

# Add sort key and sort
grouped["sort_key"] = grouped.apply(create_sort_key, axis=1)
grouped = grouped.sort_values("sort_key").reset_index(drop=True)

# Create x-axis labels
grouped["label"] = grouped.apply(
    lambda row: f"{int(row['annealing_temp'])}°C {row['annealing_time']}", 
    axis=1
)


# Create the plot
print("\n" + "="*70)
print("Creating Comparison Plot")
print("="*70)

fig, ax = plt.subplots(figsize=(14, 8))

# X positions
x_positions = np.arange(len(grouped))

# Plot mean values with error bars showing min/max spread
ax.errorbar(
    x_positions,
    grouped["mean"],
    yerr=[
        grouped["mean"] - grouped["min"],  # Lower error (distance to min)
        grouped["max"] - grouped["mean"]   # Upper error (distance to max)
    ],
    fmt="o",
    markersize=8,
    capsize=5,
    capthick=2,
    linewidth=2,
    color="steelblue",
    ecolor="steelblue",
    markerfacecolor="steelblue",
    markeredgecolor="darkblue",
    markeredgewidth=1.5,
    label="Mean ± (min-max spread)"
)

# Set x-axis labels
ax.set_xticks(x_positions)
ax.set_xticklabels(grouped["label"], rotation=45, ha="right", fontsize=12)
ax.tick_params(axis="y", labelsize=12)
# Labels and title
ax.set_xlabel("Annealing (Temperature & Time)", fontsize=14, fontweight="bold")
ax.set_ylabel("Pad Current / Total Current Ratio", fontsize=14, fontweight="bold")
ax.set_title(
    f"Pad vs Total Current Ratio at {VOLTAGE}V\n" +
    f"Campaign: {', '.join(CAMPAIGNS)}",
    fontsize=16,
    fontweight="bold"
)

# Add grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Add legend
ax.legend(fontsize=11, loc="best", framealpha=0.9)

# Add horizontal line at ratio = 1 for reference
ax.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, linewidth=1.5, label="Ratio = 1")

# Adjust layout
plt.tight_layout()

# Save the figure
output_path = f"pad_vs_total_current_ratio_{VOLTAGE}V.png"
# fig.savefig(output_path, dpi=300, bbox_inches="tight")
print(f"\nPlot saved to: {output_path}")

# Display summary statistics
print("\n" + "="*70)
print("Summary Statistics")
print("="*70)
summary_table = grouped[["label", "mean", "min", "max", "count"]].copy()
summary_table["mean"] = summary_table["mean"].round(3)
summary_table["min"] = summary_table["min"].round(3)
summary_table["max"] = summary_table["max"].round(3)
print(summary_table.to_string(index=False))
print("="*70)

# Show the plot
plt.show()

print("\nAnalysis complete!")

# =================================================================================================== 
# Analyze pad vs total current ratio across a range of voltages
# =================================================================================================== 
VOLTAGES_RANGE = [200, 300, 400, 500, 600]

print("\n" + "="*70)
print(f"Calculating Ratios Across Voltage Range: {VOLTAGES_RANGE}")
print("="*70)

# Dictionary to store all ratios for each (temp, time, voltage) combination
# Structure: {(temp, time): {voltage: [ratio1, ratio2, ...]}}
ratios_by_condition_voltage = {}

# Initialize the nested dictionary with all temp/time combinations
for temp in sorted(db["annealing_temp"].unique()):
    for time in sorted(db["annealing_time"].unique()):
        ratios_by_condition_voltage[(temp, time)] = {v: [] for v in VOLTAGES_RANGE}

# For each sample in the database, calculate ratios at all voltages
for idx, row in db.iterrows():
    file_path = os.path.join(DATA_DIR, row["file_IV"])
    temp = row["annealing_temp"]
    time = row["annealing_time"]
    
    # Calculate ratio for each voltage
    for voltage in VOLTAGES_RANGE:
        ratio = read_iv_file_and_calculate_ratio(file_path, voltage)
        if ratio < 0.5:
            print(file_path)
        if ratio is not None:
            ratios_by_condition_voltage[(temp, time)][voltage].append(ratio)

# Aggregate ratios across all voltages for each (temp, time) combination
# This creates a single distribution of ratios per condition by combining all voltage points
aggregated_ratios_data = []
for (temp, time), voltage_dict in ratios_by_condition_voltage.items():
    # Collect all ratios across all voltages for this condition
    all_ratios = []
    count_measurements = 0
    for voltage in VOLTAGES_RANGE:
        all_ratios.extend(voltage_dict[voltage])
        count_measurements += len(voltage_dict[voltage])
    
    # Only include if we have data
    if len(all_ratios) > 0:
        mean_ratio = np.mean(all_ratios)
        min_ratio = np.min(all_ratios)
        max_ratio = np.max(all_ratios)
        aggregated_ratios_data.append({
            "annealing_temp": temp,
            "annealing_time": time,
            "mean": mean_ratio,
            "min": min_ratio,
            "max": max_ratio,
            "count": count_measurements
        })

# Convert to DataFrame
aggregated_ratios_df = pd.DataFrame(aggregated_ratios_data)

# Sort by temperature and numeric annealing time (reuse previous sorting logic)
aggregated_ratios_df["sort_key"] = aggregated_ratios_df.apply(create_sort_key, axis=1)
aggregated_ratios_df = aggregated_ratios_df.sort_values("sort_key").reset_index(drop=True)

# Create x-axis labels
aggregated_ratios_df["label"] = aggregated_ratios_df.apply(
    lambda row: f"{int(row['annealing_temp'])}°C {row['annealing_time']}", axis=1
)

# Print statistics table
print(f"\nStatistics for {len(aggregated_ratios_df)} temperature/time combinations")
print(f"(Each combining {len(VOLTAGES_RANGE)} voltage points across all samples):")
print("-" * 90)
stats_display = aggregated_ratios_df[["label", "mean", "min", "max", "count"]].copy()
stats_display["mean"] = stats_display["mean"].round(4)
stats_display["min"] = stats_display["min"].round(4)
stats_display["max"] = stats_display["max"].round(4)
print(stats_display.to_string(index=False))
print("-" * 90)

# Create the plot with same format as single voltage analysis
print("\n" + "="*70)
print(f"Creating Voltage Range Aggregated Plot ({VOLTAGES_RANGE})")
print("="*70)

fig, ax = plt.subplots(figsize=(14, 8))

# X positions
x_positions = np.arange(len(aggregated_ratios_df))

# Plot mean values with error bars showing min/max spread
ax.errorbar(
    x_positions,
    aggregated_ratios_df["mean"],
    yerr=[
        aggregated_ratios_df["mean"] - aggregated_ratios_df["min"],  # Lower error (distance to min)
        aggregated_ratios_df["max"] - aggregated_ratios_df["mean"]   # Upper error (distance to max)
    ],
    fmt="o",
    markersize=8,
    capsize=5,
    capthick=2,
    linewidth=2,
    color="steelblue",
    ecolor="steelblue",
    markerfacecolor="steelblue",
    markeredgecolor="darkblue",
    markeredgewidth=1.5,
    label="Mean ± (min-max spread)"
)

# Set x-axis labels
ax.set_xticks(x_positions)
ax.set_xticklabels(grouped["label"], rotation=45, ha="right", fontsize=12)
ax.tick_params(axis="y", labelsize=12)

# Labels and title
ax.set_xlabel("Annealing (Temperature & Time)", fontsize=14, fontweight="bold")
ax.set_ylabel("Pad Current / Total Current Ratio", fontsize=14, fontweight="bold")
ax.set_title(
    f"Pad vs Total Current Ratio Across Voltages {VOLTAGES_RANGE}\n" +
    f"Campaign: {', '.join(CAMPAIGNS)} ",
    fontsize=16,
    fontweight="bold"
)

# Add grid
ax.grid(True, alpha=0.3, linestyle="--", axis="y")

# Add legend
ax.legend(fontsize=11, loc="best", framealpha=0.9)

# Add horizontal line at ratio = 1 for reference
ax.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, linewidth=1.5, label="Ratio = 1")

plt.tight_layout()

# Save the figure
output_path_voltage_range = f"pad_vs_total_current_ratio_voltage_range_{VOLTAGES_RANGE}.png"
fig.savefig(output_path_voltage_range, dpi=300, bbox_inches="tight")
print(f"\nPlot saved to: {output_path_voltage_range}")

plt.show()

print("\n" + "="*70)
print("Overall Statistics (All Conditions Combined)")
print("="*70)

# Calculate mean and std across all unique annealing conditions
all_condition_means = aggregated_ratios_df["mean"].values
all_condition_mins = aggregated_ratios_df["min"].values
all_condition_maxs = aggregated_ratios_df["max"].values

overall_mean = np.mean(all_condition_means)
overall_std = np.std(all_condition_means)
overall_min = np.min(all_condition_mins)
overall_max = np.max(all_condition_maxs)

print(f"Number of unique annealing conditions: {len(aggregated_ratios_df)}")
print(f"Mean of all condition means: {overall_mean:.4f}")
print(f"Std of all condition means: {overall_std:.4f}")
print(f"Overall min (across all conditions): {overall_min:.4f}")
print(f"Overall max (across all conditions): {overall_max:.4f}")
print("="*70)

print("\n" + "="*70)
print("Multi-Voltage Analysis Complete!")
print("="*70)


# ===================================================================================================
# Plot raw pad and total current data for specific sensor
# ===================================================================================================

print("\n" + "="*70)
print("Plotting Raw Current Data for Specific Sensor")
print("="*70)

# Filter for specific sensor and annealing time
SENSOR_ID = "200154_UR1"
ANNEALING_TIME = "10days"

# SENSOR_ID = "200123_LL1"
# ANNEALING_TIME = "20min"

# Find the sensor in the database
sensor_mask = (db["sensor_id"] == SENSOR_ID) & (db["annealing_time"] == ANNEALING_TIME)
sensor_data = db[sensor_mask]

if len(sensor_data) == 0:
    print(f"Warning: No data found for sensor {SENSOR_ID} with annealing time {ANNEALING_TIME}")
else:
    print(f"Found {len(sensor_data)} entry/entries for {SENSOR_ID} at {ANNEALING_TIME}")
    
    # Get the first matching entry (should typically be only one)
    sensor_row = sensor_data.iloc[0]
    
    # Construct file path
    iv_file_path = os.path.join(DATA_DIR, sensor_row["file_IV"])
    
    print(f"Reading file: {iv_file_path}")
    print(f"Campaign: {sensor_row['campaign']}")
    print(f"Thickness: {sensor_row['thickness']} µm")
    print(f"Fluence: {sensor_row['fluence']:.2e} neq/cm²")
    print(f"Annealing: {sensor_row['annealing_temp']}°C for {sensor_row['annealing_time']}")
    
    try:
        # Read the IV file
        iv_data = pd.read_csv(iv_file_path, delimiter=";")
        
        print(f"\nData loaded: {len(iv_data)} voltage points")
        
        # Extract data
        voltage = iv_data["real voltage (V)"].values
        pad_current = iv_data["current (A)"].values
        total_current = iv_data["input current (A)"].values
        
        # Take absolute values for plotting
        abs_voltage = np.abs(voltage)
        abs_pad_current = np.abs(pad_current)
        abs_total_current = np.abs(total_current)
        
        # Create the plot
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # ===============================
        # Plot 1: Both currents on same axis (log scale)
        # ===============================
        ax1.semilogy(
            abs_voltage,
            abs_pad_current,
            "o-",
            label="Pad Current",
            color="steelblue",
            markersize=8,
            linewidth=2,
            markeredgecolor="darkblue",
            markeredgewidth=1
        )
        
        ax1.semilogy(
            abs_voltage,
            abs_total_current,
            "s-",
            label="Total Current",
            color="coral",
            markersize=8,
            linewidth=2,
            markeredgecolor="darkred",
            markeredgewidth=1
        )
        
        ax1.set_xlabel("Absolute Voltage [V]", fontsize=13, fontweight="bold")
        ax1.set_ylabel("Absolute Current [A]", fontsize=13, fontweight="bold")
        ax1.set_title(
            f"Raw Current vs Voltage: {SENSOR_ID} ({ANNEALING_TIME})\n" +
            f"{sensor_row['thickness']}µm, {sensor_row['fluence']:.2e} neq/cm², " +
            f"{sensor_row['annealing_temp']}°C",
            fontsize=14,
            fontweight="bold"
        )
        ax1.grid(True, alpha=0.3, which="both", linestyle="--")
        ax1.legend(fontsize=12, loc="best", framealpha=0.9)
        ax1.tick_params(axis="both", labelsize=11)
        
        # ===============================
        # Plot 2: Ratio of pad to total current
        # ===============================
        # Calculate ratio (avoid division by zero)
        ratio = np.where(abs_total_current > 0, abs_pad_current / abs_total_current, np.nan)
        
        ax2.plot(
            abs_voltage,
            ratio,
            "o-",
            color="purple",
            markersize=8,
            linewidth=2,
            markeredgecolor="indigo",
            markeredgewidth=1,
            label="Pad/Total Ratio"
        )
        
        # Add reference line at ratio = 1
        ax2.axhline(y=1.0, color="red", linestyle="--", alpha=0.5, linewidth=2, label="Ratio = 1")
        
        ax2.set_xlabel("Absolute Voltage [V]", fontsize=13, fontweight="bold")
        ax2.set_ylabel("Pad Current / Total Current", fontsize=13, fontweight="bold")
        ax2.set_title("Current Ratio vs Voltage", fontsize=14, fontweight="bold")
        ax2.grid(True, alpha=0.3, linestyle="--")
        ax2.legend(fontsize=12, loc="best", framealpha=0.9)
        ax2.tick_params(axis="both", labelsize=11)
        
        plt.tight_layout()
        
        # Save the figure
        output_path_raw = f"raw_current_{SENSOR_ID}_{ANNEALING_TIME}.png"
        fig.savefig(output_path_raw, dpi=300, bbox_inches="tight")
        print(f"\nPlot saved to: {output_path_raw}")
        
        # Display summary statistics
        print("\n" + "="*70)
        print("Current Statistics")
        print("="*70)
        print(f"{'Voltage Range:':<30} {abs_voltage.min():.1f}V to {abs_voltage.max():.1f}V")
        print(f"{'Pad Current Range:':<30} {abs_pad_current.min():.2e}A to {abs_pad_current.max():.2e}A")
        print(f"{'Total Current Range:':<30} {abs_total_current.min():.2e}A to {abs_total_current.max():.2e}A")
        print(f"{'Mean Ratio (Pad/Total):':<30} {np.nanmean(ratio):.4f}")
        print(f"{'Ratio Range:':<30} {np.nanmin(ratio):.4f} to {np.nanmax(ratio):.4f}")
        print("="*70)
        
        plt.show()
        
    except FileNotFoundError:
        print(f"Error: File not found at {iv_file_path}")
    except Exception as e:
        print(f"Error reading file: {e}")

print("\nRaw data plotting complete!")



