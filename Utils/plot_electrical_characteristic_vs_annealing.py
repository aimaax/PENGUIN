import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import ListedColormap
import os
from config import RC_PLOT_STYLE, MARKERSIZE, LEGEND_SIZE, CUSTOM_COLORS, MARKERS
from config import DEFAULT_DIR_DATA
from Utils.dataframe_helper import get_files, makeDataFrame_TCT, makeDataFrame_IV
from Utils.conversion_helper import convert_annealing_time, currentConvFactor
from Utils.conversion_helper import alpha_1, alpha_err1, alpha_err2
from Utils.conversion_helper import adjust_color_brightness


def get_measurement_vs_annealing_plot(
    database, 
    campaigns, 
    measurement_type, 
    thickness, 
    annealing_temp, 
    sensor_id, 
    plot_type,  # "CC", "CCE", "alpha", or "saturation_voltage"
    voltage=None, 
    logx=False, 
    plot_from_TCT=False,
    plot_from_CV_and_TCT=False,
    use_saturation_voltage=False,
    sat_volt_cv_tct="CV"
):
    """
    Unified plotting function for CC, CCE, alpha, and saturation voltage vs annealing time.
    
    Args:
        database: Database DataFrame
        campaigns: List of campaign names
        measurement_type: List of measurement types (e.g., ["onPCB"])
        thickness: List of thickness values
        annealing_temp: List of annealing temperatures
        sensor_id: List of sensor IDs
        plot_type: "CC", "CCE", "alpha", or "saturation_voltage"
        voltage: Voltage value for filtering (for CC, CCE, alpha)
        logx: Use logarithmic x-axis
        plot_from_TCT: For saturation voltage, plot from TCT (True) or CV (False)
        plot_from_CV_and_TCT: For saturation voltage, plot both CV and TCT
    """
    plt.rcParams.update(RC_PLOT_STYLE)
    fig, ax = plt.subplots(dpi=300)
    ax.grid()
    
    pd.set_option("display.max.rows", None)
    pd.set_option("display.max.columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)
    
    chosen_campaigns = campaigns
    chosen_measurement_type = measurement_type
    chosen_thickness = [int(t) for t in thickness]
    chosen_annealing_temp = [float(t) for t in annealing_temp]
    chosen_sensor_id = sensor_id

    if plot_type in ("CC", "CCE", "alpha"):
        use_saturation_voltage = use_saturation_voltage or (voltage == "Saturation Voltage")

    df = database.reset_index()

    # Convert annealing times
    df["corrected_annealing_time"] = df["corrected_annealing_time"].apply(convert_annealing_time)
    df["corr_ann_time_err_down"] = df["corr_ann_time_err_down"].apply(convert_annealing_time)
    df["corr_ann_time_err_up"] = df["corr_ann_time_err_up"].apply(convert_annealing_time)
    
    # Sort dataframe
    df = df.sort_values(
        by=["fluence", "thickness", "corrected_annealing_time"],
        ascending=[True, False, True]
    )

    
    # Filter database based on plot type
    if plot_type == "saturation_voltage":
        if plot_from_CV_and_TCT:
            df = df[
                (df["campaign"].isin(chosen_campaigns)) &
                (df["thickness"].isin(chosen_thickness)) &
                (df["sensor_id"].isin(chosen_sensor_id)) &
                (df["annealing_temp"].isin(chosen_annealing_temp)) &
                (df["type"].isin(chosen_measurement_type)) &
                (df["Blacklisted"] == False) &
                ((df["sat_V_TCT"] != 0) | (df["sat_V_CV"] != 0))
            ]
        else:
            df = df[
                (df["campaign"].isin(chosen_campaigns)) &
                (df["thickness"].isin(chosen_thickness)) &
                (df["sensor_id"].isin(chosen_sensor_id)) &
                (df["annealing_temp"].isin(chosen_annealing_temp)) &
                (df["type"].isin(chosen_measurement_type)) &
                (df["Blacklisted"] == False) &
                (df["sat_V_TCT"] != 0 if plot_from_TCT else df["sat_V_CV"] != 0)
            ]
    else:
        # For CC, CCE, alpha - need to load files
        df = df[
            (df["campaign"].isin(chosen_campaigns)) &
            (df["thickness"].isin(chosen_thickness)) &
            (df["sensor_id"].isin(chosen_sensor_id)) &
            (df["annealing_temp"].isin(chosen_annealing_temp)) &
            (df["type"].isin(chosen_measurement_type)) &
            (df["Blacklisted"] == False)
        ]

        if plot_type in ("CC", "CCE", "alpha") and use_saturation_voltage:
            df = df[df.apply(lambda row: _row_has_valid_saturation_voltage_annealing(row, plot_type, sat_volt_cv_tct), axis=1)]
        
        # Determine file column
        if plot_type in ("CC", "CCE"):
            file_column = "file_TCT"
        elif plot_type == "alpha":
            file_column = "file_IV"
            if not chosen_measurement_type == ["onPCB"]:
                print("Only onPCB measurements are supported for alpha vs annealing time!")
                return 0
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")
        
        # Load measurement data by iterating through database
        measurement_dataframes = []
        
        for idx, row in df.iterrows():
            file_end = row[file_column]
            if pd.isna(file_end) or file_end == "None":
                continue
            
            if not str(file_end).endswith(".csv"):
                continue
            
            full_path = os.path.join(DEFAULT_DIR_DATA, file_end)
            
            # Load appropriate DataFrame
            if plot_type in ("CC", "CCE"):
                data_df = makeDataFrame_TCT(full_path, row["TCT_corr"], row["thickness"])
            elif plot_type == "alpha":
                data_df = makeDataFrame_IV(full_path)
            
            if not isinstance(data_df, pd.DataFrame):
                continue
            
            # Add metadata columns
            for col in ["sensor_id", "fluence", "thickness", "campaign", 
                        "corrected_annealing_time", "annealing_temp", "corr_ann_time_err_down", "corr_ann_time_err_up"]:
                data_df[col] = row[col]
            
            if plot_type in ("CC", "CCE"):
                data_df["TCT_corr"] = row["TCT_corr"]

            if use_saturation_voltage and plot_type in ("CC", "CCE", "alpha"):
                data_df["sat_V"] = row.get("sat_V_CV", np.nan) if sat_volt_cv_tct == "CV" else row.get("sat_V_TCT", np.nan)
            
            measurement_dataframes.append(data_df)
        
        if not measurement_dataframes:
            print(f"No {plot_type} measurements selected!")
            return 0
        
        # Concatenate all measurement DataFrames
        df = pd.concat(measurement_dataframes, ignore_index=True)
        
        if use_saturation_voltage and plot_type in ("CC", "CCE", "alpha"):
            df = _process_saturation_voltage_vs_annealing(df=df, plot_type=plot_type, sat_volt_cv_tct=sat_volt_cv_tct)
        else:
            df = df[df["Voltage"] == voltage]

        # Process alpha-specific calculations
        if plot_type == "alpha":
            df["I"] = df["I"].abs()  # Take absolute value
            df["alpha"] = df.apply(
                lambda row: alpha_1(
                    current=row["I"], 
                    thickness=row["thickness"], 
                    fluence=row["fluence"], 
                    T_target=20
                ),
                axis=1
            )
            df["alpha_err1"] = df.apply(
                lambda row: abs(alpha_err1(
                    current=row["I"], 
                    thickness=row["thickness"], 
                    fluence=row["fluence"], 
                    T_target=20
                )),
                axis=1
            )
            df["alpha_err2"] = df.apply(
                lambda row: abs(alpha_err2(
                    current=row["I"], 
                    thickness=row["thickness"], 
                    fluence=row["fluence"], 
                    T_target=20
                )),
                axis=1
            )
    
    # Group by fluence and thickness
    grouped_df_fluence_thickness = df.groupby(["fluence", "thickness", "sensor_id"])
    
    # Create colormap and assign styles
    colors = ListedColormap(CUSTOM_COLORS)
    group_keys = list(grouped_df_fluence_thickness.groups.keys())
    
    group_style = {}
    for i, key in enumerate(group_keys):
        group_style[key] = {
            "color": colors(i % len(CUSTOM_COLORS)),
            "marker": MARKERS[i % len(MARKERS)]
        }
    
    # Plot data
    for key, group_df in grouped_df_fluence_thickness:
        fluence_val, thickness_val, sensor_id_val = key
        style = group_style[key]
        color = style["color"]
        marker = style["marker"]
        
        # Create label
        fluence_str = f"{fluence_val:.1e}".replace("e+", "e")
        # label = f"{fluence_str}, {thickness_val}μm, {sensor_id_val}"
        label = f"{fluence_str}, {thickness_val}μm"
        
        # Plot based on type
        if plot_type == "saturation_voltage":
            _plot_saturation_voltage_group(
                ax, group_df, plot_from_TCT, plot_from_CV_and_TCT, 
                label, color, marker
            )
        elif plot_type == "CC":
            _plot_cc_group(ax, group_df, label, color, marker)
        elif plot_type == "CCE":
            _plot_cce_group(ax, group_df, label, color, marker)
        elif plot_type == "alpha":
            _plot_alpha_group(ax, group_df, label, color, marker)
    
    # Set labels and title
    if plot_type == "saturation_voltage":
        _set_saturation_voltage_labels(ax, chosen_campaigns, plot_from_TCT, plot_from_CV_and_TCT, logx, chosen_annealing_temp)
    elif plot_type == "CC":
        _set_cc_labels(ax, chosen_campaigns, voltage, chosen_annealing_temp)
    elif plot_type == "CCE":
        _set_cce_labels(ax, chosen_campaigns, voltage, chosen_annealing_temp)
    elif plot_type == "alpha":
        _set_alpha_labels(ax, voltage, chosen_annealing_temp)
    
    # Set x-axis scale
    if logx:
        ax.set_xscale("log")
    else:
        ax.set_xscale("linear")
    
    # Add legend
    ax.legend(
        fontsize=LEGEND_SIZE,
        loc="lower left",
        bbox_to_anchor=(0, 0),
        frameon=True,
        borderaxespad=0.5
    )
    
    return fig, ax


def _plot_saturation_voltage_group(ax, group_df, plot_from_TCT, plot_from_CV_and_TCT, label, color, marker):
    """Helper function to plot saturation voltage group."""
    
    if plot_from_CV_and_TCT:
        # Plot CV data
        group_df_cv = group_df[group_df["sat_V_CV"] != 0].copy()
        if not group_df_cv.empty:
            label_cv = f"{label} (CV @ 2kHz)"
            y_err_down_cv = group_df_cv["sat_V_err_down_CV"]
            y_err_up_cv = group_df_cv["sat_V_err_up_CV"]
            y_err_cv = [y_err_down_cv, y_err_up_cv]
            x_err_cv = [group_df_cv["corr_ann_time_err_down"], group_df_cv["corr_ann_time_err_up"]]
            
            ax.errorbar(
                group_df_cv["corrected_annealing_time"],
                group_df_cv["sat_V_CV"],
                yerr=y_err_cv,
                xerr=x_err_cv,
                fmt="none",
                capsize=3,
                color=adjust_color_brightness(color, 1.1),
                alpha=1
            )
            
            ax.plot(
                group_df_cv["corrected_annealing_time"],
                group_df_cv["sat_V_CV"],
                label=label_cv,
                linestyle=(0, (3, 2)),
                marker="o",
                markersize=MARKERSIZE,
                fillstyle="full",
                color=adjust_color_brightness(color, 1.1)
            )
        
        # Plot TCT data
        group_df_tct = group_df[group_df["sat_V_TCT"] != 0].copy()
        if not group_df_tct.empty:
            label_tct = f"{label} (TCT)"
            y_err_down_tct = pd.to_numeric(group_df_tct["sat_V_err_down_TCT"], errors="coerce").fillna(0)
            y_err_up_tct = pd.to_numeric(group_df_tct["sat_V_err_up_TCT"], errors="coerce").fillna(0)
            y_err_tct = [y_err_down_tct, y_err_up_tct]
            x_err_tct = [group_df_tct["corr_ann_time_err_down"], group_df_tct["corr_ann_time_err_up"]]
            
            ax.errorbar(
                group_df_tct["corrected_annealing_time"],
                group_df_tct["sat_V_TCT"],
                yerr=y_err_tct,
                xerr=x_err_tct,
                fmt="none",
                capsize=3,
                color=adjust_color_brightness(color, 0.6),
                alpha=1
            )
            
            ax.plot(
                group_df_tct["corrected_annealing_time"],
                group_df_tct["sat_V_TCT"],
                label=label_tct,
                linestyle=(0, (1, 3)),
                marker="x",
                markersize=MARKERSIZE,
                fillstyle="full",
                color=adjust_color_brightness(color, 0.6)
            )
    elif plot_from_TCT:
        label = f"{label} (TCT)"
        y_err_down = pd.to_numeric(group_df["sat_V_err_down_TCT"], errors="coerce").fillna(0)
        y_err_up = pd.to_numeric(group_df["sat_V_err_up_TCT"], errors="coerce").fillna(0)
        y_err = [y_err_down, y_err_up]
        x_err = [group_df["corr_ann_time_err_down"], group_df["corr_ann_time_err_up"]]
        
        ax.errorbar(
            group_df["corrected_annealing_time"],
            group_df["sat_V_TCT"],
            yerr=y_err,
            xerr=x_err,
            fmt="none",
            capsize=3,
            color=color,
            alpha=1
        )
        
        ax.plot(
            group_df["corrected_annealing_time"],
            group_df["sat_V_TCT"],
            label=label,
            linestyle="--",
            marker=marker,
            markersize=MARKERSIZE,
            color=color
        )
    else:
        label = f"{label} (CV @ 2kHz)"
        y_err_down = pd.to_numeric(group_df["sat_V_err_down_CV"], errors="coerce").fillna(0)
        y_err_up = pd.to_numeric(group_df["sat_V_err_up_CV"], errors="coerce").fillna(0)
        y_err = [y_err_down, y_err_up]
        x_err = [group_df["corr_ann_time_err_down"], group_df["corr_ann_time_err_up"]]
        
        ax.errorbar(
            group_df["corrected_annealing_time"],
            group_df["sat_V_CV"],
            yerr=y_err,
            xerr=x_err,
            fmt="none",
            capsize=3,
            color=color,
            alpha=1
        )
        
        ax.plot(
            group_df["corrected_annealing_time"],
            group_df["sat_V_CV"],
            label=label,
            linestyle="--",
            marker=marker,
            markersize=MARKERSIZE,
            color=color
        )


def _plot_cc_group(ax, group_df, label, color, marker):
    """Helper function to plot CC group."""
    
    group_df = group_df.copy()

    ax.errorbar(
        group_df["corrected_annealing_time"],
        group_df["CC_corr"],
        yerr=group_df["CC_corr"] * 0.05,
        xerr=[group_df["corr_ann_time_err_down"], group_df["corr_ann_time_err_up"]],
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )
    
    ax.plot(
        group_df["corrected_annealing_time"],
        group_df["CC_corr"],
        label=label,
        linestyle=(0, (3, 2)),
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )
    
    


def _plot_cce_group(ax, group_df, label, color, marker):
    """Helper function to plot CCE group."""
    
    group_df = group_df.copy()
    
    ax.errorbar(
        group_df["corrected_annealing_time"],
        group_df["CCEff_corr"],
        yerr=group_df["CCEff_corr"] * 0.05,
        xerr=[group_df["corr_ann_time_err_down"], group_df["corr_ann_time_err_up"]],
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )
    ax.plot(
        group_df["corrected_annealing_time"],
        group_df["CCEff_corr"],
        label=label,
        linestyle=(0, (3, 2)),
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )
    

def _plot_alpha_group(ax, group_df, label, color, marker):
    """Helper function to plot alpha group."""
    
    # Plot error bars first
    ax.errorbar(
        group_df["corrected_annealing_time"],
        group_df["alpha"],
        yerr=[
            abs((group_df["alpha"] - group_df["alpha_err1"])),
            abs((group_df["alpha"] - group_df["alpha_err2"]))
        ],
        xerr=[group_df["corr_ann_time_err_down"], group_df["corr_ann_time_err_up"]],
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )
    
    # Plot data points
    ax.plot(
        group_df["corrected_annealing_time"],
        group_df["alpha"],
        label=label,
        linestyle=(0, (3, 2)),
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )


def _set_saturation_voltage_labels(ax, campaigns, plot_from_TCT, plot_from_CV_and_TCT, logx, annealing_temp):
    """Set labels for saturation voltage plot."""
    if plot_from_CV_and_TCT:
        title_suffix = "Saturation Voltage (CV & TCT) vs Annealing Time"
    elif plot_from_TCT:
        title_suffix = "Saturation Voltage (TCT) vs Annealing Time"
    else:
        title_suffix = "Saturation Voltage (CV) vs Annealing Time"
    
    ax.set_title(f"{', '.join(campaigns)}: {title_suffix}", weight="bold")
    ax.set_xlabel(f"Annealing Time [min] @ {_get_annealing_temp_label(annealing_temp)}", fontweight="bold")
    ax.set_ylabel("Saturation Voltage [V]", fontweight="bold")


def _set_cc_labels(ax, campaigns, voltage, annealing_temp):
    """Set labels for CC plot."""
    if voltage == "Saturation Voltage":
        ax.set_title(f"{', '.join(campaigns)}: CC vs Annealing Time @ Sat Voltage", weight="bold")
        ax.set_ylabel(f"Charge Collection [fC] @ Sat Volt.")
    else:
        ax.set_title(f"{', '.join(campaigns)}: CC vs Annealing Time @ {abs(voltage):.0f} V", weight="bold")
        ax.set_ylabel(f"Charge Collection [fC] @ {abs(voltage):.0f}V")
    ax.set_xlabel(f"Annealing Time [min] @ {_get_annealing_temp_label(annealing_temp)}", fontweight="bold")


def _set_cce_labels(ax, campaigns, voltage, annealing_temp):
    """Set labels for CCE plot."""
    if voltage == "Saturation Voltage":
        ax.set_title(f"{', '.join(campaigns)}: CCE vs Annealing Time @ Sat Voltage", weight="bold")
        ax.set_ylabel(f"CCE [%] @ Sat Volt.")
    else:
        ax.set_title(f"{', '.join(campaigns)}: CCE vs Annealing Time @ {abs(voltage):.0f} V", weight="bold")
        ax.set_ylabel(f"CCE [%] @ {abs(voltage):.0f}V")
    ax.set_xlabel(f"Annealing Time [min] @ {_get_annealing_temp_label(annealing_temp)}", fontweight="bold")


def _set_alpha_labels(ax, voltage, annealing_temp):
    """Set labels for alpha plot."""
    if voltage == "Saturation Voltage":
        ax.set_title("Current Volume Normalization vs Annealing Time @ Saturation Voltage", weight="bold")
        ax.set_ylabel("I(Sat Volt.)/Volume [A/cm$^3$]")
    else:
        ax.set_title(f"Current Volume Normalization vs Annealing Time @ {abs(voltage):.0f} V", weight="bold")
        ax.set_ylabel(f"I({int(voltage)}V)/Volume [A/cm$^3$]")

    ax.set_xlabel(f"Annealing Time [min] @ {_get_annealing_temp_label(annealing_temp)}", fontweight="bold")

def _get_annealing_temp_label(annealing_temp):
    annealing_temp_label = annealing_temp[0]
    if annealing_temp_label == 20.0:
        return "20.5°C"
    elif annealing_temp_label == 40.0:
        return "40°C"
    elif annealing_temp_label == 60.0:
        return "60°C"
    else:
        return f"{annealing_temp_label}°C"


def _row_has_valid_saturation_voltage_annealing(row, plot_type, sat_volt_cv_tct):
    """Return True if a row has a usable CV saturation voltage for the requested plot type."""
    if plot_type in ("CC", "CCE", "alpha"):
        sat_v = row.get("sat_V_CV", np.nan) if sat_volt_cv_tct == "CV" else row.get("sat_V_TCT", np.nan)
        return pd.notna(sat_v) and float(sat_v) != 0.0

    return False


def _process_saturation_voltage_vs_annealing(df: pd.DataFrame, plot_type: str, sat_volt_cv_tct: str) -> pd.DataFrame:
    """
    Interpolate measurement at each sensor's CV saturation voltage.
    Rows/groups without sat_V_CV/TCT are skipped individually (others remain).
    """
    if df.empty:
        return df

    if plot_type == "alpha":
        y_col = "I"
    elif plot_type == "CC":
        y_col = "CC_corr"
    elif plot_type == "CCE":
        y_col = "CCEff_corr"
    else:
        return df

    if plot_type == "alpha" and "I" in df.columns:
        df = df.copy()
        df["I"] = df["I"].abs()

    group_cols = [
        "sensor_id",
        "thickness",
        "campaign",
        "corrected_annealing_time",
        "annealing_temp",
        "fluence",
    ]
    group_cols = [col for col in group_cols if col in df.columns]

    interpolated_rows = []
    for _, group_df in df.groupby(group_cols, dropna=False):
        local_df = group_df.copy()
        if local_df.empty or "Voltage" not in local_df.columns or y_col not in local_df.columns:
            continue

        # CV/TCT saturation voltage
        sat_candidate = local_df["sat_V"].iloc[0] if "sat_V" in local_df.columns else np.nan
        if pd.isna(sat_candidate) or float(sat_candidate) == 0.0:
            continue

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