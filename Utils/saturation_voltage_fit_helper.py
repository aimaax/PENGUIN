import numpy as np
import warnings
from config import N_HIGHEST_CURVATURE_POINTS

def find_saturation_voltage_from_curvature_fit(x_data, y_data, curvature_list, fit_from_TCT=False):
    """
    Find saturation voltage from curvature fit.
    
    Args:
        x_data: Voltage data
        y_data: Inverse capacitance squared or charge collection data
        curvature_list: List of curvature values
        fit_from_TCT: If True, fit slope for high side; if False, fit plateau (mean)
    """
    # Track interesting indices for the fit
    interesting_indices = np.arange(len(x_data))

    # Find index of the maximum curvature for the double kink problem, only interesting in the latest one.  
    max_curvature_index = np.argmax(curvature_list)

    # Find minimum curvature index within interesting indices
    min_curvature_index = interesting_indices[np.argmin(curvature_list[interesting_indices])]

    # Find kink on the right side of the max curvature index
    if min_curvature_index > max_curvature_index:
        max_curvature_index_margin = max_curvature_index - 4
        if max_curvature_index_margin < 0:
            max_curvature_index_margin = 0
        interesting_indices = interesting_indices[max_curvature_index_margin:]

    # Split data around minimum curvature
    left_mask = (interesting_indices < min_curvature_index)
    right_mask = (interesting_indices > min_curvature_index)
    
    # Cases for low fit indices
    if len(interesting_indices[left_mask]) > 9:
        # For left fit, only care about the 11 closest points and exclude the closest point to the minimum curvature index
        low_fit_indices = interesting_indices[left_mask][-9:-1] # keep 10 points for the low fit
    elif len(interesting_indices[left_mask]) > 4:
        # If len is less than 11 but larger than 4, then exclude the closest point to the minimum curvature index and first point 
        low_fit_indices = interesting_indices[left_mask][1:-1] # removes 2 points
    else:
        # If len is less than 3, then exclude the closest point to the minimum curvature index
        low_fit_indices = interesting_indices[left_mask][:-1] # removes 1 point

    # Keep all points for the high fit and find the N_HIGHEST_CURVATURE_POINTS points for high fit
    high_fit_indices = interesting_indices[right_mask]
    

    # Select top N_HIGHEST_CURVATURE_POINTS (from config.py) points on each side to fit the straight line
    low_fit_highest_indices = low_fit_indices[np.argsort(curvature_list[low_fit_indices])[-N_HIGHEST_CURVATURE_POINTS:]]
    high_fit_highest_indices = high_fit_indices[np.argsort(curvature_list[high_fit_indices])[-N_HIGHEST_CURVATURE_POINTS:]]
    
    # --- Post-selection curvature filtering with 50% rule ---
    curvature_fraction = 0.5  # Keep points within 50% of the maximum curvature
    min_points = 2             # Always keep at least 2 points

    # LOW side
    if len(low_fit_highest_indices) > 0:
        low_curvs = curvature_list[low_fit_highest_indices]
        # print("low_curvs: ", low_curvs)
        
        # Find indices of top 2 curvature points
        top_two_idx = np.argsort(low_curvs)[-min_points:]
        second_largest_curv = low_curvs[top_two_idx[0]]  # index 0 is second largest after argsort
        
        # Keep points within fraction of second largest curvature
        within_range = np.where(low_curvs >= curvature_fraction * second_largest_curv)[0]
        
        # Always keep at least top 2 points
        keep_idx = np.unique(np.concatenate([top_two_idx, within_range]))
        
        # Ensure at least 2 points are kept
        if len(keep_idx) < min_points:
            keep_idx = np.argsort(low_curvs)[-min_points:]
        
        low_fit_highest_indices = low_fit_highest_indices[keep_idx]

    # HIGH side
    if len(high_fit_highest_indices) > 0:
        high_curvs = curvature_list[high_fit_highest_indices]
        # print("high_curvs: ", high_curvs)
        
        top_two_idx = np.argsort(high_curvs)[-min_points:]
        second_largest_curv = high_curvs[top_two_idx[0]]
        
        within_range = np.where(high_curvs >= curvature_fraction * second_largest_curv)[0]
        
        keep_idx = np.unique(np.concatenate([top_two_idx, within_range]))
        
        if len(keep_idx) < min_points:
            keep_idx = np.argsort(high_curvs)[-min_points:]
        
        high_fit_highest_indices = high_fit_highest_indices[keep_idx]

    try:
        # Fit lines to selected points
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", np.RankWarning)
            low_fit_coeffs = np.polyfit(x_data.iloc[low_fit_highest_indices], y_data.iloc[low_fit_highest_indices], 1)
            
            # HIGH FIT: Use plateau (mean) for CV, linear fit for TCT
            if not fit_from_TCT:
                # For CV data, use mean value as plateau
                high_y_values = y_data.iloc[high_fit_highest_indices]
                plateau_y = np.mean(high_y_values)
                high_fit_coeffs = np.array([0, plateau_y])  # slope=0, intercept=mean value
                # print(f"CV fit - High side plateau (mean): {plateau_y}")
            else:
                # For TCT data, use linear fit
                high_fit_coeffs = np.polyfit(x_data.iloc[high_fit_highest_indices], y_data.iloc[high_fit_highest_indices], 1)
                # print(f"TCT fit - High side slope: {high_fit_coeffs[0]}")
        
        # Find intersection of the two lines
        saturation_V, intersection_y = find_intersection_of_two_lines(low_fit_coeffs, high_fit_coeffs)
    except Exception as e:
        print(f"Error in finding saturation voltage from automatic curvature fit: {e}")
        return None, None, None, None, None, None
    
    return low_fit_highest_indices, high_fit_highest_indices, low_fit_coeffs, high_fit_coeffs, saturation_V, intersection_y


