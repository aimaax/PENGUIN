import math
from Utils.constants import Eef, KB
import numpy as np
from config import UNCERTAINTY_THICKNESS, UNCERTAINTY_FLUENCE

def toKelvin(T):
    return 273.15 + T

def currentConvFactor(T_target = 20, T_meas = -20):
    T1 = toKelvin(T_target)
    T0 = toKelvin(T_meas)
    return (T1/T0)**2 * math.exp(-Eef/(2*KB) * (1/T1 - 1/T0))

def convert_annealing_time(annealing_time):
    if annealing_time == "noadd":
        return 0
    annealing_time = str(annealing_time).strip().lower()
    if annealing_time.endswith('days'):
        num_days = float(annealing_time.replace('days', ''))
        return float(num_days * 24 * 60)
    elif annealing_time.endswith('d'):
        num_days = float(annealing_time.replace('d', ''))
        return float(num_days * 24 * 60)
    elif annealing_time.endswith('h'):
        num_hours = float(annealing_time.replace('h', ''))
        return float(num_hours * 60)
    elif annealing_time.endswith('min'):
        return float(float(annealing_time.replace('min', '')))
    else:
        return -1
    
def calculate_noadd_point(group_df):
    # Sort the group_df by "annealing_time"
    group_df = group_df.sort_values(by="converted_annealing_time")
    # Get the first three points (noadd, 6days, 13days)
    times = group_df["converted_annealing_time"].values[:3]

    # Ensure we don't have zero values for log calculation
    if times[0] <= 0 or times[1] <= 0 or times[2] <= 0:
        min_time = 1e-10  # Small positive value to avoid log(0) values
        times = np.maximum(times, min_time)
    
    # Calculate the logarithmic distances
    log_dist_2_3 = np.log10(times[2]) - np.log10(times[1])
    log_dist_1_2 = np.log10(times[1]) - np.log10(times[0])
    
    # Calculate the new position for noadd point to make distances equal
    if log_dist_1_2 != log_dist_2_3:
        new_log_time = np.log10(times[1]) - log_dist_2_3
        new_noadd_time = 10**new_log_time
    
    return new_noadd_time


def adjust_color_brightness(color_hex, brightness_factor):
    """
    Adjust the brightness of a hex color.
    brightness_factor: 0.0 (very light) to 1.0 (original color) to >1.0 (darker)
    Values between 0.5-1.0 create lighter versions, 1.0+ creates darker versions
    """
    import matplotlib.colors as mcolors
    # Convert hex to RGB
    rgb = mcolors.hex2color(color_hex)
    # Convert to HSV for easier brightness manipulation
    hsv = mcolors.rgb_to_hsv(rgb)
    # Adjust the value (brightness) component
    if brightness_factor < 1.0:
        # Make lighter by interpolating with white
        hsv[2] = hsv[2] + (1 - hsv[2]) * (1 - brightness_factor)
        # Reduce saturation for lighter colors
        hsv[1] = hsv[1] * brightness_factor
    else:
        # Make darker by reducing value
        hsv[2] = hsv[2] / brightness_factor
    # Convert back to RGB
    rgb_adjusted = mcolors.hsv_to_rgb(hsv)
    return mcolors.rgb2hex(rgb_adjusted)


def alpha_1(current, thickness, fluence, T_target = -20, T_meas = -20):
    thickness_um=thickness
    convFactor = currentConvFactor(T_target, T_meas)
    # I = current*1e3*convFactor
    I = current * convFactor # current in A

    # I = (frame.loc[frame['Volt_nom']== -voltage, current_column].values[0])*1e3*convFactor
    # Ierr = frame.loc[frame['Volt_nom']== -voltage,'I_err'].values[0]*1e3*convFactor
    
    area = 0.2595
    return (I)/(area*thickness_um*1e-4*fluence)
 
def alpha_err1(current, thickness, fluence, T_target = -20, T_meas = -20):
    """
    Calculate lower error bound for alpha using Gaussian error propagation.
    Combines uncertainties from:
    - Temperature (-1°C): affects current measurement
    - Thickness: ±10 μm absolute uncertainty
    - Fluence: 10% relative uncertainty
    """
    thickness_um = thickness  # thickness in μm
    convFactor = currentConvFactor(T_target, T_meas)
    I = current * convFactor  # current in A
    
    # Temperature uncertainty (-1°C)
    convFactor_temp_plus = currentConvFactor(20, -21)
    I_temp_plus = current * convFactor_temp_plus
    
    # Calculate alpha
    area = 0.2595
    alpha = I / (area * thickness_um * 1e-4 * fluence)
    
    # Relative uncertainty from current (temperature -1°C)
    rel_err_current = abs((I_temp_plus - I) / I)
    
    # Relative uncertainty from thickness (±10 μm)
    rel_err_thickness = UNCERTAINTY_THICKNESS / thickness_um
    
    # Relative uncertainty from fluence (10%)
    rel_err_fluence = UNCERTAINTY_FLUENCE
    
    # Combined relative uncertainty (Gaussian error propagation)
    rel_err_total = np.sqrt(rel_err_current**2 + rel_err_thickness**2 + rel_err_fluence**2)
    
    # Return lower error bound (alpha + uncertainty)
    return alpha * (1.0 - rel_err_total)

