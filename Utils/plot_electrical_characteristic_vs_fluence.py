import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from matplotlib.colors import ListedColormap
import os
from config import RC_PLOT_STYLE, MARKERSIZE, LEGEND_SIZE, CUSTOM_COLORS, MARKERS, CAMPAIGN_TO_DISPLAY_NAME
from config import DEFAULT_DIR_DATA, UNCERTAINTY_THICKNESS, UNCERTAINTY_FLUENCE, FULLCHARGE_CC_DICT
from Utils.dataframe_helper import get_files, makeDataFrame_TCT, makeDataFrame_IV, makeDataFrameBare_IV
from Utils.conversion_helper import currentConvFactor, alpha_1_without_fluence, alpha_err1_without_fluence, alpha_err2_without_fluence
# from Utils.conversion_helper import alpha_1, alpha_err1, alpha_err2

def get_measurement_vs_fluence_plot(
    database,
    campaigns,
    measurement_type,
    thickness,
    annealing_time,
    annealing_temp,
    sensor_id,
    plot_type,  # "CC", "CCE", "alpha", or "saturation_voltage"
    voltage=None,
    logx=False,
    logy=False,
    I_tot=False,
    plot_from_TCT=False,
    use_saturation_voltage=False,
    sat_volt_cv_tct="CV"
):
    """
    Unified plotting function for CC, CCE, alpha, and saturation voltage vs fluence.
    
    Args:
        database: Database DataFrame
        campaigns: List of campaign names
        measurement_type: List of measurement types (e.g., ["onPCB"])
        thickness: List of thickness values
        voltage: Voltage value for filtering (for CC, CCE, alpha) or "Saturation Voltage"
        annealing_time: List of annealing times
        annealing_temp: List of annealing temperatures
        sensor_id: List of sensor IDs
        plot_type: "CC", "CCE", "alpha", or "saturation_voltage"
        logx: Use logarithmic x-axis
        logy: Use logarithmic y-axis (for alpha)
        I_tot: For alpha, use total current (bare measurements only)
        plot_from_TCT: For saturation voltage, plot from TCT (True) or CV (False)
        use_saturation_voltage: For alpha, use saturation voltage instead of fixed voltage
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
    chosen_annealing_time = annealing_time
    chosen_annealing_temp = annealing_temp
    chosen_sensor_id = sensor_id
    
    # Determine if we should use saturation voltage (for alpha plots)
    if plot_type in ("CC", "CCE", "alpha"):
        use_saturation_voltage = use_saturation_voltage or (voltage == "Saturation Voltage")
    
    # Ensure voltage is a scalar if it's not "Saturation Voltage"
    if voltage != None:
        if voltage != "Saturation Voltage" and isinstance(voltage, pd.Series):
            voltage = float(voltage.iloc[0])
        elif voltage != "Saturation Voltage":
            voltage = float(voltage)
    
    # Filter database based on plot type
    if plot_type == "saturation_voltage":
        if plot_from_TCT:
            sat_v_filter = (database["sat_V_TCT"].notna()) & (database["sat_V_TCT"] != 0)
        else:
            sat_v_filter = (database["sat_V_CV"].notna()) & (database["sat_V_CV"] != 0)
        
        df = database[
            (database.index.get_level_values("campaign").isin(chosen_campaigns)) &
            (database.index.get_level_values("thickness").isin(chosen_thickness)) &
            (database.index.get_level_values("annealing_time").isin(chosen_annealing_time)) &
            (database["type"].isin(chosen_measurement_type)) &
            (database["annealing_temp"].isin(chosen_annealing_temp)) &
            (database.index.get_level_values("sensor_id").isin(chosen_sensor_id)) &
            (database["Blacklisted"] == False) &
            sat_v_filter
        ]
        df = df.reset_index()
    else:
        # For CC, CCE, alpha - need to load files
        df = database[
            (database.index.get_level_values("campaign").isin(chosen_campaigns)) &
            (database.index.get_level_values("thickness").isin(chosen_thickness)) &
            (database.index.get_level_values("annealing_time").isin(chosen_annealing_time)) &
            (database["type"].isin(chosen_measurement_type)) &
            (database["annealing_temp"].isin(chosen_annealing_temp)) &
            (database.index.get_level_values("sensor_id").isin(chosen_sensor_id)) &
            (database["Blacklisted"] == False)
        ]
        df = df.reset_index()
        
        # Filter for saturation voltage if needed
        if plot_type in ("CC", "CCE", "alpha") and use_saturation_voltage:
            df = df[df.apply(lambda row: _row_has_valid_saturation_voltage(row, plot_type, sat_volt_cv_tct), axis=1)]
        
        # Determine file column
        if plot_type in ("CC", "CCE"):
            file_column = "file_TCT"
        elif plot_type == "alpha":
            file_column = "file_IV"
            if chosen_measurement_type != ["onPCB"] and not use_saturation_voltage:
                print("Only onPCB measurements are supported for alpha vs fluence!")
                return 0
        else:
            raise ValueError(f"Unknown plot_type: {plot_type}")
        
        # Load measurement data by iterating through database
        measurement_dataframes = []
        
        for idx, row in df.iterrows():
            file_end = row[file_column]
            if pd.isna(file_end) or file_end == "None":
                continue
            
            if not str(file_end).endswith(".csv") and plot_type in ("CC", "CCE"):
                continue
            if plot_type == "alpha" and chosen_measurement_type == ["bare"] and not str(file_end).endswith(".iv"):
                continue
            if plot_type == "alpha" and chosen_measurement_type == ["onPCB"] and not str(file_end).endswith(".csv"):
                continue
            
            full_path = os.path.join(DEFAULT_DIR_DATA, file_end)
            
            # Load appropriate DataFrame
            if plot_type in ("CC", "CCE"):
                data_df = makeDataFrame_TCT(full_path, row["TCT_corr"], row["thickness"])
            elif plot_type == "alpha":
                if chosen_measurement_type == ["bare"]:
                    data_df = makeDataFrameBare_IV(full_path)
                elif chosen_measurement_type == ["onPCB"]:
                    data_df = makeDataFrame_IV(full_path)
            
            if not isinstance(data_df, pd.DataFrame):
                continue
            
            # Add metadata columns
            for col in ["sensor_id", "fluence", "thickness", "campaign", 
                        "annealing_time", "annealing_temp"]:
                data_df[col] = row[col]
            
            if plot_type in ("CC", "CCE"):
                data_df["TCT_corr"] = row["TCT_corr"]
            
            # Add saturation voltage
            if plot_type in ("CC", "CCE", "alpha") and use_saturation_voltage:
                data_df["sat_V"] = row["sat_V_CV"] if sat_volt_cv_tct == "CV" else row["sat_V_TCT"]
            
            measurement_dataframes.append(data_df)
        
        if not measurement_dataframes:
            print(f"No {plot_type} measurements selected!")
            return 0
        
        # Concatenate all measurement DataFrames
        df = pd.concat(measurement_dataframes, ignore_index=True)
        
        # Process voltage filtering
        if plot_type in ("CC", "CCE", "alpha") and use_saturation_voltage:
            df = _process_saturation_voltage_measurement(df, plot_type, chosen_measurement_type, I_tot, sat_volt_cv_tct)
        elif plot_type == "alpha":
            # Filter by voltage
            if chosen_measurement_type == ["bare"]:
                df = df[df["Volt_nom"] == voltage].reset_index(drop=True)
            elif chosen_measurement_type == ["onPCB"]:
                df["I"] = df["I"].abs()
                df = df[df["Voltage"] == voltage].reset_index(drop=True)
        else:
            # Filter by voltage for CC/CCE
            df = df[df["Voltage"] == voltage].reset_index(drop=True)

    # Use to set xlim for CC when plotting full charge lines
    min_fluence = df["fluence"].min()
    max_fluence = df["fluence"].max()
    
    # Group by thickness and campaign
    grouped_df = df.groupby(["thickness", "campaign"])
    
    # Extract unique campaigns for marker assignment
    unique_campaigns = df["campaign"].unique()
    campaign_to_marker = {campaign: MARKERS[i % len(MARKERS)] for i, campaign in enumerate(unique_campaigns)}
    
    # Plot data
    if plot_type == "alpha":
        # For alpha, compute fits per thickness (across all campaigns) first
        thickness_fits = _compute_alpha_fits_per_thickness(df, chosen_thickness, logx, logy)
        
        # Track which thicknesses we've already plotted the fit for
        plotted_fits = set()
        
        for (thickness, campaign), group_df in grouped_df:
            color = _get_thickness_color(thickness)
            marker = campaign_to_marker[campaign]
            
            # Create label
            campaign_clean_name = CAMPAIGN_TO_DISPLAY_NAME[campaign]
            label = f"{campaign_clean_name} - {int(thickness)} µm"
            
            # Plot data points
            _plot_alpha_vs_fluence_group(
                ax, group_df, label, color, marker, thickness, 
                logx, logy, None  # Don't pass fit_data here
            )
            
            # Plot fit line once per thickness (for the first campaign encountered)
            if thickness not in plotted_fits and thickness in thickness_fits:
                fit_data = thickness_fits[thickness]
                if fit_data.get("success", False):
                    ax.plot(
                        fit_data["fit_x"], 
                        fit_data["fit_y"], 
                        linestyle="--", 
                        color=color, 
                        alpha=0.9,
                        zorder=1  # Behind data points
                    )
                    plotted_fits.add(thickness)
    else:
        # For other plot types, use existing logic
        for (thickness, campaign), group_df in grouped_df:
            color = _get_thickness_color(thickness)
            marker = campaign_to_marker[campaign]
            
            # Create label
            campaign_clean_name = CAMPAIGN_TO_DISPLAY_NAME[campaign]
            label = f"{campaign_clean_name} - {int(thickness)} µm"
            
            # Plot based on type
            if plot_type == "saturation_voltage":
                _plot_saturation_voltage_vs_fluence_group(
                    ax, group_df, plot_from_TCT, label, color, marker
                )
            elif plot_type == "CC":
                _plot_cc_vs_fluence_group(ax, group_df, label, color, marker)
            elif plot_type == "CCE":
                _plot_cce_vs_fluence_group(ax, group_df, label, color, marker)
    
    
    # Set axis scales
    if logx:
        ax.set_xscale("log")
    else:
        ax.set_xscale("linear")

    # Add special features
    if plot_type == "CC":
        _add_full_charge_lines(ax, chosen_thickness, logx, min_fluence, max_fluence)
    
    # Set labels and title
    if plot_type == "saturation_voltage":
        _set_saturation_voltage_vs_fluence_labels(ax, plot_from_TCT)
    elif plot_type == "CC":
        _set_cc_vs_fluence_labels(ax, campaigns, voltage)
    elif plot_type == "CCE":
        _set_cce_vs_fluence_labels(ax, campaigns, voltage)
    elif plot_type == "alpha":
        _set_alpha_vs_fluence_labels(ax, voltage, use_saturation_voltage)
    
    
    if logy and plot_type == "alpha":
        ax.set_yscale("log")
    else:
        ax.set_yscale("linear")
    
    # Add legend
    ax.legend(
        fontsize=LEGEND_SIZE,
        loc="lower left",
        bbox_to_anchor=(0, 0),
        frameon=True,
        borderaxespad=0.5
    )
    
    # Add alpha text box for alpha plots
    if plot_type == "alpha":
        _add_alpha_text_box(ax, df, chosen_thickness)
    
    return fig, ax


def _get_thickness_color(thickness):
    """Get color for thickness."""
    from config import get_thickness_color
    return get_thickness_color(thickness)


def _row_has_valid_saturation_voltage(row, plot_type, sat_volt_cv_tct):
    """Return True if a row has a usable CV saturation voltage for the requested plot type."""
    if plot_type in ("CC", "CCE", "alpha"):
        sat_v = row.get("sat_V_CV", np.nan) if sat_volt_cv_tct == "CV" else row.get("sat_V_TCT", np.nan)
        return pd.notna(sat_v) and float(sat_v) != 0.0

    return False

def _process_saturation_voltage_measurement(df, plot_type, measurement_type, I_tot, sat_volt_cv_tct):
    """
    Interpolate CC/CCE/alpha values at each measurement's CV/TCT saturation voltage.
    Rows/groups without sat_V_CV/TCT are skipped individually (others remain).
    """
    if df.empty:
        return df

    # Resolve per-plot columns
    if plot_type == "alpha":
        if measurement_type == ["bare"]:
            voltage_col = "Volt_nom"
            value_col = "I_tot" if I_tot else "I_pad"
        else:
            voltage_col = "Voltage"
            value_col = "I"
            df = df.copy()
            df["I"] = df["I"].abs()
    elif plot_type == "CC":
        voltage_col = "Voltage"
        value_col = "CC_corr"
    elif plot_type == "CCE":
        voltage_col = "Voltage"
        value_col = "CCEff_corr"
    else:
        return df

    group_cols = [
        "sensor_id",
        "fluence",
        "thickness",
        "campaign",
        "annealing_time",
        "annealing_temp",
    ]
    group_cols = [col for col in group_cols if col in df.columns]

    interpolated_rows = []
    for _, group_df in df.groupby(group_cols, dropna=False):
        local_df = group_df.copy()
        if local_df.empty or voltage_col not in local_df.columns or value_col not in local_df.columns:
            continue

        # CV/TCT saturation voltage
        sat_candidate = local_df["sat_V"].iloc[0] if "sat_V" in local_df.columns else np.nan
        if pd.isna(sat_candidate) or float(sat_candidate) == 0.0:
            continue

        sat_v = abs(float(sat_candidate))

        local_df = local_df.sort_values(voltage_col)
        voltages = local_df[voltage_col].abs().to_numpy(dtype=float)
        values = local_df[value_col].to_numpy(dtype=float)

        finite_mask = np.isfinite(voltages) & np.isfinite(values)
        voltages = voltages[finite_mask]
        values = values[finite_mask]

        if voltages.size < 2:
            continue

        interpolated_value = np.interp(sat_v, voltages, values)

        row = local_df.iloc[0].copy()
        row[voltage_col] = sat_v
        row[value_col] = interpolated_value
        interpolated_rows.append(row)

    if not interpolated_rows:
        return pd.DataFrame(columns=df.columns)

    return pd.DataFrame(interpolated_rows).reset_index(drop=True)

def _plot_saturation_voltage_vs_fluence_group(ax, group_df, plot_from_TCT, label, color, marker):
    """Helper function to plot saturation voltage vs fluence group."""
    if plot_from_TCT:
        y_col = "sat_V_TCT"
        group_df[y_col] = pd.to_numeric(group_df[y_col], errors="coerce")
    else:
        y_col = "sat_V_CV"
        group_df[y_col] = pd.to_numeric(group_df[y_col], errors="coerce")
    
    ax.plot(
        group_df["fluence"],
        group_df[y_col],
        label=label,
        linestyle="none",
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )
    
    ax.errorbar(
        group_df["fluence"],
        group_df[y_col],
        xerr=0.10 * group_df["fluence"],
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )


def _plot_cc_vs_fluence_group(ax, group_df, label, color, marker):
    """Helper function to plot CC vs fluence group."""
    ax.plot(
        group_df["fluence"],
        group_df["CC_corr"],
        label=label,
        linestyle="none",
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )
    
    ax.errorbar(
        group_df["fluence"],
        group_df["CC_corr"],
        xerr=0.10 * group_df["fluence"],
        yerr=group_df["CC_corr"] * 0.05,
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )


def _plot_cce_vs_fluence_group(ax, group_df, label, color, marker):
    """Helper function to plot CCE vs fluence group."""
    ax.plot(
        group_df["fluence"],
        group_df["CCEff_corr"],
        label=label,
        linestyle="none",
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )
    
    ax.errorbar(
        group_df["fluence"],
        group_df["CCEff_corr"],
        xerr=0.10 * group_df["fluence"],
        yerr=group_df["CCEff_corr"] * 0.05,
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )


def _plot_alpha_vs_fluence_group(ax, group_df, label, color, marker, thickness, logx, logy, fit_data=None):
    """Helper function to plot alpha vs fluence group."""
    # Determine current column
    if "I_pad" in group_df.columns or "I_tot" in group_df.columns:
        current_column = "I_pad" if "I_pad" in group_df.columns else "I_tot"
    else:
        current_column = "I"
    
    # Compute alpha values and errors for this group
    group_df = group_df.copy()  # Add .copy() to avoid SettingWithCopyWarning
    group_df["alpha"] = group_df[current_column].apply(
        lambda x: alpha_1_without_fluence(current=x, thickness=thickness, T_target=20)
    )
    group_df["alpha_err1"] = group_df[current_column].apply(
        lambda x: abs(alpha_err1_without_fluence(current=x, thickness=thickness, T_target=20))
    )
    group_df["alpha_err2"] = group_df[current_column].apply(
        lambda x: abs(alpha_err2_without_fluence(current=x, thickness=thickness, T_target=20))
    )
    
    # Plot error bars
    ax.errorbar(
        group_df["fluence"],
        group_df["alpha"],
        xerr=UNCERTAINTY_FLUENCE * group_df["fluence"],
        yerr=[
            np.abs(group_df["alpha_err1"] - group_df["alpha"]),
            np.abs(group_df["alpha"] - group_df["alpha_err2"])
        ],
        fmt="none",
        capsize=5,
        color=color,
        alpha=1
    )
    
    # Plot data points
    ax.plot(
        group_df["fluence"],
        group_df["alpha"],
        label=label,
        linestyle="none",
        marker=marker,
        markersize=MARKERSIZE,
        color=color
    )

def _add_full_charge_lines(ax, chosen_thickness, logx, min_fluence, max_fluence):
    """Add full charge reference lines for CC plots."""
    from config import get_thickness_color
    
    
    
    xlim = ax.get_xlim()
    
    x_fill = np.linspace(xlim[0], xlim[1], 100)
    
    for thickness in chosen_thickness:
        if thickness in FULLCHARGE_CC_DICT:
            fullcharge = FULLCHARGE_CC_DICT[thickness]
            color = get_thickness_color(thickness)
            
            ax.axhline(
                y=fullcharge,
                color=color,
                linestyle="--",
                linewidth=1.5,
                alpha=0.7,
                zorder=2
            )
            
            ax.fill_between(
                x_fill,
                fullcharge * 0.95,
                fullcharge * 1.05,
                color=color,
                alpha=0.15,
                zorder=1,
                linewidth=0
            )
    
    ax.set_xlim(xlim)


def _set_saturation_voltage_vs_fluence_labels(ax, plot_from_TCT):
    """Set labels for saturation voltage vs fluence plot."""
    if plot_from_TCT:
        ax.set_title("Saturation Voltage (TCT) vs Fluence", weight="bold")
    else:
        ax.set_title("Saturation Voltage (CV) vs Fluence", weight="bold")
    ax.set_xlabel("Fluence [n$_{eq}$/cm$^2$]")
    ax.set_ylabel("Saturation Voltage [V]")


def _set_cc_vs_fluence_labels(ax, campaigns, voltage):
    """Set labels for CC vs fluence plot."""
    if voltage == "Saturation Voltage":
        ax.set_title("CC vs Fluence @ Sat Voltage", weight="bold")
        ax.set_ylabel(f"Charge Collection [fC] @ Sat Volt.")
    else:
        ax.set_title(f"CC vs Fluence @ {abs(voltage):.0f} V", weight="bold")
        ax.set_ylabel(f"Charge Collection [fC] @ {abs(voltage):.0f}V")
    ax.set_xlabel("Fluence [n$_{eq}$/cm$^2$]")


def _set_cce_vs_fluence_labels(ax, campaigns, voltage):
    """Set labels for CCE vs fluence plot."""
    if voltage == "Saturation Voltage":
        ax.set_title("CCE vs Fluence @ Sat Voltage", weight="bold")
        ax.set_ylabel(f"CCE [%] @ Sat Volt.")
    else:
        ax.set_title(f"CCE vs Fluence @ {abs(voltage):.0f} V", weight="bold")
        ax.set_ylabel(f"CCE [%] @ {abs(voltage):.0f}V")
    ax.set_xlabel("Fluence [n$_{eq}$/cm$^2$]")


def _set_alpha_vs_fluence_labels(ax, voltage, use_saturation_voltage):
    """Set labels for alpha vs fluence plot."""
    if use_saturation_voltage:
        ax.set_title("Current Volume Normalization @ Saturation Voltage", weight="bold")
        ax.set_ylabel("I(Saturation Voltage)/Volume [A/cm$^3$]")
    else:
        ax.set_title(f"Current Volume Normalization @ {abs(voltage):.0f} V", weight="bold")
        ax.set_ylabel(f"I({int(voltage)}V)/Volume [A/cm$^3$]")
    ax.set_xlabel("Fluence [n$_{eq}$/cm$^2$]")


def _compute_alpha_fits_per_thickness(df, chosen_thickness, logx, logy):
    """Compute alpha fits per thickness across all campaigns."""
    from scipy.stats import linregress
    
    thickness_fits = {}
    
    # Determine current column
    if "I_pad" in df.columns or "I_tot" in df.columns:
        current_column = "I_pad" if "I_pad" in df.columns else "I_tot"
    else:
        current_column = "I"
    
    for thickness in chosen_thickness:
        thickness_df = df[df["thickness"] == thickness].copy()  # Add .copy() here
        if thickness_df.empty:
            continue
        
        # Compute alpha values if not already computed
        if "alpha" not in thickness_df.columns:
            thickness_df["alpha"] = thickness_df[current_column].apply(
                lambda x: alpha_1_without_fluence(current=x, thickness=thickness, T_target=20)
            )
        
        try:
            slope_linear, intercept_linear, _, _, _ = linregress(
                thickness_df["fluence"], thickness_df["alpha"]
            )
            
            if logx and logy:
                log_fluence = np.log10(thickness_df["fluence"])
                log_alpha = np.log10(thickness_df["alpha"])
                slope_log, intercept_log, _, _, _ = linregress(log_fluence, log_alpha)
                
                power_coeff = 10 ** intercept_log
                fit_x = np.logspace(
                    np.log10(min(thickness_df["fluence"])), 
                    np.log10(max(thickness_df["fluence"])), 
                    100
                )
                fit_y = power_coeff * fit_x ** slope_log
            else:
                fit_x = np.linspace(
                    min(thickness_df["fluence"]), 
                    max(thickness_df["fluence"]), 
                    100
                )
                fit_y = slope_linear * fit_x + intercept_linear
            
            thickness_fits[thickness] = {
                "fit_x": fit_x,
                "fit_y": fit_y,
                "slope": slope_linear,
                "intercept": intercept_linear,
                "success": True
            }
        except:
            thickness_fits[thickness] = {"success": False}
    
    return thickness_fits


def _add_alpha_text_box(ax, df, chosen_thickness):
    """Add text box with alpha values for alpha plots."""
    from scipy.stats import linregress
    
    text_content_alpha = ""
    
    for thickness in chosen_thickness:
        thickness_df = df[df["thickness"] == thickness].copy()  # Add .copy() here
        if thickness_df.empty:
            continue
        
        # Determine current column
        if "I_pad" in thickness_df.columns or "I_tot" in thickness_df.columns:
            current_column = "I_pad" if "I_pad" in thickness_df.columns else "I_tot"
        else:
            current_column = "I"
        
        # Compute alpha if not already computed
        if "alpha" not in thickness_df.columns:
            thickness_df["alpha"] = thickness_df[current_column].apply(
                lambda x: alpha_1_without_fluence(current=x, thickness=thickness, T_target=20)
            )
        
        try:
            slope_linear, intercept_linear, _, _, _ = linregress(thickness_df["fluence"], thickness_df["alpha"])
            text_content_alpha += r"$\alpha_{" + str(int(thickness)) + r"}$" + f" = {slope_linear:.2e} A/cm\n"
        except:
            text_content_alpha += r"$\alpha_{" + str(int(thickness)) + r"}$" + f" = N/A\n"
    
    text_content_alpha = text_content_alpha.rstrip()
    
    if text_content_alpha:
        ax.text(
            0.95,
            0.1,
            text_content_alpha,
            transform=ax.transAxes,
            fontsize=8.4,
            verticalalignment="bottom",
            horizontalalignment="right",
            bbox=dict(
                facecolor="white",
                edgecolor="black",
                alpha=0.8
            )
        )