def calculate_saturation_voltage_with_uncertainty(x_low_fit, y_low_fit, high_fit_coeffs, plateau_lower, plateau_upper):
    """
    Calculate saturation voltage with uncertainty by trying all possible combinations of low fit points.
    
    Args:
        x_low_fit: x data points in low fit region
        y_low_fit: y data points in low fit region
        high_fit_coeffs: coefficients for high fit [slope, intercept]
        plateau_lower: lower bound of plateau/endcap value
        plateau_upper: upper bound of plateau/endcap value
    
    Returns:
        saturation_V_mean: mean saturation voltage
        saturation_V_lower: lower bound (minimum value)
        saturation_V_upper: upper bound (maximum value)
    """
    from itertools import combinations
    
    n_points = len(x_low_fit)
    all_sat_voltages = []
    
    points_to_try = range(n_points, 1, -1) if n_points == 3 or n_points == 2 else range(n_points, 2, -1)
    
    # Try all combinations from n_points down to 2 points
    for subset_size in points_to_try: 
        # Generate all combinations of indices for this subset size
        for combo_indices in combinations(range(n_points), subset_size):
            # Extract the subset of points
            x_subset = x_low_fit.iloc[list(combo_indices)]
            y_subset = y_low_fit.iloc[list(combo_indices)]
            
            try:
                # Fit a line to this subset
                low_fit_coeffs_subset = np.polyfit(x_subset, y_subset, deg=1)
                
                # Calculate intersection with central plateau
                high_fit_coeffs_central = [high_fit_coeffs[0], high_fit_coeffs[1]]
                sat_V_central, _ = find_intersection_of_two_lines(
                    low_fit_coeffs_subset, high_fit_coeffs_central
                )
                all_sat_voltages.append(sat_V_central)
                
                # Calculate intersection with lower plateau
                high_fit_coeffs_lower = [0, plateau_lower]
                sat_V_lower_plateau, _ = find_intersection_of_two_lines(
                    low_fit_coeffs_subset, high_fit_coeffs_lower
                )
                all_sat_voltages.append(sat_V_lower_plateau)
                
                # Calculate intersection with upper plateau
                high_fit_coeffs_upper = [0, plateau_upper]
                sat_V_upper_plateau, _ = find_intersection_of_two_lines(
                    low_fit_coeffs_subset, high_fit_coeffs_upper
                )
                all_sat_voltages.append(sat_V_upper_plateau)
                
            except Exception as e:
                # Skip combinations that don't produce valid fits
                continue
    
    # Calculate statistics with asymmetric errors
    if len(all_sat_voltages) > 0:
        all_sat_voltages = np.array(all_sat_voltages)
        saturation_V_mean = np.mean(all_sat_voltages)
        saturation_V_min = np.min(all_sat_voltages)
        saturation_V_max = np.max(all_sat_voltages)
        
        # Bounds are the actual min and max
        saturation_V_lower = saturation_V_min
        saturation_V_upper = saturation_V_max
        
        return saturation_V_mean, saturation_V_lower, saturation_V_upper
    else:
        return None, None, None
    

def find_intersection_of_two_lines(low_fit_coeffs, high_fit_coeffs):
    a1, b1 = low_fit_coeffs
    a2, b2 = high_fit_coeffs
    intersection_x = (b2 - b1) / (a1 - a2)
    intersection_y = a1 * intersection_x + b1
    return intersection_x, intersection_y
    