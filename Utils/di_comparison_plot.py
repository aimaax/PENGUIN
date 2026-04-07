import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import os
from config import RC_PLOT_STYLE, MARKERSIZE
from config import DEFAULT_DIR_DATA
from Utils.dataframe_helper import makeDataFrame_TCT, makeDataFrame_IV
from Utils.conversion_helper import convert_annealing_time
from Utils.conversion_helper import alpha_1, alpha_err1, alpha_err2
from Utils.conversion_helper import currentConvFactor

def get_di_comparison_plot(
    database, 
    campaigns, 
    measurement_type, 
    thickness, 
    annealing_temp, 
    sensor_id_fr, 
    sensor_id_sr, 
    sensor_id_hf, 
    sensor_id_lf, 
    type_of_plot, 
    voltage, 
    logx, 
    add_quarter_ann_time_from_di_first_round, 
    split_x_axis, 
    points_after_last_annealing_time, 
    plot_saturation_voltage_from_tct=None,
    plot_ratio_DI_vs_HF=False,
    plot_average_ratio_DI_vs_HF=False,
    skip_x_colors_markers = 0,
    sat_volt_cv_tct="CV"
):
    
    plt.rcParams.update(RC_PLOT_STYLE) # use RC_PLOT_STYLE by default
    
    pd.set_option('display.max.rows', None)
    pd.set_option('display.max.columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    
    sensor_id = sensor_id_fr + sensor_id_sr + sensor_id_hf + sensor_id_lf

    use_saturation_voltage = (
        type_of_plot in ("CC", "CCE", "alpha") and voltage == "Saturation Voltage"
    )
    
    df = database[
        (database.index.get_level_values("campaign").isin(campaigns)) &
        (database.index.get_level_values('thickness').isin([int(t) for t in thickness])) &
        (database.index.get_level_values("sensor_id").isin(sensor_id)) &
        (database['annealing_temp'].isin([float(t) for t in annealing_temp])) &
        (database["type"].isin(measurement_type)) &
        (database['Blacklisted']==False)
    ].reset_index()

    df_metadata = df[["sensor_id", "campaign", "fluence", "thickness"]].drop_duplicates().copy()
    
    if df.empty:
        print("No measurements selected!")
        return 0

    # Iterate directly over the filtered dataframe
    df_list = []
    for _, row in df.iterrows():
        tmp = None
        
        # Get corresponding file end for the type of plot 
        if type_of_plot == "alpha":
            file_end = row["file_IV"]
        elif type_of_plot in ("CC", "CCE"):
            file_end = row["file_TCT"]
        else:
            file_end = None
            
        # Case where type of plot is alpha or CC/CCE --> need to read file to get data from files
        if type_of_plot == "alpha" and file_end and str(file_end).endswith(".csv"):
            tmp = makeDataFrame_IV(os.path.join(DEFAULT_DIR_DATA, file_end)) # "Voltage", "I", "I_err"

        elif type_of_plot in ("CC", "CCE") and file_end and str(file_end).endswith(".csv"):
            tmp = makeDataFrame_TCT(os.path.join(DEFAULT_DIR_DATA, file_end), row["TCT_corr"], row["thickness"]) # "Voltage", "CC_corr", "CC_err_corr", "CCEff_corr", "CCEff_err_corr"; error here not used as we take 5% for everything considered

        # Saturation voltage is already analysed and stored in the database, no need to retrieve files. 
        if type_of_plot == "saturation voltage":
            if plot_saturation_voltage_from_tct == True:
                tmp = pd.DataFrame([{
                    "sat_V_TCT": row["sat_V_TCT"],
                    "sat_V_err_down_TCT": row["sat_V_err_down_TCT"],
                    "sat_V_err_up_TCT": row["sat_V_err_up_TCT"],
                    "low_fit_start_TCT": row["low_fit_start_TCT"],
                    "low_fit_stop_TCT": row["low_fit_stop_TCT"],
                    "high_fit_start_TCT": row["high_fit_start_TCT"],
                    "high_fit_stop_TCT": row["high_fit_stop_TCT"],
                }])
            else:
                tmp = pd.DataFrame([{
                    "sat_V_CV": row["sat_V_CV"],
                    "sat_V_err_down_CV": row["sat_V_err_down_CV"],
                    "sat_V_err_up_CV": row["sat_V_err_up_CV"],
                    "low_fit_start_CV": row["low_fit_start_CV"],
                    "low_fit_stop_CV": row["low_fit_stop_CV"],
                    "high_fit_start_CV": row["high_fit_start_CV"],
                    "high_fit_stop_CV": row["high_fit_stop_CV"],
                }])

        if tmp is not None and isinstance(tmp, pd.DataFrame):
            for col in ["sensor_id", "fluence", "thickness", "campaign",
                        "TCT_corr", "annealing_time", "annealing_temp",
                        "corrected_annealing_time", "corr_ann_time_err_up", "corr_ann_time_err_down"]:
                tmp[col] = row[col]

            # Keep CV saturation voltage for interpolation mode (CC/CCE/alpha)
            if use_saturation_voltage and type_of_plot in ("CC", "CCE", "alpha"):
                tmp["sat_V"] = row.get("sat_V_CV", np.nan) if sat_volt_cv_tct == "CV" else row.get("sat_V_TCT", np.nan)

            df_list.append(tmp)
    
    if not df_list:
        print("No TCT measurements selected!")
        return 0

    # Create a single DataFrame
    df = pd.concat(df_list, ignore_index=True)
    
    # Select only the rows corresponding to the specified voltage, only applicable for CC, CCE, and alpha
    if type_of_plot in ("CC", "CCE", "alpha"):
        if use_saturation_voltage:
            df = _process_saturation_voltage_di(df=df, type_of_plot=type_of_plot, sat_volt_cv_tct=sat_volt_cv_tct)
        else:
            df = df[df["Voltage"] == voltage]
    
    if type_of_plot == "alpha":
        df["I"] = df["I"].abs() # Take the absolute value of the current column "I" as we measure pad only for low fluence campaign and receive neg. current because of polarity of cables. 
        df["alpha"] = df.apply(
            lambda row: alpha_1(current=row['I'], thickness=row['thickness'], fluence=row['fluence'], T_target=20),
            axis=1
        )
        df["alpha_err1"] = df.apply(
            lambda row: abs(alpha_err1(current=row['I'], thickness=row['thickness'], fluence=row['fluence'], T_target=20)),
            axis=1
        )
        df["alpha_err2"] = df.apply(
            lambda row: abs(alpha_err2(current=row['I'], thickness=row['thickness'], fluence=row['fluence'], T_target=20)),
            axis=1
        )
        
    df = df.copy()
    df["annealing_time"] = df["annealing_time"].apply(convert_annealing_time) # convert noadd to 0 and other values to min
    df["corrected_annealing_time"] = df["corrected_annealing_time"].apply(convert_annealing_time) # convert all corrected annealing times to min and make it into float
    df["corr_ann_time_err_up"] = df["corr_ann_time_err_up"].apply(convert_annealing_time) # convert all corrected annealing times to min
    df["corr_ann_time_err_down"] = df["corr_ann_time_err_down"].apply(convert_annealing_time) # convert all corrected annealing times to min

    # Find maximum annealing time of DoubleIrrNeutron2025 campaign (first round) to add to second round data points
    max_annealing_time_di_neutron_first_round = df[df["campaign"] == "DoubleIrrNeutron2025"]["corrected_annealing_time"].max()
    if add_quarter_ann_time_from_di_first_round:
        # Apply temperature-specific quarter time adjustment
        for temp in df["annealing_temp"].unique():
            # Get max annealing time for this specific temperature from first round
            max_ann_time_temp = df[
                (df["campaign"] == "DoubleIrrNeutron2025") & 
                (df["annealing_temp"] == temp)
            ]["corrected_annealing_time"].max()
            
            # Apply adjustment only to second round data at this temperature
            di_sr_temp_mask = (
                (df["campaign"] == "DoubleIrrSRNeutron2025") & 
                (df["annealing_temp"] == temp)
            )
            
            if not pd.isna(max_ann_time_temp):
                df.loc[di_sr_temp_mask, "corrected_annealing_time"] += max_ann_time_temp * 0.25

    # Sort dataframe by first lowest fluence, then highest thickness and then low to high corrected annealing time
    df = df.sort_values(by=["fluence", "thickness", "corrected_annealing_time"], ascending=[True, False, True])
    
    # Find maximum annealing_time of DoubleIrrSRNeutron2025 campaign to filter out data points after this time
    max_annealing_time = df[df["campaign"] == "DoubleIrrSRNeutron2025"]["corrected_annealing_time"].max()
    
    # Filter out annealing time data points of non DoubleIrrNeutron2025 and DoubleIrrSRNeutron2025 campaigns
    double_irr_campaign_mask = df["campaign"].isin(["DoubleIrrNeutron2025", "DoubleIrrSRNeutron2025"])
    ref_df = df[double_irr_campaign_mask]
    other_campaigns_df = df[~double_irr_campaign_mask]
    
    filtered_other_campaigns_df = []
    
    # Group by BOTH campaign AND sensor_id to filter per sensor
    for (campaign, sensor_id), group in other_campaigns_df.groupby(['campaign', 'sensor_id']):
        # Sort the annealing times for this specific sensor
        sorted_times = group["corrected_annealing_time"].unique() # already sorted
        # Find the first index where annealing_time > max_ref_time
        idx = (sorted_times > max_annealing_time).argmax() if any(sorted_times > max_annealing_time) else len(sorted_times)
        
        # Include up to N extra steps after max_ref_time FOR THIS SENSOR
        last_idx = min(idx + points_after_last_annealing_time, len(sorted_times))
        allowed_times = sorted_times[:last_idx]

        # Filter this sensor's data to only include allowed times
        filtered_other_campaigns_df.append(group[group["corrected_annealing_time"].isin(allowed_times)])
        
    # Concatenate the filtered other campaigns df
    df = pd.concat([ref_df] + filtered_other_campaigns_df, ignore_index=True)
    
    
    # Split campaign into left and right side of the cut, left side is DoubleIrrNeutron2025 and right side is DoubleIrrSRNeutron2025 + other campaigns
    left_df = df[df["campaign"].isin(["DoubleIrrNeutron2025"])]
    right_df = df[df["campaign"].isin([c for c in campaigns if c not in ["DoubleIrrNeutron2025"]])]
    
    # Create a mapping of base sensor names to ensure color consistency
    group_style = {}
    unique_sensors = df["sensor_id"].unique()

    # Define distinct base colors for each sensor group
    group_colors = ["#e41a1c", "#377eb8", "#4daf4a", "#7570b3", "#000000", "#ff7f00", "#a65628"]

    # Define marker options for different sensor groups
    marker_options = ['x', 's', '^', 'v', 'o', '<', '>', 'D', 'P', '*']

    # Create matching groups for markers and colors
    # Group DI sensors with their SR counterparts and matching HF sensors by fluence/thickness
    sensor_groups = []

    # Get DoubleIrrSRNeutron2025 sensors as the primary reference for grouping
    di_sr_sensors_with_info = df_metadata[df_metadata["campaign"] == "DoubleIrrSRNeutron2025"][
        ["sensor_id", "fluence", "thickness"]
    ].drop_duplicates().reset_index(drop=True)

    for idx, sr_row in di_sr_sensors_with_info.iterrows():
        sr_sensor_id = sr_row["sensor_id"]
        sr_fluence = sr_row["fluence"]
        sr_thickness = sr_row["thickness"]
        
        # Create a group containing:
        # 1. The SR sensor (DI second round)
        # 2. The matching DI first round sensor (base name)
        # 3. The matching HF sensor (same fluence and thickness)
        
        group = {"di_sr": [], "di_first": [], "hf": []}
        
        # Add SR sensor
        group["di_sr"].append(sr_sensor_id)
        
        # Add matching DI first round sensor
        base_sensor = get_base_sensor_name(sr_sensor_id)
        di_first_sensors = df_metadata[df_metadata["campaign"] == "DoubleIrrNeutron2025"]["sensor_id"].unique()
        if base_sensor in di_first_sensors:
            group["di_first"].append(base_sensor)
        
        # Add matching HF sensor(s) with same fluence and thickness
        hf_matching = df_metadata[
            (df_metadata["campaign"] == "HighFluenceIrrNeutron2023") &
            (df_metadata["fluence"] == sr_fluence) &
            (df_metadata["thickness"] == sr_thickness)
        ]["sensor_id"].unique()
        
        for hf_sensor in hf_matching:
            group["hf"].append(hf_sensor)
        
        sensor_groups.append(group)

    # Assign colors and markers to each group
    for group_idx, sensor_group in enumerate(sensor_groups):
        base_color = group_colors[(group_idx + skip_x_colors_markers) % len(group_colors)]
        marker = marker_options[(group_idx + skip_x_colors_markers) % len(marker_options)]
        
        darker_color = adjust_color_brightness(base_color, 1.1)
        
        # Assign base color to DI first round and DI SR sensors
        for sensor_id in sensor_group["di_first"] + sensor_group["di_sr"]:
            # group_style[sensor_id] = {"color": base_color, "marker": marker}
            group_style[sensor_id] = {"color": darker_color, "marker": 'o'}
        
        # Assign lighter version of base color to HF sensors
        lighter_color = adjust_color_brightness(base_color, 0.6)  # 0.6 makes it noticeably lighter
        for sensor_id in sensor_group["hf"]:
            # group_style[sensor_id] = {"color": lighter_color, "marker": marker}
            group_style[sensor_id] = {"color": lighter_color, "marker": 'x'}
            
    # Check if we're plotting a ratio
    if plot_ratio_DI_vs_HF:
        # Calculate ratio data
        ratio_df = calculate_ratio_plot_data(
            df, 
            type_of_plot, 
            plot_saturation_voltage_from_tct, 
            sensor_groups, 
            group_style,
        )
        
        if ratio_df.empty:
            print("No ratio data could be calculated!")
            return 0
        
        # Plot ratio
        fig, ax = plt.subplots(1, 1, figsize=(4.5, 3), dpi=300)
        # ax.set_facecolor('#FAFAFA')
        ax.grid(True)
        
        # Plot each sensor's ratio
        for sensor_id in ratio_df["sensor_id"].unique():
            # sensor_ratio_data = ratio_df[ratio_df["sensor_id"] == sensor_id].sort_values("corrected_annealing_time")
            sensor_ratio_data = ratio_df[ratio_df["sensor_id"] == sensor_id]
            color = sensor_ratio_data["color"].iloc[0]
            marker = sensor_ratio_data["marker"].iloc[0]
            linestyle = sensor_ratio_data["linestyle"].iloc[0]
            campaign = sensor_ratio_data["campaign"].iloc[0]
            fluence = sensor_ratio_data["fluence"].iloc[0]
            thickness = sensor_ratio_data["thickness"].iloc[0]
            hf_sensor = sensor_ratio_data["hf_sensor"].iloc[0]
            
            # label = f"{fluence:.1e}".replace("+", "") + fr"$\,n$/cm$^2$, {thickness}μm"
            label = f"{fluence:.1e}".replace("+", "") + fr", {thickness}μm"

            # Plot error bars if available
            if "ratio_err_up" in sensor_ratio_data.columns and "ratio_err_down" in sensor_ratio_data.columns:
                ratio_values = sensor_ratio_data["ratio"].values
                # Convert to float array, replacing None with np.nan
                ratio_err_up_values = pd.to_numeric(sensor_ratio_data["ratio_err_up"], errors="coerce").values
                ratio_err_down_values = pd.to_numeric(sensor_ratio_data["ratio_err_down"], errors="coerce").values
                
                # Handle cases where only some error bars are available
                # Replace NaN/None with 0 for matplotlib (0 means no error bar in that direction)
                yerr_lower = np.where(np.isnan(ratio_err_down_values), 0, ratio_err_down_values)
                yerr_upper = np.where(np.isnan(ratio_err_up_values), 0, ratio_err_up_values)
                yerr = [yerr_lower, yerr_upper]
                
                # Plot error bars if at least one direction has valid data
                if not (np.all(yerr_lower == 0) and np.all(yerr_upper == 0)):
                    ax.errorbar(
                        sensor_ratio_data["corrected_annealing_time"],
                        sensor_ratio_data["ratio"],
                        yerr=yerr,
                        fmt="none",
                        capsize=4,
                        color=color,
                        alpha=1
                    )
            
            ax.plot(
                sensor_ratio_data["corrected_annealing_time"],
                sensor_ratio_data["ratio"],
                linestyle=linestyle,
                marker=marker,
                markersize=MARKERSIZE,
                color=color,
                label=label,
            )

        # Add colored background regions to indicate good/bad outcome
        # Get current y-axis limits to determine extent of colored regions
        ylim = ax.get_ylim()

        if type_of_plot in ["CC", "CCE"]:
            # For CC/CCE: Higher ratio is better (DI SR > HF is good)
            # Green region above 1 (good)
            ax.axhspan(1, 2, facecolor="green", alpha=0.1, zorder=0)
            # Red region below 1 (bad)
            ax.axhspan(0, 1, facecolor="red", alpha=0.1, zorder=0)
        elif type_of_plot in ["alpha", "saturation voltage"]:
            # For alpha/saturation voltage: Lower ratio is better (DI SR < HF is good)
            # Green region below 1 (good)
            ax.axhspan(0, 1, facecolor="green", alpha=0.1, zorder=0)
            # Red region above 1 (bad)
            ax.axhspan(1, 2, facecolor="red", alpha=0.1, zorder=0)
        
        # Add horizontal line at ratio = 1
        ax.axhline(y=1, color='black', linestyle=':', linewidth=1, alpha=0.6)
        
        # Center the plot around ratio = 1 with symmetric y-axis limits
        if not ratio_df.empty:
            ratio_values = ratio_df["ratio"].values
            ratio_max = ratio_values.max()
            ratio_min = ratio_values.min()
            
            # Calculate deviations from 1
            max_deviation_above = abs(ratio_max - 1.0)
            max_deviation_below = abs(ratio_min - 1.0)
            
            # Use the larger deviation to make it symmetric
            max_deviation = max(max_deviation_above, max_deviation_below)
            
            # Add margin (20% of the deviation, with a minimum margin)
            margin = max(max_deviation * 0.2, 0.05)  # At least 0.05 margin
            
            # Set symmetric y-limits centered at 1
            y_center = 1.0
            y_range = max_deviation + margin
            ax.set_ylim(y_center - y_range, y_center + y_range)
        
        # Set x-axis limits to match the regular plot
        # ax.set_xlim(xlim_for_ratio)
        
        annealing_temp_label = annealing_temp[0]
        if annealing_temp_label == 20.0:
            annealing_temp_label = "20.5°C"
        elif annealing_temp_label == 40.0:
            annealing_temp_label = "40°C"
        elif annealing_temp_label == 60.0:
            annealing_temp_label = "60°C"
        ax.set_xlabel(f"Annealing Time [min] @ {annealing_temp_label}", fontweight='bold')
        # ax.set_xlabel("Annealing Time [min]")
        if type_of_plot == "alpha":
            ax.set_ylabel(fr"$\alpha$ Ratio @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
            # ax.set_ylabel(fr"$\alpha$ DI SR / HF [A/cm] @ {int(voltage)} V")
        elif type_of_plot == "CC":
            ax.set_ylabel(f"CC Ratio @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
            # ax.set_ylabel(f"CC DI SR / HF [fC] @ {int(voltage)} V")
        elif type_of_plot == "CCE":
            ax.set_ylabel(f"CCE Ratio @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
            # ax.set_ylabel(f"CCE DI SR / HF [%] @ {int(voltage)} V")
        elif type_of_plot == "saturation voltage":
            ax.set_ylabel(fr"$V_{{sat}}$ Ratio", fontweight='bold')
            # ax.set_ylabel(fr"$V_{{sat}}$ DI SR / HF [V] @ {_voltage_axis_suffix(voltage)}")
        ax.legend(markerscale=2, fontsize=6, frameon=True, fancybox=True, shadow=True, loc="best")
        
        plt.title(f"Ratio Plot: DI SR / HF vs Annealing Time @ {_voltage_title_label(voltage)}", weight='bold')
        # plt.title(f"Ratio Plot: DI SR / HF vs Annealing Time @ {abs(voltage):.0f} V")
        
        # ===== NEW CODE: Create additional plot for average ratios =====
        if plot_average_ratio_DI_vs_HF:
            # Calculate mean ratio for each thickness/fluence/temperature combination
            # print(ratio_df)
            grouped_ratios = ratio_df.groupby(["thickness", "fluence", "annealing_temp"]).agg({
                "ratio": ["mean", "std", "count"],
                "color": "first",
                "marker": "first"
            }).reset_index()
            # print(grouped_ratios)
            
            # Flatten column names
            grouped_ratios.columns = ["thickness", "fluence", "annealing_temp", "ratio_mean", "ratio_std", "count", "color", "marker"]
            
            # Sort by the order you specified: (300, 2e15), (300, 4e15), etc.
            desired_order = [
                (300, 2e15), (300, 4e15), (200, 4e15), 
                (200, 6e15), (200, 8e15), (120, 6e15), (120, 1.5e16)
            ]
            
            # Create a sorting key based on desired order
            order_dict = {combo: idx for idx, combo in enumerate(desired_order)}
            grouped_ratios["sort_key"] = grouped_ratios.apply(
                lambda row: order_dict.get((row["thickness"], row["fluence"]), 999), 
                axis=1
            )
            grouped_ratios = grouped_ratios.sort_values(["sort_key", "annealing_temp"])
            
            # Filter to only include combinations in desired_order
            grouped_ratios = grouped_ratios[grouped_ratios["sort_key"] != 999]
            
            # Get unique thickness/fluence combinations
            unique_combos = grouped_ratios[["thickness", "fluence", "sort_key"]].drop_duplicates().sort_values("sort_key").reset_index(drop=True)

            # Create x-axis labels for ALL desired combinations (regardless of data availability)
            x_labels = []
            for thickness_val, fluence_val in desired_order:
                label = f"{int(thickness_val)}μm\n{fluence_val:.1e}".replace("+", "")
                x_labels.append(label)

            x_positions = np.arange(len(desired_order))

            # Create a mapping from (thickness, fluence) to x-position
            combo_to_xpos = {combo: idx for idx, combo in enumerate(desired_order)}
            
            # Calculate standard error (std / sqrt(n))
            grouped_ratios["ratio_stderr"] = grouped_ratios["ratio_std"]
            
            # Create new figure for average ratios
            fig_avg, ax_avg = plt.subplots(1, 1, figsize=(6, 4), dpi=300)
            # ax_avg.set_facecolor("#FAFAFA")
            ax_avg.grid(True, alpha=0.3)
            
            # Define temperature-specific formatting
            # ["#e41a1c", "#377eb8", "#4daf4a", "#7570b3", "#000000", "#ff7f00", "#a65628"]
            # temp_colors = {20: "#377eb8", 40: "#000000", 60: "#ff7f00"}
            temp_colors = {20: "#2E86AB", 40: "#3B9C5C", 60: "#C44536"}
            temp_markers = {20: "o", 40: "x", 60: ">"}
            temp_offsets = {20: -0.15, 40: 0.0, 60: 0.15}  # Horizontal offsets for visual separation
            temp_labels_added = set()

            # Plot average ratios with error bars
            for _, row in grouped_ratios.iterrows():
                # Get x-position from the desired_order mapping
                combo_key = (row["thickness"], row["fluence"])
                
                # Skip if this combination is not in our desired order
                if combo_key not in combo_to_xpos:
                    continue
                
                x_idx = combo_to_xpos[combo_key]
                
                # Get temperature-specific formatting
                temp = row["annealing_temp"]
                marker = temp_markers.get(temp, "o")
                temp_color = temp_colors.get(temp, "black")
                x_offset = temp_offsets.get(temp, 0.0)
                
                # Create label only once per temperature
                if temp not in temp_labels_added:
                    if temp == 20:
                        label = "20.5°C"
                    else:
                        label = f"{int(temp)}°C"
                    temp_labels_added.add(temp)
                else:
                    label = None
                
                ax_avg.errorbar(
                    x_positions[x_idx] + x_offset,  # Apply horizontal offset
                    row["ratio_mean"],
                    yerr=row["ratio_stderr"],
                    fmt=marker,
                    markersize=8,
                    color=temp_color,
                    markerfacecolor=temp_color,
                    markeredgecolor=temp_color,
                    capsize=5,
                    capthick=1,
                    elinewidth=2,
                    label=label,
                    alpha=1
                )

            # Add colored background regions to indicate good/bad outcome
            # Get current y-axis limits
            ylim_avg = ax_avg.get_ylim()

            if type_of_plot in ["CC", "CCE"]:
                # For CC/CCE: Higher ratio is better
                # Green region above 1 (good)
                ax_avg.axhspan(1, 2, facecolor="green", alpha=0.1, zorder=0)
                # Red region below 1 (bad)
                ax_avg.axhspan(0, 1, facecolor="red", alpha=0.1, zorder=0)
            elif type_of_plot in ["alpha", "saturation voltage"]:
                # For alpha/saturation voltage: Lower ratio is better
                # Green region below 1 (good)
                ax_avg.axhspan(0, 1, facecolor="green", alpha=0.1, zorder=0)
                # Red region above 1 (bad)
                ax_avg.axhspan(1, 2, facecolor="red", alpha=0.1, zorder=0)
                        
            # Add horizontal line at ratio = 1
            ax_avg.axhline(y=1, color="black", linestyle=":", linewidth=1, alpha=0.7)
            
            # Add vertical lines to separate thickness groups (300μm | 200μm | 120μm)
            ax_avg.axvline(x=1.5, color="gray", linestyle="--", linewidth=0.7, alpha=1)
            ax_avg.axvline(x=4.5, color="gray", linestyle="--", linewidth=0.7, alpha=1)
            
            # Formatting
            ax_avg.set_xticks(x_positions)
            ax_avg.set_xticklabels(x_labels, rotation=0, ha="center", fontsize=8)
            ax_avg.set_xlim(-0.5, len(x_positions) - 0.5)
            ax_avg.set_xlabel(r"Thickness & Fluence [$n_{eq}$/cm$^{2}$]", fontsize=10, fontweight='bold')
            
            if type_of_plot == "alpha":
                ax_avg.set_ylabel(fr"$\alpha$ Ratio @ {_voltage_axis_suffix(voltage)}", fontsize=10, fontweight='bold')
            elif type_of_plot == "CC":
                ax_avg.set_ylabel(f"CC Ratio @ {_voltage_axis_suffix(voltage)}", fontsize=10, fontweight='bold')
            elif type_of_plot == "CCE": 
                ax_avg.set_ylabel(f"CCE Ratio @ {_voltage_axis_suffix(voltage)}", fontsize=10, fontweight='bold')
            elif type_of_plot == "saturation voltage":
                ax_avg.set_ylabel(fr"$V_{{sat}}$ Ratio", fontsize=10, fontweight='bold')
            
            ax_avg.set_title(f"Average Ratio: DI SR / HF by Thickness/Fluence @ {_voltage_title_label(voltage)}", fontsize=11, fontweight='bold')
            
            # Add legend
            ax_avg.legend(fontsize=8, loc="best", frameon=True, fancybox=True, shadow=True)
            
            # Set y-limits with some padding around ratio = 1
            if not grouped_ratios.empty:
                y_min = (grouped_ratios["ratio_mean"] - grouped_ratios["ratio_stderr"]).min()
                y_max = (grouped_ratios["ratio_mean"] + grouped_ratios["ratio_stderr"]).max()
                y_center = 1.0
                y_range = max(abs(y_max - y_center), abs(y_center - y_min))
                ax_avg.set_ylim(y_center - y_range * 1.2, y_center + y_range * 1.2)
            
            plt.tight_layout()
            
            return fig_avg, ax_avg  # Show average plot in GUI
        # ===== END NEW CODE =====

        return fig, ax
    
    
            
    # Assign linestyles based on campaign
    di_linestyle = (0, (3, 2))
    hf_linestyle = (0, (1, 3))

    for s in df["sensor_id"].unique():
        if s in group_style:
            sensor_campaign = df[df["sensor_id"] == s]["campaign"].iloc[0]
            if sensor_campaign in ["DoubleIrrNeutron2025", "DoubleIrrSRNeutron2025"]:
                group_style[s]["linestyle"] = di_linestyle
            elif sensor_campaign == "HighFluenceIrrNeutron2023":
                group_style[s]["linestyle"] = hf_linestyle
            else:
                group_style[s]["linestyle"] = "--"

    # Handle any sensors not in groups (e.g., LowFluence or unmatched sensors)
    for sensor in unique_sensors:
        if sensor not in group_style:
            # Get campaign to decide color and marker
            sensor_campaign = df[df["sensor_id"] == sensor]["campaign"].iloc[0]
            if "DoubleIrr" in sensor_campaign:
                default_color = group_colors[0]  # Use first color as default
            else:
                default_color = group_colors[-1]  # Use last color as default
            
            default_marker = marker_options[0]
            group_style[sensor] = {"color": default_color, "marker": default_marker}

    # Add legend labels based on campaign
    for s in df["sensor_id"].unique():
        if s in group_style:
            sensor_campaign = df[df["sensor_id"] == s]["campaign"].iloc[0]
            if sensor_campaign == "DoubleIrrNeutron2025":
                group_style[s]["legend_label"] = "First Round DI"
            
    if split_x_axis:
        # --- Create broken x-axis figure ---
        fig, (ax1, ax2) = plt.subplots(1, 2, sharey=True, figsize=(4.5, 3), dpi=300,
                                    gridspec_kw={'wspace':0.05, 'width_ratios':[0.3, 0.7]})
        
        plot_grouped_side(ax1, left_df, type_of_plot, plot_saturation_voltage_from_tct, group_style, add_quarter_ann_time_from_di_first_round, max_annealing_time_di_neutron_first_round)
        plot_grouped_side(ax2, right_df, type_of_plot, plot_saturation_voltage_from_tct, group_style, add_quarter_ann_time_from_di_first_round, max_annealing_time_di_neutron_first_round)
        
        # Add diagonal breaks
        d = 0.02
        cut_kwargs = dict(color='#333333', clip_on=False, linewidth=2)

        # Left axis (ax1) - width ratio 0.3
        ax1.plot((1-d, 1+d), (-d, +d), transform=ax1.transAxes, **cut_kwargs)

        # Right axis (ax2) - width ratio 0.7
        width_ratio = 0.3 / 0.7  # scale x coordinates to match visual slope
        ax2.plot((-d*width_ratio, +d*width_ratio), (-d, +d), transform=ax2.transAxes, **cut_kwargs)
        
        ax1.grid(True)
        ax2.grid(True)
        
        # --- Custom legends for left and right axes ---

        for ax in (ax1, ax2) if split_x_axis else [ax]:
            ax.legend(markerscale=2, fontsize=4, frameon=True, fancybox=True, shadow=True, loc="best", borderaxespad=1.2)
        
        annealing_temp_label = annealing_temp[0]
        if annealing_temp_label == 20.0:
            annealing_temp_label = "20.5°C"
        elif annealing_temp_label == 40.0:
            annealing_temp_label = "40°C"
        elif annealing_temp_label == 60.0:
            annealing_temp_label = "60°C"
        # Labels
        ax1.set_xlabel("Annealing Time [min]", fontweight='bold')
        ax2.set_xlabel(f"Annealing Time [min] @ {annealing_temp_label}", fontweight='bold')
        if type_of_plot == "CC":
            ax1.set_ylabel(f"Charge Collection [fC] @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
        elif type_of_plot == "CCE":
            ax1.set_ylabel(f"CCE [%] @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
        elif type_of_plot == "alpha":
            ax1.set_ylabel(fr"$\alpha$ [A/cm] @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
        elif type_of_plot == "saturation voltage":
            ax1.set_ylabel(f"Saturation Voltage [V]", fontweight='bold')
            
            
        # --- Axis positioning ---
        for ax in (ax1, ax2):
            ax.spines['top'].set_visible(False)
        # Left plot: y-axis on left, ticks on bottom/left
        ax1.yaxis.set_ticks_position('left')
        ax1.xaxis.set_ticks_position('bottom')
        ax1.spines['right'].set_visible(False)

        # Right plot: y-axis on right, ticks on bottom/right
        ax2.yaxis.set_label_position("right")
        ax2.yaxis.tick_right()
        ax2.xaxis.set_ticks_position('bottom')

        # Optional: hide left spine of right plot
        ax2.spines['left'].set_visible(False)
        ax2.spines['right'].set_visible(False)
            
        ax.yaxis.set_ticks_position('none')

        # plt.title(f"{', '.join(campaigns)}: {type_of_plot} vs Annealing Time @ {abs(voltage):.0f} V", weight='bold')
        plt.title(f"{', '.join(campaigns)}: {type_of_plot} vs Annealing Time @ {_voltage_title_label(voltage)}", weight='bold')

        return fig, (ax1, ax2)
    
    else:
        fig, ax = plt.subplots(1, 1, figsize=(4.5, 3), dpi=300)

        plot_grouped_side(ax, df, type_of_plot, plot_saturation_voltage_from_tct, group_style, add_quarter_ann_time_from_di_first_round, max_annealing_time_di_neutron_first_round)
        
        # ax.set_facecolor('#FAFAFA')
        ax.grid(True)
        
        # Labels
        ax.set_xlabel("Annealing Time [min]", fontweight='bold')
        if type_of_plot == "CC":
            ax.set_ylabel(f"Charge Collection [fC] @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
        elif type_of_plot == "CCE":
            ax.set_ylabel(f"CCE [%] @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
        elif type_of_plot == "alpha":
            ax.set_ylabel(fr"$\alpha$ [A/cm] @ {_voltage_axis_suffix(voltage)}", fontweight='bold')
        elif type_of_plot == "saturation voltage":
            ax.set_ylabel(f"Saturation Voltage [V]", fontweight='bold')
            
        ax.legend(markerscale=2, fontsize=18, frameon=True, fancybox=True, shadow=True, loc="best", borderaxespad=1.2)
        
        # plt.title(f"{', '.join(campaigns)}: {type_of_plot} vs Annealing Time @ {abs(voltage):.0f} V", weight='bold')
        plt.title(f"{', '.join(campaigns)}: {type_of_plot} vs Annealing Time @ {_voltage_title_label(voltage)}", weight='bold')
        
        return fig, ax
    

def _process_saturation_voltage_di(df: pd.DataFrame, type_of_plot: str, sat_volt_cv_tct: str) -> pd.DataFrame:
    """
    Interpolate CC/CCE/alpha at sat_V_CV/TCT.
    Drops only groups where sat_V_CV/TCT is missing/invalid, keeps all others.
    """
    if df.empty:
        return df

    if type_of_plot == "alpha":
        y_col = "I"
    elif type_of_plot == "CC":
        y_col = "CC_corr"
    elif type_of_plot == "CCE":
        y_col = "CCEff_corr"
    else:
        return df

    if type_of_plot == "alpha" and "I" in df.columns:
        df = df.copy()
        df["I"] = df["I"].abs()

    group_cols = [
        "sensor_id",
        "fluence",
        "thickness",
        "campaign",
        "annealing_time",
        "annealing_temp",
        "corrected_annealing_time",
    ]
    group_cols = [col for col in group_cols if col in df.columns]

    interpolated_rows = []

    for _, group_df in df.groupby(group_cols, dropna=False):
        local_df = group_df.copy()

        if local_df.empty or "Voltage" not in local_df.columns or y_col not in local_df.columns:
            continue

        sat_candidate = local_df["sat_V"].iloc[0] if "sat_V" in local_df.columns else np.nan
        if pd.isna(sat_candidate) or float(sat_candidate) == 0.0:
            continue  # drop only this datapoint/group

        sat_v = abs(float(sat_candidate))

        local_df = local_df.sort_values("Voltage")
        voltages = local_df["Voltage"].abs().to_numpy(dtype=float)
        values = local_df[y_col].to_numpy(dtype=float)

        finite_mask = np.isfinite(voltages) & np.isfinite(values)
        voltages = voltages[finite_mask]
        values = values[finite_mask]

        if voltages.size < 2:
            continue

        interpolated_value = np.interp(sat_v, voltages, values)

        row = local_df.iloc[0].copy()
        row["Voltage"] = sat_v
        row[y_col] = interpolated_value
        interpolated_rows.append(row)

    if not interpolated_rows:
        return pd.DataFrame(columns=df.columns)

    return pd.DataFrame(interpolated_rows).reset_index(drop=True)


def plot_grouped_side(ax, df_side, type_of_plot, plot_saturation_voltage_from_tct, group_style, add_quarter_ann_time_from_di_first_round, max_annealing_time_di_neutron_first_round=0):
    # Sort sensors by fluence (ascending) and thickness (descending)
    # This determines the plotting order (lowest fluence first, highest thickness first for same fluence)
    sensor_order = (df_side.groupby("sensor_id")[["fluence", "thickness"]]
                    .first()
                    .sort_values(by=["fluence", "thickness"], ascending=[True, False])
                    .index.tolist())
    
    grouped = df_side.groupby("sensor_id")

    # First loop: error bars (in sorted order)
    for key in sensor_order:
        if key not in grouped.groups:
            continue
        group_df = grouped.get_group(key)
        style = group_style[key]
        color = style["color"]

        if type_of_plot == "alpha":
            y_data = group_df["alpha"]
            y_err = [abs(y_data - group_df["alpha_err1"]), abs(y_data - group_df["alpha_err2"])]
        elif type_of_plot == "CC":
            y_data = group_df["CC_corr"]
            y_err = y_data*0.05 # 5% error for everything considered
        elif type_of_plot == "CCE":
            y_data = group_df["CCEff_corr"]
            y_err = y_data*0.05 # 5% error for everything considered
        else:  # saturation voltage
            if plot_saturation_voltage_from_tct:
                y_col = "sat_V_TCT"
                y_err_down_col = "sat_V_err_down_TCT"
                y_err_up_col = "sat_V_err_up_TCT"
            else:
                y_col = "sat_V_CV"
                y_err_down_col = "sat_V_err_down_CV"
                y_err_up_col = "sat_V_err_up_CV"

            group_df = group_df.copy()
            # Drop NaNs and zeros in that column
            group_df = group_df.loc[group_df[y_col].notna() & (group_df[y_col] != 0)]

            if group_df.empty:
                continue

            y_data = group_df[y_col]
            
            # Calculate error bars + handle nan values as 0
            y_err_down = group_df[y_err_down_col].fillna(0)
            y_err_up = group_df[y_err_up_col].fillna(0)
            y_err = [y_err_down, y_err_up]
            
        if y_data.empty:
            continue
        
        # Uncertainty for corrected annealing time, prepare x_err
        x_err = [group_df["corr_ann_time_err_down"], group_df["corr_ann_time_err_up"]]
        
        if y_err is not None:
            ax.errorbar(group_df["corrected_annealing_time"], y_data, yerr=y_err, xerr=x_err, fmt="none", capsize=8, color=color, alpha=1)
        else:
            ax.errorbar(group_df["corrected_annealing_time"], y_data, xerr=x_err, fmt="none", capsize=8, color=color, alpha=1)

    # Second loop: markers/lines (in sorted order)
    for key in sensor_order:
        if key not in grouped.groups:
            continue
        group_df = grouped.get_group(key)
        style = group_style[key]
        color = style["color"]
        marker = style["marker"]
        fillstyle = style.get("fillstyle", "full")
        linestyle = style.get("linestyle", "--")

        if type_of_plot == "alpha":
            y_data = group_df["alpha"]
        elif type_of_plot == "CC":
            y_data = group_df["CC_corr"]
        elif type_of_plot == "CCE":
            y_data = group_df["CCEff_corr"]
        else:
            if plot_saturation_voltage_from_tct:
                y_col = "sat_V_TCT"
            else:
                y_col = "sat_V_CV"

            group_df = group_df.copy()
            # Drop NaNs and zeros in that column
            group_df = group_df.loc[group_df[y_col].notna() & (group_df[y_col] != 0)]

            if group_df.empty:
                continue

            y_data = group_df[y_col]
            
        if y_data.empty:
            continue
        
        sensor_id = group_df["sensor_id"].iloc[0]
        campaign = group_df["campaign"].iloc[0]
        fluence = group_df["fluence"].iloc[0]
        thickness = group_df["thickness"].iloc[0]
        
        if campaign == "DoubleIrrNeutron2025":
            label = f"{fluence:.1e}".replace("+", "") + fr", {thickness}μm (DI)"
        elif campaign == "DoubleIrrSRNeutron2025":
            label = f"{fluence:.1e}".replace("+", "") + fr", {thickness}μm (DI SR)"
        elif campaign == "HighFluenceIrrNeutron2023":
            label = f"{fluence:.1e}".replace("+", "") + fr", {thickness}μm (HF)"
        elif campaign == "LowFluenceIrrNeutron2025":
            label = f"{fluence:.1e}".replace("+", "") + fr", {thickness}μm (LF)"
        ax.plot(group_df["corrected_annealing_time"], y_data, linestyle=linestyle, marker=marker,
                    markersize=MARKERSIZE, color=color, fillstyle=fillstyle, label=label)

        # Add measurement limit line for saturation voltage plots
        if type_of_plot == "saturation voltage":
            # Add horizontal line at 900V
            ax.axhline(
                y=900, 
                color="#4D4D4D",  # Dark brown color
                linestyle="--", 
                linewidth=0.3, 
                alpha=0.6, 
                zorder=1
            )
            

def calculate_ratio_plot_data(
        df, 
        type_of_plot, 
        plot_saturation_voltage_from_tct, 
        sensor_groups, 
        group_style,
    ):
    """
    Calculate ratio of DI SR / HF values for matching sensors.
    For each DI SR annealing time, interpolate HF values if exact match doesn't exist.
    Only compares DoubleIrrSRNeutron2025 vs HighFluenceIrrNeutron2023 (excludes DoubleIrrNeutron2025).
    IMPORTANT: Comparisons are made WITHIN the same temperature only.
    """
    
    """ 
    Alpha:
    Index(['Voltage', 'I', 'I_err', 'sensor_id', 'fluence', 'thickness',
       'campaign', 'TCT_corr', 'annealing_time', 'annealing_temp',
       'corrected_annealing_time', 'corr_ann_time_err_up',
       'corr_ann_time_err_down', 'alpha', 'alpha_err1', 'alpha_err2'],
      dtype='object')
      
    Saturation Voltage:
    Index(['sat_V_CV', 'sat_V_err_down_CV', 'sat_V_err_up_CV', 'low_fit_start_CV',
       'low_fit_stop_CV', 'high_fit_start_CV', 'high_fit_stop_CV', 'sensor_id',
       'fluence', 'thickness', 'campaign', 'TCT_corr', 'annealing_time',
       'annealing_temp', 'corrected_annealing_time', 'corr_ann_time_err_up',
       'corr_ann_time_err_down'],
      dtype='object')
      
    CC/CCE:
    Index(['Voltage', 'CC_corr', 'CC_err_corr', 'CCEff_corr', 'CCEff_err_corr',
       'sensor_id', 'fluence', 'thickness', 'campaign', 'TCT_corr',
       'annealing_time', 'annealing_temp', 'corrected_annealing_time',
       'corr_ann_time_err_up', 'corr_ann_time_err_down'],
      dtype='object')
      
    Sensor Groups:
    e.g.  [{'di_sr': ['100264_SR_UR1'], 'di_first': ['100264_UR1'], 'hf': ['N8738_1_LR']}, {'di_sr': ['107954_SR_UR1'], 'di_first': ['107954_UR1'], 'hf': ['N8738_2_LL2']}]
    """
    # print(sensor_groups) 
    
    
    ratio_data_list = []
    
    for group_idx, sensor_group in enumerate(sensor_groups):
        # Get ONLY DI SR sensors (second round), exclude first round
        di_sr_sensors = sensor_group["di_sr"]
        hf_sensors = sensor_group["hf"]
        
        if not di_sr_sensors or not hf_sensors:
            continue  # Skip if no matching DI SR-HF pair
        
        # Process each DI SR sensor
        for di_sr_sensor in di_sr_sensors:
            di_sr_data = df[df["sensor_id"] == di_sr_sensor].copy()
            if di_sr_data.empty:
                continue
                
            di_sr_campaign = di_sr_data["campaign"].iloc[0]
            # Extract fluence and thickness for this sensor 
            di_sr_fluence = di_sr_data["fluence"].iloc[0]
            di_sr_thickness = di_sr_data["thickness"].iloc[0]
            
            # Get unique temperatures for this sensor
            di_sr_temperatures = di_sr_data["annealing_temp"].unique()
            
            # Get the corresponding y-column based on type_of_plot
            if type_of_plot == "alpha":
                y_col = "alpha"
                y_err_down_col = "alpha_err1" # absolute alpha value so relative error will be alpha - alpha_err1 = sigma
                y_err_up_col = "alpha_err2" # absolute alpha value so relative error will be alpha_err2 - alpha = sigma
            elif type_of_plot == "CC":
                y_col = "CC_corr"
                y_err_down_col = None # add 5% to hf_value later
                y_err_up_col = None # add 5% to hf_value later
            elif type_of_plot == "CCE":
                y_col = "CCEff_corr"
                y_err_down_col = None # add 5% to hf_value later
                y_err_up_col = None # add 5% to hf_value later
            elif type_of_plot == "saturation voltage":
                if plot_saturation_voltage_from_tct:
                    y_col = "sat_V_TCT"
                    y_err_down_col = "sat_V_err_down_TCT" # relative error so upper bound = sat_V_TCT + sat_V_err_down_TCT. Need interpolation for this
                    y_err_up_col = "sat_V_err_up_TCT" # relative error so lower bound = sat_V_TCT - sat_V_err_up_TCT. Need interpolation for this
                else:
                    y_col = "sat_V_CV"
                    y_err_down_col = "sat_V_err_down_CV" # relative error so upper bound - sat_V_CV = sat_V_err_down_CV. Need interpolation for this
                    y_err_up_col = "sat_V_err_up_CV" # relative error so sat_V_CV - lower bound = sat_V_err_up_CV. Need interpolation for this
            else:
                continue
            
            # Process each matching HF sensor
            for hf_sensor in hf_sensors:
                hf_data = df[df["sensor_id"] == hf_sensor].copy()
                if hf_data.empty:
                    continue
                
                hf_fluence = hf_data["fluence"].iloc[0]
                hf_thickness = hf_data["thickness"].iloc[0]
                
                 # === NEW: Loop through each temperature separately ===
                for temp in di_sr_temperatures:
                    # Filter data for this specific temperature
                    di_sr_data_temp = di_sr_data[di_sr_data["annealing_temp"] == temp].copy()
                    hf_data_temp = hf_data[hf_data["annealing_temp"] == temp].copy()
                    
                    if di_sr_data_temp.empty or hf_data_temp.empty:
                        continue  # Skip if either sensor doesn't have data at this temperature
                    
                    # Drop NaN values and zeros for this temperature
                    di_sr_data_clean = di_sr_data_temp[(di_sr_data_temp[y_col].notna()) & (di_sr_data_temp[y_col] != 0)].copy()
                    hf_data_clean = hf_data_temp[(hf_data_temp[y_col].notna()) & (hf_data_temp[y_col] != 0)].copy()
                    
                    
                    if len(hf_data_clean) < 2:
                        continue  # Need at least 2 points for interpolation
                    
                    # Create interpolation function for HF data
                    hf_interp = interp1d(
                        hf_data_clean["corrected_annealing_time"].values,
                        hf_data_clean[y_col].values,
                        kind="linear",
                        bounds_error=False,
                        fill_value=np.nan
                    )
                    
                    # Calculate ratios for each DI SR annealing time
                    for _, di_sr_row in di_sr_data_clean.iterrows():
                        di_sr_time = di_sr_row["corrected_annealing_time"]
                        di_sr_value = di_sr_row[y_col]
                        
                        # Interpolate HF value at this annealing time
                        hf_value = hf_interp(di_sr_time)

                        
                        if np.isnan(hf_value) or hf_value == 0:
                            continue  # Skip if interpolation failed or division by zero
                        
                        ratio = di_sr_value / hf_value
                        
                        ratio_err_up = None
                        ratio_err_down = None
                        
                        if type_of_plot == "alpha":
                            # Convert interpolated HF alpha back to current
                            hf_current_interpolated = hf_value * 0.2595 * hf_thickness * 1e-4 * hf_fluence / currentConvFactor(20, -20)
                            
                            # Calculate HF uncertainty bounds from the interpolated current
                            # alpha_err1 and alpha_err2 gives total value, so absolute error will be abs(alpha_err1 - alpha) and abs(alpha - alpha_err2). alpha_err1 is lower error bound and alpha_err2 is upper error bound.
                            hf_alpha_down = alpha_err1(
                                current=hf_current_interpolated,
                                thickness=hf_thickness,
                                fluence=hf_fluence,
                                T_target=20,
                            )
                            hf_alpha_up = alpha_err2(
                                current=hf_current_interpolated,
                                thickness=hf_thickness,
                                fluence=hf_fluence,
                                T_target=20,
                            )
                            # Compute absolute uncertainties
                            sigma_hf_up = hf_alpha_up - hf_value
                            sigma_hf_down = hf_value - hf_alpha_down
                            sigma_di_sr_up = di_sr_row[y_err_up_col] - di_sr_value
                            sigma_di_sr_down = di_sr_value - di_sr_row[y_err_down_col]

                            # Convert to relative
                            rel_hf_up = sigma_hf_up / hf_value
                            rel_hf_down = sigma_hf_down / hf_value
                            rel_di_sr_up = sigma_di_sr_up / di_sr_value
                            rel_di_sr_down = sigma_di_sr_down / di_sr_value

                            # Propagate ratio uncertainty
                            ratio_err_up = ratio * np.sqrt(rel_di_sr_up**2 + rel_hf_down**2)
                            ratio_err_down = ratio * np.sqrt(rel_di_sr_down**2 + rel_hf_up**2)
                            
                        elif type_of_plot == "saturation voltage":
                            hf_sat_V_upper_bound_interp = interp1d(
                                hf_data_clean["corrected_annealing_time"].values,
                                (hf_data_clean[y_col].values + hf_data_clean[y_err_up_col].values),
                                kind="linear",
                                bounds_error=False,
                                fill_value=np.nan
                            )
                            hf_sat_V_lower_bound_interp = interp1d(
                                hf_data_clean["corrected_annealing_time"].values,
                                (hf_data_clean[y_col].values - hf_data_clean[y_err_down_col].values),
                                kind="linear",
                                bounds_error=False,
                                fill_value=np.nan
                            )
                            
                            hf_sat_V_upper_bound = hf_sat_V_upper_bound_interp(di_sr_time)
                            hf_sat_V_lower_bound = hf_sat_V_lower_bound_interp(di_sr_time)

                            sigma_hf_up = hf_sat_V_upper_bound - hf_value
                            sigma_hf_down = hf_value - hf_sat_V_lower_bound
                            sigma_di_sr_up = di_sr_row[y_err_up_col]            # already absolute uncertainty
                            sigma_di_sr_down = di_sr_row[y_err_down_col]        # already absolute uncertainty
                            
                            rel_hf_up = sigma_hf_up / hf_value                  # relative uncertainty
                            rel_hf_down = sigma_hf_down / hf_value              # relative uncertainty
                            rel_di_sr_up = sigma_di_sr_up / di_sr_value         # relative uncertainty
                            rel_di_sr_down = sigma_di_sr_down / di_sr_value     # relative uncertainty
                            
                            # Propagate ratio uncertainty
                            ratio_err_up = ratio * np.sqrt(rel_di_sr_up**2 + rel_hf_down**2)
                            ratio_err_down = ratio * np.sqrt(rel_di_sr_down**2 + rel_hf_up**2)
                            
                        elif type_of_plot == "CC" or type_of_plot == "CCE":
                            # No need to interpolate since we just add 5% for both hf and di_sr --> symmetric uncertainty
                            ratio_err_up = ratio * np.sqrt(0.05**2 + 0.05**2)
                            ratio_err_down = ratio * np.sqrt(0.05**2 + 0.05**2)
                            
                        # Store ratio data
                        ratio_data_list.append({
                            "sensor_id": di_sr_sensor,
                            "hf_sensor": hf_sensor,
                            "campaign": di_sr_campaign,
                            "fluence": di_sr_fluence,
                            "thickness": di_sr_thickness,
                            "annealing_temp": temp,
                            "corrected_annealing_time": di_sr_time,
                            "ratio": ratio,
                            "ratio_err_up": ratio_err_up,
                            "ratio_err_down": ratio_err_down,
                            "di_sr_value": di_sr_value,
                            "hf_value": hf_value,
                            "color": group_style[di_sr_sensor]["color"],
                            "marker": group_style[di_sr_sensor]["marker"],
                            "linestyle": group_style[di_sr_sensor].get("linestyle", "--")
                        })
    
    return pd.DataFrame(ratio_data_list)

def get_base_sensor_name(sensor_id):
    """Extract base sensor name by removing _SR_ prefix if present"""
    if "_SR_" in sensor_id:
        return sensor_id.replace("_SR_", "_")
    return sensor_id

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

def _voltage_title_label(voltage):
    if voltage == "Saturation Voltage":
        return "Sat Volt."
    return f"{abs(float(voltage)):.0f}V"

def _voltage_axis_suffix(voltage):
    if voltage == "Saturation Voltage":
        return "Sat Volt."
    return f"{int(float(voltage))}V"