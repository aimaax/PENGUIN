import numpy as np
import math
from typing import Tuple
from Utils.constants import KB, EA_EPI, EA_FZ

def read_annealing_file(filename: str, ignore_file_time: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """
    Read annealing data from a file.
    
    Args:
        filename: Path to the file to read
        ignore_file_time: If True, generate time steps based on row index (1, 2, 3, ...)
    
    Returns:
        Tuple of numpy arrays (time, temperature)
    """
    temp_data = []

    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            # Process temperature string (handle ".625" edge case)
            temp_str = parts[1]
            if temp_str.endswith(".625"):
                temp_str = temp_str[:-4] + ".0625"

            temp_data.append(float(temp_str))

    # Generate time array: 1, 2, 3, ... N (in seconds)
    time_array = np.arange(1, len(temp_data) + 1)

    temp_array = np.array(temp_data)

    return time_array, temp_array


def arrhenius_factor(temp_C: float, t_ref_C: float, ea: float) -> float:
    """
    Calculate Arrhenius scaling factor for equivalent annealing time.
    
    This returns the factor dt_eq/dt relative to the reference temperature.
    
    Parameters
    ----------
    temp_C : float
        Temperature in degrees Celsius
    t_ref_C : float
        Reference temperature in degrees Celsius
    ea : float
        Activation energy in eV
    
    Returns
    -------
    float
        Scaling factor for equivalent time
    """
    temp_K = temp_C + 273.15  # Convert to Kelvin
    t_ref_K = t_ref_C + 273.15  # Convert reference temperature to Kelvin
    return math.exp(-ea / KB * (1.0 / temp_K - 1.0 / t_ref_K))


def _calculate_equivalent_annealing_time(
    input_file: str,
    annealing_temp: float,
    ea: float
) -> float:
    """
    Helper function to calculate the equivalent annealing time for a given EA value.
    
    This function matches the calculation method from calculate_annealing_equivalent_time_HD.py.
    Returns only the equivalent annealing time (not real duration).
    
    Parameters
    ----------
    input_file : str
        Path to the temperature log file.
    annealing_temp : float
        Reference annealing temperature in °C (this is T_REF_C, typically 60°C).
    ea : float
        Activation energy in eV (use EA_EPI or EA_FZ).
    
    Returns
    -------
    eq_time : float
        Total equivalent annealing time in minutes.
    """
    # Read recorded times and temperatures from file
    times, temps = read_annealing_file(input_file, ignore_file_time=True)
    temps = np.array(temps, dtype=float)
    
    # Filter out invalid temperatures 
    valid_mask = (temps > -100) & (temps < 90) 
    times = times[valid_mask]
    temps = temps[valid_mask]
    
    if len(times) < 2:
        return 0.0
    
    # Smooth out single-point spikes (jump >50 °C)
    if len(temps) > 2:
        temp_diff = np.abs(np.diff(temps))
        spike_mask = temp_diff > 50
        if spike_mask.any():
            # Replace spikes with previous valid value
            spike_indices = np.where(spike_mask)[0] + 1
            for idx in spike_indices:
                if idx > 0:
                    temps[idx] = temps[idx - 1]
    
    # Time is in seconds (each row is one second)
    # Calculate time intervals
    dt = times[1:] - times[:-1]  # Time intervals in seconds
    
    # Calculate Arrhenius factors for each temperature segment
    # Use annealing_temp as the reference temperature (T_REF_C)
    factors = np.array([arrhenius_factor(T, annealing_temp, ea) for T in temps[:-1]])
    
    # Calculate equivalent time segments
    t_eq_segments = factors * dt  # Equivalent time in seconds
    
    # Total equivalent duration
    eq_duration_s = np.sum(t_eq_segments)  # Equivalent duration in seconds
    
    # Convert to minutes
    eq_duration_min = eq_duration_s / 60.0
    
    return eq_duration_min


def calculate_equivalent_annealing_time(
    input_file: str,
    annealing_temp: float
) -> Tuple[float, float]:
    """
    Calculate equivalent annealing time for both EPI and FZ sensor types in one run.
    
    Parameters
    ----------
    input_file : str
        Path to the temperature log file.
    annealing_temp : float
        Reference annealing temperature in °C (this is T_REF_C, typically 60°C).
    
    Returns
    -------
    eq_time_epi : float
        Equivalent annealing time for EPI sensors (EA=1.01 eV) in minutes.
    eq_time_fz : float
        Equivalent annealing time for FZ sensors (EA=1.1 eV) in minutes.
    """
    # Calculate for EPI (EA = 1.01 eV)
    eq_time_epi = _calculate_equivalent_annealing_time(
        input_file, annealing_temp, ea=EA_EPI
    )
    
    # Calculate for FZ (EA = 1.1 eV)
    eq_time_fz = _calculate_equivalent_annealing_time(
        input_file, annealing_temp, ea=EA_FZ
    )
    
    return eq_time_epi, eq_time_fz
