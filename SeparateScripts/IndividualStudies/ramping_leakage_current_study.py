"""
Script to analyze leakage current stabilization after voltage ramp-up.
Groups files by sensor name and measurement type (CV/TCT), extracts data
for each voltage step, and plots individual files separately.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import numpy as np
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import re

# ===================================================================================================
# Configuration
# ===================================================================================================

# Directory containing ramping recording CSV files
RECORDINGS_DIR = Path("Ramping_Recordings")

# Voltage step definitions (in order they appear in the data)
# CV: ramps from -25 to -900 (forward)
CV_VOLTAGE_STEPS = [-50, -75, -100, -125, -150, -175, -200, -225, -250, -275, -300,
                    -325, -350, -375, -400, -425, -450, -475, -500, -525, -550, -575, -600,
                    -625, -650, -675, -700, -725, -750, -775, -800, -825, -850, -875]

# TCT: ramps from -900 to -100 (reverse order)
TCT_VOLTAGE_STEPS = [-800, -700, -600, -500, -400, -300, -200]

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


def interpolate_and_normalize_single_file(step_data: Dict[str, np.ndarray], 
                                         max_time: float = 15.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpolate single file step data to a common time grid and normalize current.
    
    Args:
        step_data: Dictionary with "time" and "current" keys
        max_time: Maximum time to include (default 15.0 seconds)
        
    Returns:
        Tuple of (common_time_grid, normalized_current)
    """
    step_time = step_data["time"]
    step_current = step_data["current"]
    
    if len(step_time) == 0:
        raise ValueError("No data to interpolate")
    
    # Create time grid
    min_time = 0.0
    max_time_actual = min(max_time, step_time.max())
    
    # Create common time grid
    if len(step_time) > 1:
        min_dt = np.min(np.diff(step_time))
        if min_dt <= 0:
            min_dt = 0.1
    else:
        min_dt = 0.1
    
    common_time = np.arange(min_time, max_time_actual + min_dt, min_dt)
    
    # Interpolate
    interp_current = np.interp(common_time, step_time, step_current,
                               left=step_current[0] if len(step_current) > 0 else 0,
                               right=step_current[-1] if len(step_current) > 0 else 0)
    
    # Normalize current
    normalized_current = normalize_current(interp_current)
    
    return common_time, normalized_current


def process_single_file(file_path: Path, output_path: Optional[Path] = None) -> None:
    """
    Process a single CSV file and create a plot for it.
    
    Args:
        file_path: Path to CSV file
        output_path: Optional path to save the figure
    """
    try:
        df = pd.read_csv(file_path)
        
        # Validate columns
        required_columns = ["time", "voltage", "current"]
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Missing columns in {file_path.name}, skipping")
            return
        
        # Extract sensor name and measurement type
        sensor_name = extract_sensor_name(file_path.name)
        measurement_type = get_measurement_type(file_path.name)
        
        if sensor_name is None or measurement_type is None:
            print(f"Warning: Could not parse {file_path.name}, skipping")
            return
        
        # Extract and convert to absolute values
        time = df["time"].values
        voltage = np.abs(df["voltage"].values)  # Absolute voltage
        current = df["current"].values  # Will convert to absolute later
        
        # Find the -900 boundary index
        boundary_900_idx = find_first_900_index(voltage, VOLTAGE_TOLERANCE)
        if boundary_900_idx is None:
            print(f"Warning: Could not find -900V boundary in {file_path.name}, skipping")
            return
        
        # Get voltage steps for this measurement type
        if measurement_type == "CV":
            voltage_steps = CV_VOLTAGE_STEPS
            reverse_direction = False
            # CV: only process data BEFORE -900
            data_start_idx = 0
            data_end_idx = boundary_900_idx
        else:  # TCT
            voltage_steps = TCT_VOLTAGE_STEPS
            reverse_direction = True
            # TCT: only process data AFTER -900
            data_start_idx = boundary_900_idx
            data_end_idx = len(voltage)
        
        print(f"\nProcessing: {file_path.name}")
        print(f"  Sensor: {sensor_name}, Type: {measurement_type}")
        
        # Create plot for this file
        fig, ax = plt.subplots(figsize=(14, 8))
        
        colors = plt.cm.tab20(np.linspace(0, 1, len(voltage_steps)))
        
        # Process each voltage step
        for step_idx, target_voltage in enumerate(voltage_steps):
            step_data = extract_step_data(
                time,
                voltage,
                current,
                target_voltage,
                VOLTAGE_TOLERANCE,
                data_start_idx,
                data_end_idx,
                reverse_direction
            )
            
            if step_data is None or len(step_data["time"]) == 0:
                print(f"  Voltage {target_voltage}V: No data found")
                continue
            
            try:
                common_time, normalized_current = interpolate_and_normalize_single_file(
                    step_data, max_time=PLOT_TIME_MAX
                )
            except Exception as e:
                print(f"  Voltage {target_voltage}V: Error - {e}")
                continue
            
            # Plot this voltage step
            color = colors[step_idx]
            ax.plot(common_time, normalized_current, color=color, linewidth=2,
                   label=f"{abs(target_voltage)}V", alpha=0.8)
            
            print(f"  Voltage {target_voltage}V: time range 0-{common_time.max():.2f}s, "
                  f"normalized current range {normalized_current.min():.4f}-{normalized_current.max():.4f}")
        
        # Format plot
        ax.set_xlabel("Time [s]", fontsize=14, fontweight="bold")
        ax.set_ylabel("Normalized Current", fontsize=14, fontweight="bold")
        ax.set_title(
            f"Leakage Current Stabilization: {sensor_name} ({measurement_type})\n"
            f"File: {file_path.name} (Normalized: 0-1)",
            fontsize=16, fontweight="bold"
        )
        ax.set_xlim(0, PLOT_TIME_MAX)  # Set x-axis limit to 0-15 seconds
        ax.set_ylim(0, 1.1)  # Set y-axis to 0-1 range
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend(fontsize=10, loc="best", framealpha=0.9, ncol=2)
        ax.tick_params(labelsize=12)
        
        plt.tight_layout()
        
        # Save or show
        if output_path is not None:
            # Create filename based on input file
            safe_filename = file_path.stem.replace(" ", "_").replace("/", "_")
            output_path_file = output_path.parent / f"{output_path.stem}_{safe_filename}{output_path.suffix}"
            fig.savefig(output_path_file, dpi=300, bbox_inches="tight")
            print(f"  Plot saved to: {output_path_file}")
        
        plt.show()
        
    except Exception as e:
        print(f"Error processing {file_path.name}: {e}")
        import traceback
        traceback.print_exc()


# ===================================================================================================
# Main Analysis Function
# ===================================================================================================

def analyze_leakage_current_stabilization(recordings_dir: Path, output_path: Optional[Path] = None) -> None:
    """
    Analyze leakage current stabilization by processing each file individually.
    Only processes CV files.
    
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
    print("Processing CV files individually...")
    
    # Process each file separately (only CV files)
    cv_count = 0
    for csv_file in csv_files:
        # Check if it's a CV file
        measurement_type = get_measurement_type(csv_file.name)
        if measurement_type != "CV":
            continue  # Skip non-CV files
        
        process_single_file(csv_file, output_path)
        cv_count += 1
    
    print(f"\n{'='*70}")
    print(f"Processed {cv_count} CV files (skipped {len(csv_files) - cv_count} non-CV files)")
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