"""
Script to analyze leakage current stabilization after voltage ramp-up.
Processes all CV files together and plots mean ± spread for each voltage step.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import sys
from typing import Dict, List, Tuple, Optional
import re

# Import plot styles from config
sys.path.append(str(Path(__file__).parent.parent / "particulars-analysis"))
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
    "axes.font.size": 9,
    "axes.textonaxis.size": 6.5,
    "axes.textbox.size": 8,
    "axes.border.width": 1,
    "axes.tick.major.label.size": 8,
    "axes.tick.major.size": 4,
    "axes.tick.major.width": 1,
    "axes.tick.minor.size": 2,
    "axes.tick.minor.width": 1,
    "marker.size": 4,
    "line.width": 1,
    "legend.size": 3,
}

# Apply RC_PLOT_STYLE globally
plt.rcParams.update(RC_PLOT_STYLE)

# ===================================================================================================
# Configuration
# ===================================================================================================

# Directory containing ramping recording CSV files
RECORDINGS_DIR = Path("Ramping_Recordings")

# Voltage step definitions (in order they appear in the data)
# CV: ramps from -25 to -900 (forward)
CV_VOLTAGE_STEPS = [-25, -50, -75, -100, -125, -150, -175, -200, -225, -250, -275, -300,
                    -325, -350, -375, -400, -425, -450, -475, -500, -525, -550, -575, -600,
                    -625, -650, -675, -700, -725, -750, -775, -800, -825, -850, -875, -900]

# Tolerance for voltage matching (V)
VOLTAGE_TOLERANCE = 2.0

# Time range for plots (seconds)
PLOT_TIME_MAX = 15.0

# Minimum number of 0V rows required for ramp-down analysis
MIN_ZERO_VOLTAGE_ROWS = 10

# Output file path (optional - set to None to not save)
OUTPUT_FILE = None  # Set to a path like "leakage_current_stabilization.png" to save the figure

# ===================================================================================================
# Helper Functions
# ===================================================================================================

def extract_sensor_name(filename: str) -> Optional[str]:
    """
    Extract sensor name from filename.
    Example: "100264_SR_UR1_2e15_500min_CV_ramping_recording.csv" -> "100264_SR_UR1_2e15"
    
    Args:
        filename: CSV filename
        
    Returns:
        Sensor name string or None if pattern doesn't match
    """
    # Pattern: sensor_id_fluence_annealing_measurement_type_ramping_recording.csv
    # We want: sensor_id_fluence (e.g., "100264_SR_UR1_2e15")
    match = re.match(r"^([^_]+_[^_]+_[^_]+_[^_]+)", filename)
    if match:
        return match.group(1)
    return None


def get_measurement_type(filename: str) -> Optional[str]:
    """
    Determine if file is CV or TCT measurement.
    
    Args:
        filename: CSV filename
        
    Returns:
        "CV" or "TCT" or None if cannot determine
    """
    filename_upper = filename.upper()
    if "_CV_" in filename_upper:
        return "CV"
    elif "_TCT_" in filename_upper:
        return "TCT"
    return None


def round_voltage(voltage: np.ndarray) -> np.ndarray:
    """
    Round voltage values to 0 decimals.
    
    Args:
        voltage: Array of voltage values
        
    Returns:
        Array of rounded voltage values
    """
    return np.round(voltage, decimals=0)


def find_first_900_index(voltage: np.ndarray, tolerance: float = 2.0) -> Optional[int]:
    """
    Find the index where voltage first reaches -900 (within tolerance).
    This is the boundary point: before this for CV, after this for TCT.
    
    Args:
        voltage: Array of absolute voltage values
        tolerance: Tolerance for matching voltage (V)
        
    Returns:
        Index where -900 first appears, or None if not found
    """
    abs_voltage = np.abs(voltage)
    target_abs = 900.0
    
    for i, v in enumerate(abs_voltage):
        if abs(v - target_abs) <= tolerance:
            return i
    
    return None


def find_zero_voltage_stabilization(voltage: np.ndarray, time: np.ndarray,
                                     after_900_idx: int,
                                     min_rows: int = 10) -> Optional[Tuple[int, int]]:
    """
    Find the 0V stabilization period after ramping down from -900V.
    Only includes data AFTER voltage has reached 0V (not during ramp down).
    
    Args:
        voltage: Array of rounded absolute voltage values
        time: Array of time values
        after_900_idx: Index after -900V (start searching from here)
        min_rows: Minimum number of consecutive 0V rows required
        
    Returns:
        Tuple of (start_idx, end_idx) for 0V stabilization period, or None if not found
    """
    # Round voltage to 0 decimals
    voltage_rounded = round_voltage(voltage)
    
    # Find where voltage first reaches 0V after -900V
    zero_start_idx = None
    for i in range(after_900_idx, len(voltage_rounded)):
        if voltage_rounded[i] == 0.0:
            zero_start_idx = i
            break
    
    if zero_start_idx is None:
        return None
    
    # Find consecutive 0V values
    zero_end_idx = zero_start_idx
    consecutive_zeros = 0
    
    for i in range(zero_start_idx, len(voltage_rounded)):
        if voltage_rounded[i] == 0.0:
            consecutive_zeros += 1
            zero_end_idx = i
        else:
            # If we've found enough zeros, stop here
            if consecutive_zeros >= min_rows:
                break
            # Otherwise, reset and continue searching
            consecutive_zeros = 0
            zero_start_idx = None
    
    # Check if we found enough consecutive zeros
    if consecutive_zeros < min_rows:
        return None
    
    return zero_start_idx, zero_end_idx


def find_voltage_step_indices(voltage: np.ndarray, target_voltage: float, 
                               tolerance: float = 2.0, 
                               start_index: int = 0,
                               end_index: Optional[int] = None,
                               reverse_direction: bool = False) -> Tuple[Optional[int], Optional[int]]:
    """
    Find start and end indices for a voltage step within a specified range.
    Start: first point where voltage reaches target (within tolerance)
    End: last point before voltage changes to next step.
    
    Args:
        voltage: Array of absolute voltage values (should be rounded)
        target_voltage: Target voltage step (absolute value)
        tolerance: Tolerance for matching voltage (V)
        start_index: Start searching from this index
        end_index: Stop searching at this index (None = end of array)
        reverse_direction: If True, search backwards from end_index
        
    Returns:
        Tuple of (start_index, end_index) or (None, None) if not found
    """
    if end_index is None:
        end_index = len(voltage)
    
    # Round voltage to 0 decimals
    abs_voltage = round_voltage(np.abs(voltage))
    target_abs = round_voltage(np.array([abs(target_voltage)]))[0]
    
    if reverse_direction:
        # For TCT: search backwards from end_index
        # Find where voltage first reaches target going backwards
        start_idx = None
        for i in range(end_index - 1, start_index - 1, -1):
            if abs_voltage[i] == target_abs:
                start_idx = i
                break
        
        if start_idx is None:
            return None, None
        
        # Find where voltage leaves this step (going backwards, so look for previous point)
        end_idx = start_idx
        for i in range(start_idx - 1, start_index - 1, -1):
            v = abs_voltage[i]
            # Check if voltage is still at target
            if v == target_abs:
                end_idx = i
            else:
                # Voltage has changed - end is the next point (forward from this)
                break
        
        # Swap start and end for reverse direction (start should be earlier in time)
        if end_idx < start_idx:
            start_idx, end_idx = end_idx, start_idx
            
    else:
        # For CV: search forwards from start_index
        # Find where voltage first reaches target
        start_idx = None
        for i in range(start_index, end_index):
            if abs_voltage[i] == target_abs:
                start_idx = i
                break
        
        if start_idx is None:
            return None, None
        
        # Find where voltage leaves this step (changes significantly)
        end_idx = start_idx
        for i in range(start_idx + 1, end_index):
            v = abs_voltage[i]
            # Check if voltage is still at target
            if v == target_abs:
                end_idx = i
            else:
                # Voltage has changed - end is the previous point
                break
    
    return start_idx, end_idx


def extract_step_data(time: np.ndarray, voltage: np.ndarray, current: np.ndarray,
                      target_voltage: float, tolerance: float = 2.0,
                      start_index: int = 0,
                      end_index: Optional[int] = None,
                      reverse_direction: bool = False) -> Optional[Dict[str, np.ndarray]]:
    """
    Extract data for a specific voltage step.
    
    Args:
        time: Time array
        voltage: Voltage array (will be rounded)
        current: Current array
        target_voltage: Target voltage step
        tolerance: Tolerance for voltage matching
        start_index: Start searching from this index
        end_index: Stop searching at this index
        reverse_direction: If True, search backwards (for TCT)
        
    Returns:
        Dictionary with "time", "current" (normalized to start at 0) or None if step not found
    """
    start_idx, end_idx = find_voltage_step_indices(
        voltage, target_voltage, tolerance, start_index, end_index, reverse_direction
    )
    
    if start_idx is None or end_idx is None:
        return None
    
    # Extract data for this step
    step_time = time[start_idx:end_idx + 1]
    step_current = np.abs(current[start_idx:end_idx + 1])  # Absolute current
    
    # Normalize time to start at 0
    normalized_time = step_time - step_time[0]
    
    return {
        "time": normalized_time,
        "current": step_current,
        "end_index": end_idx  # Return end index for next step search
    }


def extract_zero_voltage_data(time: np.ndarray, voltage: np.ndarray, current: np.ndarray,
                              zero_start_idx: int, zero_end_idx: int) -> Dict[str, np.ndarray]:
    """
    Extract data for 0V stabilization period.
    
    Args:
        time: Time array
        voltage: Voltage array
        current: Current array
        zero_start_idx: Start index of 0V period
        zero_end_idx: End index of 0V period
        
    Returns:
        Dictionary with "time", "current" (normalized to start at 0)
    """
    # Extract data for this period
    step_time = time[zero_start_idx:zero_end_idx + 1]
    step_current = np.abs(current[zero_start_idx:zero_end_idx + 1])  # Absolute current
    
    # Normalize time to start at 0
    normalized_time = step_time - step_time[0]
    
    return {
        "time": normalized_time,
        "current": step_current
    }


def normalize_current(current: np.ndarray) -> np.ndarray:
    """
    Normalize current to range 0-1 using min-max normalization.
    
    Args:
        current: Current array (should already be absolute values)
        
    Returns:
        Normalized current array (min -> 0, max -> 1)
    """
    if len(current) == 0:
        return current
    
    # Ensure current is absolute (safety check)
    current = np.abs(current)
    
    # Find minimum and maximum values
    min_value = np.min(current)
    max_value = np.max(current)
    
    # Normalize: (current - min) / (max - min)
    # This makes min -> 0 and max -> 1
    if abs(max_value - min_value) < 1e-10:  # Avoid division by zero
        return np.zeros_like(current)
    
    normalized = (current - min_value) / (max_value - min_value)
    
    return normalized


def interpolate_to_common_grid(step_data_list: List[Dict[str, np.ndarray]], 
                                max_time: float = 15.0) -> Tuple[np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Interpolate all step data to a common time grid and normalize current.
    Calculate mean and spread (min-max range).
    
    Args:
        step_data_list: List of dictionaries with "time" and "current" keys
        max_time: Maximum time to include (default 15.0 seconds)
        
    Returns:
        Tuple of (common_time_grid, mean_normalized_current, (spread_lower, spread_upper))
    """
    if len(step_data_list) == 0:
        raise ValueError("No data to interpolate")
    
    # Find common time range
    all_times = [data["time"] for data in step_data_list]
    min_time = 0.0  # Always start at 0
    max_time_actual = min(max_time, min(t.max() for t in all_times if len(t) > 0))
    
    # Create common time grid (use finest resolution from all datasets)
    min_dt = min(np.min(np.diff(t)) for t in all_times if len(t) > 1)
    if min_dt <= 0:
        min_dt = 0.1  # Default if calculation fails
    common_time = np.arange(min_time, max_time_actual + min_dt, min_dt)
    
    # Interpolate each dataset to common grid and normalize
    interpolated_normalized_currents = []
    for data in step_data_list:
        step_time = data["time"]
        step_current = data["current"]
        
        if len(step_time) == 0:
            continue
        
        # Interpolate (extrapolate with nearest value)
        interp_current = np.interp(common_time, step_time, step_current,
                                   left=step_current[0] if len(step_current) > 0 else 0,
                                   right=step_current[-1] if len(step_current) > 0 else 0)
        
        # Normalize current for this dataset
        normalized_current = normalize_current(interp_current)
        interpolated_normalized_currents.append(normalized_current)
    
    if len(interpolated_normalized_currents) == 0:
        raise ValueError("No valid data after interpolation")
    
    # Compute statistics
    interpolated_array = np.array(interpolated_normalized_currents)
    mean_normalized = np.mean(interpolated_array, axis=0)
    
    # Calculate spread as distance from mean to min/max
    min_normalized = np.min(interpolated_array, axis=0)
    max_normalized = np.max(interpolated_array, axis=0)
    spread_lower = mean_normalized - min_normalized  # Distance from mean to min
    spread_upper = max_normalized - mean_normalized  # Distance from mean to max
    
    return common_time, mean_normalized, (spread_lower, spread_upper)