def alpha_err2(current, thickness, fluence, T_target = -20, T_meas = -20):
    """
    Calculate lower error bound for alpha using Gaussian error propagation.
    Combines uncertainties from:
    - Temperature (+1°C): affects current measurement
    - Thickness: ±10 μm absolute uncertainty
    - Fluence: 10% relative uncertainty
    """
    thickness_um = thickness  # thickness in μm
    convFactor = currentConvFactor(T_target, T_meas)
    I = current * convFactor  # current in A
    
    # Temperature uncertainty (+1°C)
    convFactor_temp_minus = currentConvFactor(20, -19)
    I_temp_minus = current * convFactor_temp_minus
    
    # Calculate alpha 
    area = 0.2595
    alpha = I / (area * thickness_um * 1e-4 * fluence)
    
    # Relative uncertainty from current (temperature +1°C)
    rel_err_current = abs((I_temp_minus - I) / I)
    
    # Relative uncertainty from thickness (±10 μm)
    rel_err_thickness = UNCERTAINTY_THICKNESS / thickness_um
    
    # Relative uncertainty from fluence (10%)
    rel_err_fluence = UNCERTAINTY_FLUENCE
    
    # print(f"rel_err_current: {rel_err_current}, rel_err_thickness: {rel_err_thickness}, rel_err_fluence: {rel_err_fluence}")
    
    # Combined relative uncertainty (Gaussian error propagation)
    rel_err_total = np.sqrt(rel_err_current**2 + rel_err_thickness**2 + rel_err_fluence**2)
    
    # Return upper error bound (alpha + uncertainty)
    return alpha * (1.0 + rel_err_total)


def alpha_1_without_fluence(current, thickness, T_target = -20, T_meas = -20):
    thickness=thickness
    convFactor = currentConvFactor(T_target, T_meas)
    # I = current*1e3*convFactor
    I = current * convFactor # current in A

    # I = (frame.loc[frame['Volt_nom']== -voltage, current_column].values[0])*1e3*convFactor
    # Ierr = frame.loc[frame['Volt_nom']== -voltage,'I_err'].values[0]*1e3*convFactor
    
    area = 0.2595
    return (I)/(area*thickness*1e-4)
 
def alpha_err1_without_fluence(current, thickness, T_target = -20, T_meas = -20):
    """
    Calculate upper error bound for alpha (I/V) using Gaussian error propagation.
    Combines uncertainties from:
    - Temperature (+1°C): affects current measurement
    - Thickness: ±10 μm absolute uncertainty
    Note: No fluence uncertainty since this is I/V, not I/(V*fluence)
    """
    thickness_um = thickness  # thickness in μm
    convFactor = currentConvFactor(T_target, T_meas)
    I = current * convFactor  # current in A
    
    # Temperature uncertainty (+1°C)
    convFactor_temp_plus = currentConvFactor(20, -21)
    I_temp_plus = current * convFactor_temp_plus
    
    # Calculate alpha with nominal values
    area = 0.2595
    alpha_nominal = I / (area * thickness_um * 1e-4)
    
    # Relative uncertainty from current (temperature +1°C)
    rel_err_current = abs((I_temp_plus - I) / I)
    
    # Relative uncertainty from thickness (±10 μm)
    rel_err_thickness = UNCERTAINTY_THICKNESS / thickness_um
    
    # Combined relative uncertainty (Gaussian error propagation)
    # Only current and thickness, no fluence
    rel_err_total = np.sqrt(rel_err_current**2 + rel_err_thickness**2)
    
    # Return upper error bound (alpha_nominal + uncertainty)
    return alpha_nominal * (1.0 + rel_err_total)

def alpha_err2_without_fluence(current, thickness, T_target = -20, T_meas = -20):
    """
    Calculate lower error bound for alpha (I/V) using Gaussian error propagation.
    Combines uncertainties from:
    - Temperature (-1°C): affects current measurement
    - Thickness: ±10 μm absolute uncertainty
    Note: No fluence uncertainty since this is I/V, not I/(V*fluence)
    """
    thickness_um = thickness  # thickness in μm
    convFactor = currentConvFactor(T_target, T_meas)
    I = current * convFactor  # current in A
    
    # Temperature uncertainty (-1°C)
    convFactor_temp_minus = currentConvFactor(20, -19)
    I_temp_minus = current * convFactor_temp_minus
    
    # Calculate alpha with nominal values
    area = 0.2595
    alpha_nominal = I / (area * thickness_um * 1e-4)
    
    # Relative uncertainty from current (temperature -1°C)
    rel_err_current = abs((I_temp_minus - I) / I)
    
    # Relative uncertainty from thickness (±10 μm)
    rel_err_thickness = UNCERTAINTY_THICKNESS / thickness_um
    
    # Combined relative uncertainty (Gaussian error propagation)
    # Only current and thickness, no fluence
    rel_err_total = np.sqrt(rel_err_current**2 + rel_err_thickness**2)
    
    # Return lower error bound (alpha_nominal - uncertainty)
    return alpha_nominal * (1.0 - rel_err_total)
