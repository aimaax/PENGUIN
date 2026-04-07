import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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
    "axes.font.size": 10,
    "axes.textonaxis.size": 6.5,
    "axes.textbox.size": 8,
    "axes.border.width": 1,
    "axes.tick.major.label.size": 9,
    "axes.tick.major.size": 4,
    "axes.tick.major.width": 1,
    "axes.tick.minor.size": 2,
    "axes.tick.minor.width": 1,
    "marker.size": 4,
    "line.width": 1,
    "legend.size": 3,
}

# Endcap assumptions from config
END_INV_CAPACITANCE_2_ASSUMPTION = {
    "300": 1.187e22,
    "200": 5.426e21,
    "120": 1.952e21
}

END_CAP_ERROR_UP = 0.03  # 3% error up
END_CAP_ERROR_DOWN = 0.02  # 2% error down

# Apply RC_PLOT_STYLE first
plt.rcParams.update(RC_PLOT_STYLE)

# File paths
file_300um = "UIRAD_Measurements/IVCV_onPCB/300um_UIRAD/300um_UIRAD_CV.csv"
file_200um = "UIRAD_Measurements/IVCV_onPCB/200um_UIRAD/200um_UIRAD_CV.csv"
file_120um = "UIRAD_Measurements/IVCV_onPCB/120um_UIRAD/120um_UIRAD_CV.csv"

# Read CSV files
df_300um = pd.read_csv(file_300um, delimiter=";")
df_200um = pd.read_csv(file_200um, delimiter=";")
df_120um = pd.read_csv(file_120um, delimiter=";")

# Open correction value
open_correction = 5.0276597281666e-11

# Take absolute value of voltage and add as new column
df_300um["voltage_abs"] = abs(df_300um["real voltage (V)"])
df_200um["voltage_abs"] = abs(df_200um["real voltage (V)"])
df_120um["voltage_abs"] = abs(df_120um["real voltage (V)"])

# Filter data for voltage range 0 to 500V
df_300um = df_300um[(df_300um["voltage_abs"] >= 0) & (df_300um["voltage_abs"] <= 500)].copy()
df_200um = df_200um[(df_200um["voltage_abs"] >= 0) & (df_200um["voltage_abs"] <= 500)].copy()
df_120um = df_120um[(df_120um["voltage_abs"] >= 0) & (df_120um["voltage_abs"] <= 500)].copy()

# Sort by voltage (ascending, from 0 to 500)
df_300um = df_300um.sort_values("voltage_abs")
df_200um = df_200um.sort_values("voltage_abs")
df_120um = df_120um.sort_values("voltage_abs")

# Apply open correction to serial capacitance
df_300um["ser_cap_corrected"] = abs(df_300um["serial capacitance"]) - open_correction
df_200um["ser_cap_corrected"] = abs(df_200um["serial capacitance"]) - open_correction
df_120um["ser_cap_corrected"] = abs(df_120um["serial capacitance"]) - open_correction

# Calculate 1/C^2 for corrected capacitance
df_300um["inv_c2"] = 1 / (df_300um["ser_cap_corrected"]**2)
df_200um["inv_c2"] = 1 / (df_200um["ser_cap_corrected"]**2)
df_120um["inv_c2"] = 1 / (df_120um["ser_cap_corrected"]**2)

# Colors from config.py
colors = ["#3f90da", "#f1a90e", "#bd1f01"]  # Blue, Yellow, Red

# Create single plot for 1/C^2
fig, ax = plt.subplots(1, 1, figsize=(4, 3), dpi=300)

# Plot 1/C^2 data
ax.plot(df_300um["voltage_abs"], df_300um["inv_c2"], 
        marker="o", color=colors[0], 
        linewidth=1,
        markersize=3, 
        label="300μm")
ax.plot(df_200um["voltage_abs"], df_200um["inv_c2"], 
        marker="o", color=colors[1], 
        linewidth=1,
        markersize=3, 
        label="200μm")
ax.plot(df_120um["voltage_abs"], df_120um["inv_c2"], 
        marker="o", color=colors[2], 
        linewidth=1,
        markersize=3, 
        label="120μm")

# Add endcap assumption lines with error bands
voltage_range = np.array([0, 500])

# 300μm endcap
endcap_300 = END_INV_CAPACITANCE_2_ASSUMPTION["300"]
endcap_300_upper = endcap_300 * (1 + END_CAP_ERROR_UP)
endcap_300_lower = endcap_300 * (1 - END_CAP_ERROR_DOWN)

ax.axhline(y=endcap_300, color=colors[0], linestyle="--", linewidth=1, alpha=0.8)
ax.fill_between(voltage_range, endcap_300_lower, endcap_300_upper, 
                color=colors[0], alpha=0.3, linewidth=0)

# 200μm endcap
endcap_200 = END_INV_CAPACITANCE_2_ASSUMPTION["200"]
endcap_200_upper = endcap_200 * (1 + END_CAP_ERROR_UP)
endcap_200_lower = endcap_200 * (1 - END_CAP_ERROR_DOWN)

ax.axhline(y=endcap_200, color=colors[1], linestyle="--", linewidth=1, alpha=0.8)
ax.fill_between(voltage_range, endcap_200_lower, endcap_200_upper, 
                color=colors[1], alpha=0.3, linewidth=0)

# 120μm endcap
endcap_120 = END_INV_CAPACITANCE_2_ASSUMPTION["120"]
endcap_120_upper = endcap_120 * (1 + END_CAP_ERROR_UP)
endcap_120_lower = endcap_120 * (1 - END_CAP_ERROR_DOWN)

ax.axhline(y=endcap_120, color=colors[2], linestyle="--", linewidth=1, alpha=0.8)
ax.fill_between(voltage_range, endcap_120_lower, endcap_120_upper, 
                color=colors[2], alpha=0.3, linewidth=0)

# Apply PLOT_STYLE settings manually
# Axis labels using PLOT_STYLE["axes.font.size"]
ax.set_xlabel("Voltage [V]", 
              fontsize=9, 
              fontweight="bold")
ax.set_ylabel(r"$1/Capacitance^2$ [$\dfrac{1}{F^{2}}$]", 
              fontsize=9, 
              fontweight="bold")

# Set axis limits
ax.set_xlim(0, 500)

# Tick parameters using PLOT_STYLE
ax.tick_params(
    axis='both', 
    which='major',
    labelsize=8,  # 9
    size=PLOT_STYLE["axes.tick.major.size"],  # 4
    width=PLOT_STYLE["axes.tick.major.width"]  # 1
)
ax.tick_params(
    axis='both',
    which='minor',
    size=PLOT_STYLE["axes.tick.minor.size"],  # 2
    width=PLOT_STYLE["axes.tick.minor.width"]  # 1
)

# Spine (border) width using PLOT_STYLE["axes.border.width"]
for spine in ax.spines.values():
    spine.set_linewidth(PLOT_STYLE["axes.border.width"])

# Grid
ax.grid(True, alpha=0.8, linestyle=":", linewidth=0.3)

# Legend using PLOT_STYLE["legend.size"]
legend = ax.legend(
    fontsize=7, 
    markerscale=3.5 / 3,
    frameon=True, 
    loc="upper left",
    bbox_to_anchor=(0.01, 0.91),
    borderaxespad=1, 
    fancybox=True, 
    framealpha=0.7,
    handlelength=1.6
)

# Set legend frame properties
legend.get_frame().set_linewidth(0.3)
legend.get_frame().set_edgecolor("black")

plt.tight_layout()
plt.savefig("UIRAD_CV_1overC2.pdf", dpi=300, bbox_inches="tight")
plt.show()