def apply_plot_style(ax, title: str = ""):
    """
    Apply PLOT_STYLE to axes.
    
    Args:
        ax: Matplotlib axes object
        title: Optional title for the plot
    """
    # --- Labels ---
    ax.set_xlabel("Time [s]", fontsize=PLOT_STYLE["axes.font.size"], fontweight="bold")
    ax.set_ylabel("Normalised Current", fontsize=PLOT_STYLE["axes.font.size"], fontweight="bold")
    
    if title:
        ax.set_title(title, fontsize=PLOT_STYLE["axes.font.size"], fontweight="bold")
    
    # --- Axis limits ---
    ax.set_xlim(0, 5)  # Set x-axis limit to 0-5 seconds
    
    # --- Grid ---
    ax.grid(True, alpha=0.3, linestyle=":")
    
    # --- Spine properties (border width) ---
    for spine in ax.spines.values():
        spine.set_linewidth(PLOT_STYLE["axes.border.width"])
    
    # --- Tick parameters ---
    ax.tick_params(axis="x", which="major",
                  size=PLOT_STYLE["axes.tick.major.size"],
                  width=PLOT_STYLE["axes.tick.major.width"],
                  labelsize=PLOT_STYLE["axes.tick.major.label.size"])
    ax.tick_params(axis="x", which="minor",
                  size=PLOT_STYLE["axes.tick.minor.size"],
                  width=PLOT_STYLE["axes.tick.minor.width"])
    ax.tick_params(axis="y", which="major",
                  size=PLOT_STYLE["axes.tick.major.size"],
                  width=PLOT_STYLE["axes.tick.major.width"],
                  labelsize=PLOT_STYLE["axes.tick.major.label.size"])
    ax.tick_params(axis="y", which="minor",
                  size=PLOT_STYLE["axes.tick.minor.size"],
                  width=PLOT_STYLE["axes.tick.minor.width"])
    
    # --- Line properties ---
    for line in ax.get_lines():
        line.set_linewidth(PLOT_STYLE["line.width"])


