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
        voltage: Array of absolute voltage values
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
    
    abs_voltage = np.abs(voltage)
    target_abs = abs(target_voltage)
    
    if reverse_direction:
        # For TCT: search backwards from end_index
        # Find where voltage first reaches target going backwards
        start_idx = None
        for i in range(end_index - 1, start_index - 1, -1):
            if abs(abs_voltage[i] - target_abs) <= tolerance:
                start_idx = i
                break
        
        if start_idx is None:
            return None, None
        
        # Find where voltage leaves this step (going backwards, so look for previous point)
        end_idx = start_idx
        for i in range(start_idx - 1, start_index - 1, -1):
            v = abs_voltage[i]
            # Check if voltage is still at target
            if abs(v - target_abs) <= tolerance:
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
            if abs(abs_voltage[i] - target_abs) <= tolerance:
                start_idx = i
                break
        
        if start_idx is None:
            return None, None
        
        # Find where voltage leaves this step (changes significantly)
        end_idx = start_idx
        for i in range(start_idx + 1, end_index):
            v = abs_voltage[i]
            # Check if voltage is still at target
            if abs(v - target_abs) <= tolerance:
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
        voltage: Voltage array
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


def interpolate_to_common_grid(step_data_list: List[Dict[str, np.ndarray]], 
                                max_time: float = 15.0) -> Tuple[np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """
    Interpolate all step data to a common time grid.
    Calculate mean and spread (min-max range) without normalization.
    
    Args:
        step_data_list: List of dictionaries with "time" and "current" keys
        max_time: Maximum time to include (default 15.0 seconds)
        
    Returns:
        Tuple of (common_time_grid, mean_current_uA, (spread_lower, spread_upper))
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
    
    # Interpolate each dataset to common grid (convert to µA, no normalization)
    interpolated_currents = []
    for data in step_data_list:
        step_time = data["time"]
        step_current = data["current"]
        
        if len(step_time) == 0:
            continue
        
        # Interpolate (extrapolate with nearest value)
        interp_current = np.interp(common_time, step_time, step_current,
                                   left=step_current[0] if len(step_current) > 0 else 0,
                                   right=step_current[-1] if len(step_current) > 0 else 0)
        
        # Convert to µA (no normalization)
        current_uA = interp_current * 1e6
        interpolated_currents.append(current_uA)
    
    if len(interpolated_currents) == 0:
        raise ValueError("No valid data after interpolation")
    
    # Compute statistics
    interpolated_array = np.array(interpolated_currents)
    mean_current = np.mean(interpolated_array, axis=0)
    
    # Calculate spread as distance from mean to min/max
    min_current = np.min(interpolated_array, axis=0)
    max_current = np.max(interpolated_array, axis=0)
    spread_lower = mean_current - min_current  # Distance from mean to min
    spread_upper = max_current - mean_current  # Distance from mean to max
    
    return common_time, mean_current, (spread_lower, spread_upper)


# ===================================================================================================
# Main Analysis Function
# ===================================================================================================

def analyze_leakage_current_stabilization(recordings_dir: Path, output_path: Optional[Path] = None) -> None:
    """
    Analyze leakage current stabilization by processing all CV files together.
    Calculates mean and spread for each voltage step across all files.
    
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
            
            # Find the -900 boundary index
            boundary_900_idx = find_first_900_index(voltage, VOLTAGE_TOLERANCE)
            if boundary_900_idx is None:
                print(f"Warning: Could not find -900V boundary in {csv_file.name}, skipping")
                continue
            
            # CV: only process data BEFORE -900
            data_start_idx = 0
            data_end_idx = boundary_900_idx
            
            all_file_data.append({
                "time": time,
                "voltage": voltage,
                "current": current,
                "filename": csv_file.name,
                "data_start_idx": data_start_idx,
                "data_end_idx": data_end_idx
            })
            
        except Exception as e:
            print(f"Error loading {csv_file.name}: {e}")
            continue
    
    if len(all_file_data) == 0:
        print("No valid CV files found")
        return
    
    print(f"\nSuccessfully loaded {len(all_file_data)} CV files")
    print("Files used:")
    for data in all_file_data:
        print(f"  • {data['filename']}")
    
    # Process each voltage step across all files
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = plt.cm.viridis(np.linspace(0, 1, len(CV_VOLTAGE_STEPS)))
    
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
        time_range = common_time.max() - common_time.min()  # Should be just common_time.max() since min is 0
        if time_range <= 2.0:
            print(f"  Voltage {target_voltage}V: Time range {time_range:.2f}s <= 2s, skipping")
            continue
        
        # Plot mean with fill showing spread
        color = colors[step_idx]
        ax.plot(common_time, mean_current, color=color, linewidth=2,
               label=f"{abs(target_voltage)}V (n={len(step_data_list)})")
        # ax.fill_between(common_time,
        #                mean_current - spread_lower,
        #                mean_current + spread_upper,
        #                alpha=0.2, color=color)
        
        print(f"  Voltage {target_voltage}V: {len(step_data_list)} files, "
              f"time range 0-{common_time.max():.2f}s, "
              f"current range {mean_current.min():.4f}-{mean_current.max():.4f} µA")
    
    # Format plot
    ax.set_xlabel("Time [s]", fontsize=14, fontweight="bold")
    ax.set_ylabel("Current [µA]", fontsize=14, fontweight="bold")
    ax.set_title(
        f"Leakage Current Stabilization: CV Measurements\n"
        f"Mean ± Spread across {len(all_file_data)} files",
        fontsize=16, fontweight="bold"
    )
    ax.set_xlim(0, PLOT_TIME_MAX)  # Set x-axis limit to 0-15 seconds
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(fontsize=10, loc="best", framealpha=0.9, ncol=2)
    ax.tick_params(labelsize=12)
    
    # Add text box with file list
    file_list_text = "\n".join([f"  • {data['filename']}" for data in all_file_data])
    textstr = f"Files used ({len(all_file_data)}):\n{file_list_text}"
    props = dict(boxstyle="round", facecolor="wheat", alpha=0.5)
    # ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=8,
    #         verticalalignment="top", bbox=props, family="monospace")
    
    plt.tight_layout()
    
    # Save or show
    if output_path is not None:
        fig.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"\nPlot saved to: {output_path}")
    
    plt.show()
    
    print(f"\n{'='*70}")
    print(f"Processed {len(all_file_data)} CV files")
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