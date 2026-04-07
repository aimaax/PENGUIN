import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import os
import pandas as pd

from Utils.dataframe_helper import get_files, makeDataFrameBare_IV, makeDataFrameBare_CV, makeDataFrame_IV, makeDataFrame_CV, makeDataFrame_TCT
from Utils.conversion_helper import currentConvFactor
from config import FILLSTYLE, MARKERSIZE, LEGEND_SIZE, CAMPAIGN_TO_PARTICLE_DICT, RC_PLOT_STYLE, LABEL_MODE
from config import DEFAULT_DIR_DATA

def plot_iv_cv_tct(df, measurement_type, measurement, mode, color, list_style, 
                     CV_mode="1/Cs2", i_tot=False, include_uncertainty=False):
    """
    Unified plotting function for IV, CV, and TCT measurements.
    
    Args:
        df: DataFrame with database entries
        measurement_type: "bare" or "onPCB"
        measurement: "IV", "CV", or "TCT"
        mode: Label mode for mode_setting
        color: List of colors for each measurement
        list_style: List of marker styles for each measurement
        CV_mode: "CV" or "1/Cs2" for CV plots
        i_tot: Use total current for bare IV measurements
        include_uncertainty: Include uncertainty bands
    """
    plt.rcParams.update(RC_PLOT_STYLE)
    fig, ax = plt.subplots(dpi=300)
    ax.grid()
    
    # Determine file column based on measurement type
    if measurement == "IV":
        file_column = "file_IV"
    elif measurement == "CV":
        file_column = "file_CV"
    elif measurement == "TCT":
        file_column = "file_TCT"
    else:
        raise ValueError(f"Unknown measurement type: {measurement}")
    
    # Build file paths and extract metadata by iterating through database
    measurement_files = []
    metadata_list = []
    
    for idx, row in df.iterrows():
        file_end = row[file_column]
        if pd.notna(file_end):
            full_path = os.path.join(DEFAULT_DIR_DATA, file_end)
            measurement_files.append(full_path)
            
            # Extract metadata for this row
            metadata = {
                "sensor_id": row["sensor_id"],
                "campaign": row["campaign"],
                "thickness": row["thickness"],
                "fluence": row["fluence"],
                "particle": CAMPAIGN_TO_PARTICLE_DICT[row["campaign"]],
                "temperature": row["temperature"],
                "annealing_time": row["annealing_time"],
                "annealing_temp": row["annealing_temp"],
                "type_PCB": row["type"],
            }
            
            # Add measurement-specific metadata
            if measurement == "CV":
                metadata["CVF"] = row["CVF"]
                metadata["open_corr"] = row["open_corr"]
            elif measurement == "TCT":
                metadata["TCT_corr"] = row["TCT_corr"]
            
            metadata_list.append(metadata)
    
    if not measurement_files:
        print(f"No {measurement} measurements selected!")
        return fig, ax
    
    # Load measurement data
    files = get_files(measurement_files)
    dataframes = []
    
    for i, file_path in enumerate(files):
        metadata = metadata_list[i]
        
        if measurement == "IV":
            if measurement_type == "bare":
                if file_path.endswith(".iv"):
                    df_data = makeDataFrameBare_IV(file_path)
                else:
                    continue
            elif measurement_type == "onPCB":
                if file_path.endswith(".csv"):
                    df_data = makeDataFrame_IV(file_path)
                else:
                    continue
            
        elif measurement == "CV":
            if measurement_type == "bare":
                if file_path.endswith(".cv") or file_path.endswith("cv.dat"):
                    df_data = makeDataFrameBare_CV(file_path)
                else:
                    continue
            elif measurement_type == "onPCB":
                if file_path.endswith(".csv"):
                    df_data = makeDataFrame_CV(file_path, open_corr=metadata["open_corr"])
                else:
                    continue
        
        elif measurement == "TCT":
            if file_path.endswith(".csv"):
                df_data = makeDataFrame_TCT(file_path, metadata["TCT_corr"], metadata["thickness"])
            else:
                continue
        
        if type(df_data) != int:
            dataframes.append(df_data)
    
    if not dataframes:
        print(f"No {measurement} measurements loaded!")
        return fig, ax
    
    
    # Plot data
    for i, (df_data, metadata) in enumerate(zip(dataframes, metadata_list)):
        fluence_label = f"{metadata['fluence']:.1e}".replace("e+", "e")
        if LABEL_MODE == "fluence, thickness, annealing_time":
            label = f"{fluence_label}, {metadata['thickness']}μm ({metadata['annealing_time']})"
        elif LABEL_MODE == "fluence, thickness, sensor_id":
            label = f"{fluence_label}, {metadata['thickness']}μm ({metadata['sensor_id']})"
        if measurement == "IV":
            # Determine column to use
            if measurement_type == "bare":
                column = "I_tot" if i_tot else "I_pad"
                voltage = df_data["Volt_nom"]
            elif measurement_type == "onPCB":
                column = "I"
                voltage = df_data["Voltage"]
            
            curr = df_data[column] * 1e6  # Convert to uA
            
            if include_uncertainty:
                current_conv_upper = curr * currentConvFactor(T_target=-19, T_meas=-20)
                current_conv_lower = curr * currentConvFactor(T_target=-21, T_meas=-20)
                ax.fill_between(voltage, current_conv_upper, current_conv_lower, 
                               color=color[i], alpha=0.2, linewidth=0)
            
            ax.plot(voltage, curr, label=label, color=color[i], 
                   marker=list_style[i], fillstyle=FILLSTYLE, markersize=MARKERSIZE)
            
            ax.set_xlabel("Voltage [V]")
            ax.set_ylabel("Leakage Current [uA]")
        
        elif measurement == "CV":
            if measurement_type == "bare":
                voltage = df_data["v_nom"]
                column = "cs" if metadata["CVF"] >= 500 else "cp"
            elif measurement_type == "onPCB":
                voltage = df_data["Voltage"]
                column = "ser_cap"
            
            cap = df_data[column]
            
            if CV_mode == "CV":
                yaxis_label = "Capacitance [F]"
                ax.plot(voltage, cap, label=label, color=color[i], 
                       marker=list_style[i], fillstyle=FILLSTYLE, markersize=MARKERSIZE)
            elif CV_mode == "1/Cs2":
                yaxis_label = r"$1/Capacitance^2$ [$\dfrac{1}{F^{2}}$]"
                cap_inv = 1 / cap ** 2
                ax.plot(voltage, cap_inv, label=label, color=color[i], 
                       marker=list_style[i], fillstyle=FILLSTYLE, markersize=MARKERSIZE)
            
            ax.set_xlabel("Voltage [V]")
            ax.set_ylabel(yaxis_label)
        
        elif measurement == "TCT":
            voltage = abs(df_data["Voltage"])
            
            if include_uncertainty:
                error = df_data["CC_corr"] * 0.05
                charge_collection_error_down = df_data["CC_corr"] - error
                charge_collection_error_up = df_data["CC_corr"] + error
                ax.fill_between(voltage, charge_collection_error_up, 
                               charge_collection_error_down, color=color[i], 
                               alpha=0.2, linewidth=0)
            
            ax.plot(voltage, df_data["CC_corr"], label=label, 
                   color=color[i], marker=list_style[i], fillstyle=FILLSTYLE, markersize=12)
            
            ax.set_xlabel("Voltage [V]")
            ax.set_ylabel("Collected Charge [fC]")
            
    # Add legend
    ax.legend(bbox_to_anchor=(1.02, 0), fontsize=LEGEND_SIZE, loc="lower left", frameon=True)
    
    if measurement == "IV":
        plt.close(fig)
    
    return fig, ax

def grade_colors(base_color, n, light_factor=0.8, dark_factor=0.7):
    """
    Generate n graded colors around a given base color.
    - The middle (or near middle) is the base color.
    - Lighter shades go toward white.
    - Darker shades go toward black.
    - The range of shading adapts to the number of colors.

    Parameters:
        base_color (str or tuple): The base color (name or RGB tuple).
        n (int): Number of graded colors to generate.
        light_factor (float): Max shift toward white when n is large.
        dark_factor (float): Min multiplier toward black when n is large.
    """
    base_rgb = mcolors.to_rgb(base_color)

    if n == 1:
        return [base_rgb]

    # Scale how far we go based on n
    light_factor = light_factor * min(1, n / 10)   # only full strength if n ≥ 10
    dark_factor  = 1 - (1 - dark_factor) * min(1, n / 10)

    lighter = [(1 - light_factor) * c + light_factor * 1 for c in base_rgb]
    darker = [dark_factor * c for c in base_rgb]

    cmap = mcolors.LinearSegmentedColormap.from_list("graded", [lighter, base_rgb, darker])
    return [cmap(i / (n - 1)) for i in range(n)]