# ===================================================================================================
# Main Analysis Function
# ===================================================================================================

def analyze_leakage_current_stabilization(recordings_dir: Path, output_path: Optional[Path] = None) -> None:
    """
    Analyze leakage current stabilization by processing all CV files together.
    Creates a single plot with:
    1. Ramp-up: from -25 to -900V (blue)
    2. Ramp-down: stabilization at 0V after -900V (red)
    
    Args:
        recordings_dir: Directory containing CSV files
        output_path: Optional path to save the figure
    """
    # Validate directory exists
    if not recordings_dir.exists():
        raise FileNotFoundError(f"Directory not found: {recordings_dir}")
    
    # Find all CSV files
    csv_files = list(recordings_dir.glob("*.csv"))
    if len(csv_files) == 0:
        raise ValueError(f"No CSV files found in {recordings_dir}")
    
    print(f"Found {len(csv_files)} CSV files")
    print("Processing CV files...")
    
    # Load all CV files
    all_file_data = []
    ramp_down_file_data = []  # Files with sufficient 0V data after -900V
    
    for csv_file in csv_files:
        # Skip files with "_old" in the name
        if "_old" in csv_file.name.lower():
            continue
        
        # Check if it's a CV file
        measurement_type = get_measurement_type(csv_file.name)
        if measurement_type != "CV":
            continue  # Skip non-CV files
        
        try:
            df = pd.read_csv(csv_file)
            
            # Validate columns
            required_columns = ["time", "voltage", "current"]
            if not all(col in df.columns for col in required_columns):
                print(f"Warning: Missing columns in {csv_file.name}, skipping")
                continue
            
            # Extract and convert to absolute values
            time = df["time"].values
            voltage = np.abs(df["voltage"].values)  # Absolute voltage
            current = df["current"].values  # Will convert to absolute later
            
            # Round voltage to 0 decimals
            voltage_rounded = round_voltage(voltage)
            
            # Find the -900 boundary index
            boundary_900_idx = find_first_900_index(voltage_rounded, VOLTAGE_TOLERANCE)
            if boundary_900_idx is None:
                print(f"Warning: Could not find -900V boundary in {csv_file.name}, skipping")
                continue
            
            # CV: only process data BEFORE -900 for ramp-up
            data_start_idx = 0
            data_end_idx = boundary_900_idx
            
            all_file_data.append({
                "time": time,
                "voltage": voltage_rounded,  # Use rounded voltage
                "current": current,
                "filename": csv_file.name,
                "data_start_idx": data_start_idx,
                "data_end_idx": data_end_idx
            })
            
            # Check for ramp-down data (0V stabilization after -900V)
            zero_period = find_zero_voltage_stabilization(
                voltage_rounded, time, boundary_900_idx, MIN_ZERO_VOLTAGE_ROWS
            )
            
            if zero_period is not None:
                zero_start_idx, zero_end_idx = zero_period
                ramp_down_file_data.append({
                    "time": time,
                    "voltage": voltage_rounded,
                    "current": current,
                    "filename": csv_file.name,
                    "zero_start_idx": zero_start_idx,
                    "zero_end_idx": zero_end_idx
                })
                print(f"  Found 0V stabilization in {csv_file.name}: {zero_end_idx - zero_start_idx + 1} rows")
            
        except Exception as e:
            print(f"Error loading {csv_file.name}: {e}")
            continue
    
    if len(all_file_data) == 0:
        print("No valid CV files found")
        return
    
    print(f"\nSuccessfully loaded {len(all_file_data)} CV files for ramp-up analysis")
    print(f"Found {len(ramp_down_file_data)} files with sufficient 0V data for ramp-down analysis")
    
    # Create single figure with one subplot
    fig, ax = plt.subplots(figsize=(4.5, 4), dpi=300)
    
    # ===============================================================================================
    # PLOT 1: Ramp-up analysis (from -25 to -900V) - BLUE
    # ===============================================================================================
    print("\n" + "="*70)
    print("RAMP-UP ANALYSIS (from -25 to -900V)")
    print("="*70)
    
    # Collect all voltage step data together
    all_step_data_list = []
    
    for step_idx, target_voltage in enumerate(CV_VOLTAGE_STEPS):
        # Extract step data from all files
        step_data_list = []
        valid_files = []
        
        for file_data in all_file_data:
            step_data = extract_step_data(
                file_data["time"],
                file_data["voltage"],
                file_data["current"],
                target_voltage,
                VOLTAGE_TOLERANCE,
                file_data["data_start_idx"],
                file_data["data_end_idx"],
                False  # CV is forward direction
            )
            
            if step_data is not None and len(step_data["time"]) > 0:
                step_data_list.append(step_data)
                valid_files.append(file_data["filename"])
        
        if len(step_data_list) == 0:
            print(f"  Voltage {target_voltage}V: No data found")
            continue
        
        # Interpolate to common grid and calculate statistics
        try:
            common_time, mean_current, (spread_lower, spread_upper) = interpolate_to_common_grid(
                step_data_list, max_time=PLOT_TIME_MAX
            )
        except Exception as e:
            print(f"  Voltage {target_voltage}V: Error interpolating - {e}")
            continue
        
        # Check if time range is greater than 2 seconds
        time_range = common_time.max() - common_time.min()
        if time_range <= 2.0:
            print(f"  Voltage {target_voltage}V: Time range {time_range:.2f}s <= 2s, skipping")
            continue
        
        # Store this voltage step's data for aggregation
        all_step_data_list.append({
            "time": common_time,
            "mean": mean_current,
            "spread_lower": spread_lower,
            "spread_upper": spread_upper,
            "voltage": target_voltage,
            "n_files": len(step_data_list)
        })
        
        print(f"  Voltage {target_voltage}V: {len(step_data_list)} files, "
              f"time range 0-{common_time.max():.2f}s, "
              f"current range {mean_current.min():.4f}-{mean_current.max():.4f}")
    
    if len(all_step_data_list) == 0:
        print("No valid voltage steps found for ramp-up")
    else:
        # Aggregate all voltage steps to a common time grid
        min_time = 0.0
        max_time_actual = min(PLOT_TIME_MAX, min(data["time"].max() for data in all_step_data_list))
        
        # Create common time grid
        min_dt = 0.1
        common_time_all = np.arange(min_time, max_time_actual + min_dt, min_dt)
        
        # Interpolate all voltage steps to common grid
        all_means = []
        all_spread_lowers = []
        all_spread_uppers = []
        
        for step_data in all_step_data_list:
            step_time = step_data["time"]
            step_mean = step_data["mean"]
            step_spread_lower = step_data["spread_lower"]
            step_spread_upper = step_data["spread_upper"]
            
            # Interpolate to common grid
            interp_mean = np.interp(common_time_all, step_time, step_mean,
                                   left=step_mean[0] if len(step_mean) > 0 else 0,
                                   right=step_mean[-1] if len(step_mean) > 0 else 0)
            interp_spread_lower = np.interp(common_time_all, step_time, step_spread_lower,
                                           left=step_spread_lower[0] if len(step_spread_lower) > 0 else 0,
                                           right=step_spread_lower[-1] if len(step_spread_lower) > 0 else 0)
            interp_spread_upper = np.interp(common_time_all, step_time, step_spread_upper,
                                           left=step_spread_upper[0] if len(step_spread_upper) > 0 else 0,
                                           right=step_spread_upper[-1] if len(step_spread_upper) > 0 else 0)
            
            all_means.append(interp_mean)
            all_spread_lowers.append(interp_spread_lower)
            all_spread_uppers.append(interp_spread_upper)
        
        # Calculate overall mean and spread across all voltage steps
        all_means_array = np.array(all_means)
        overall_mean = np.mean(all_means_array, axis=0)
        
        # Calculate overall spread (mean of individual spreads)
        all_spread_lowers_array = np.array(all_spread_lowers)
        all_spread_uppers_array = np.array(all_spread_uppers)
        overall_spread_lower = np.mean(all_spread_lowers_array, axis=0)
        overall_spread_upper = np.mean(all_spread_uppers_array, axis=0)
        
        # Plot overall mean with fill showing spread - BLUE
        ax.plot(common_time_all, overall_mean, color="steelblue", 
               linewidth=PLOT_STYLE["line.width"],
               label=f"Leakage Current Stabilisation after 5 V/s (from -25 V to -900 V)")
        ax.fill_between(common_time_all,
                       overall_mean - overall_spread_lower,
                       overall_mean + overall_spread_upper,
                       alpha=0.2, color="steelblue", linewidth=0)
    
    # ===============================================================================================
    # PLOT 2: Ramp-down analysis (0V stabilization after -900V) - RED
    # ===============================================================================================
    print("\n" + "="*70)
    print("RAMP-DOWN ANALYSIS (0V stabilization after -900V)")
    print("="*70)
    
    if len(ramp_down_file_data) == 0:
        print("No files with sufficient 0V data found")
    else:
        print(f"Files used for ramp-down analysis:")
        for data in ramp_down_file_data:
            print(f"  • {data['filename']}")
        
        # Extract 0V stabilization data from all files
        zero_voltage_data_list = []
        
        for file_data in ramp_down_file_data:
            zero_data = extract_zero_voltage_data(
                file_data["time"],
                file_data["voltage"],
                file_data["current"],
                file_data["zero_start_idx"],
                file_data["zero_end_idx"]
            )
            
            if zero_data is not None and len(zero_data["time"]) > 0:
                zero_voltage_data_list.append(zero_data)
                # Print individual time range for this file
                time_start = file_data["time"][file_data["zero_start_idx"]]
                time_end = file_data["time"][file_data["zero_end_idx"]]
                time_range = time_end - time_start
                num_points = file_data["zero_end_idx"] - file_data["zero_start_idx"] + 1
                print(f"    {file_data['filename']}: "
                      f"time range {time_start:.2f}s - {time_end:.2f}s "
                      f"(duration: {time_range:.2f}s, {num_points} points)")
        
        if len(zero_voltage_data_list) > 0:
            # Interpolate to common grid and calculate statistics
            try:
                common_time_zero, mean_current_zero, (spread_lower_zero, spread_upper_zero) = interpolate_to_common_grid(
                    zero_voltage_data_list, max_time=PLOT_TIME_MAX
                )
                
                # Plot mean with fill showing spread - RED
                ax.plot(common_time_zero, mean_current_zero, color="red", 
                       linewidth=PLOT_STYLE["line.width"],
                       label=f"Leakage Current Stabilisation after 10 V/s (from -900 V to 0 V)")
                ax.fill_between(common_time_zero,
                               mean_current_zero - spread_lower_zero,
                               mean_current_zero + spread_upper_zero,
                               alpha=0.2, color="red", linewidth=0)
                
                print(f"  Processed {len(zero_voltage_data_list)} files, "
                      f"time range 0-{common_time_zero.max():.2f}s, "
                      f"current range {mean_current_zero.min():.4f}-{mean_current_zero.max():.4f}")
                
            except Exception as e:
                print(f"Error processing 0V data: {e}")
    
    # Apply plot styling
    apply_plot_style(ax)
    
    # Legend
    legend = ax.legend(
        fontsize=6, markerscale=3.5/PLOT_STYLE["marker.size"], 
        loc="upper right", shadow=False,
        frameon=True, borderaxespad=1.2, 
        fancybox=True, framealpha=0.7,
        handlelength=2.4,
        labelspacing=0.5
    )
    legend.get_frame().set_linewidth(0.4)
    legend.get_frame().set_edgecolor("black")
    
    plt.tight_layout()
    
    # Save or show
    if output_path is not None:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\nPlot saved to: {output_path}")
    
    plt.show()
    
    print(f"\n{'='*70}")
    print(f"Ramp-up: Processed {len(all_file_data)} CV files, {len(all_step_data_list)} voltage steps")
    print(f"Ramp-down: Processed {len(ramp_down_file_data)} files with 0V stabilization")
    print(f"{'='*70}")


# ===================================================================================================
# Execute script
# ===================================================================================================

if __name__ == "__main__":
    try:
        analyze_leakage_current_stabilization(RECORDINGS_DIR, OUTPUT_FILE)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)