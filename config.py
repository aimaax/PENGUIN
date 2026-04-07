from ast import Str
import os
import numpy as np
import matplotlib.cm as cm

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


# Define the RGB colors for diodes plot.
CUSTOM_COLORS = [
    "#3f90da",  # Blue
    "#f1a90e",  # Yellow 
    "#bd1f01",  # Red
    "#94a4a2",  # Gray
    "#832db6",  # Violet
    "#a96b59",  # Brown
    "#e76300",  # Orange
    "#b9ac70",  # Green
    "#717581",  # Ash
    "#3f90da",  # Blue
    "#bd1f01",  # Red
    "#94a4a2",  # Gray
    "#f1a90e",  # Yellow 
]

# CUSTOM_COLORS = [
#     "#e41a1c", 
#     "#377eb8", 
#     "#4daf4a", 
#     "#7570b3", 
#     "#000000", 
#     "#ff7f00", 
#     "#a65628"
# ]

MATPLOTLIB_COLORS = {
    "viridis": cm.get_cmap("viridis"),
    "plasma": cm.get_cmap("plasma"),
    "inferno": cm.get_cmap("inferno"),
    "magma": cm.get_cmap("magma"),
    "cividis": cm.get_cmap("cividis"),
}

MARKERS = ['o', '^', 's', 'D', 'X', '>', 'P', '<', 'h', '.', 'p', 'd', '*'] 

LINESTYLES = ["-", "--", "-.", ":"]

FILLSTYLE = "full"
MARKERSIZE = 7
LEGEND_SIZE = 8


# Automatically get the root path of the repository 
ROOT_PATH_REPO = os.path.dirname(os.path.abspath(__file__))


DEFAULT_DIR_DATA = os.path.join(ROOT_PATH_REPO, "Data")
DEFAULT_DIR_SATURATION_VOLTAGE_DATA = os.path.join(ROOT_PATH_REPO, "Database", "SaturationVoltageData")
DEFAULT_DIR_PLOT_SENSORS_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots")
DEFAULT_DIR_VOLUME_NORM_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots", "Volume_Norm_vs_Fluence")
DEFAULT_DIR_SATURATION_VOLTAGE_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots", "Saturation_Voltage_vs_Fluence")
DEFAULT_DIR_CC_FLUENCE_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots", "CC_vs_Fluence")
DEFAULT_DIR_CCE_FLUENCE_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots", "CCE_vs_Fluence")
DEFAULT_DIR_CCE_ANNEALING_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots", "CCE_vs_Annealing")
DEFAULT_DIR_CC_ANNEALING_RESULTS = os.path.join(ROOT_PATH_REPO, "SavedPlots", "CC_vs_Annealing")

DEFAULT_DIR_SATURATION_VOLTAGE_FIT = os.path.join(ROOT_PATH_REPO, "SavedPlots", "Saturation_Voltage_Fit")
DEFAULT_PATH_SATURATION_VOLTAGE_FIT_OVERVIEW= os.path.join(ROOT_PATH_REPO, "Data", "Saturation_Voltage_Fit", "Saturation_Voltage_Fit_Overview.csv")

DEFAULT_DIR_ANNEALING_FILES = os.path.join(ROOT_PATH_REPO, "Data", "Annealing_Files")

# Database inputs
DEFAULT_DATABASE_PATH = os.path.join(ROOT_PATH_REPO, "Database", "Diodes_Database.pkl")

DATABASE_COLUMNS = ['sensor_id', 'campaign', 'thickness', 'fluence', 'temperature', 'CVF', 
                    'annealing_time', 'annealing_temp', 
                    'type', 'file_IV', 'file_CV', 'open_corr', 'file_TCT', 'TCT_corr', 
                    'sat_V_CV', 'sat_V_err_down_CV', 'sat_V_err_up_CV', 'low_fit_start_CV', 'low_fit_stop_CV', 'high_fit_start_CV', 'high_fit_stop_CV', "upper_fit_params_CV",
                    'sat_V_TCT', 'sat_V_err_down_TCT', 'sat_V_err_up_TCT', 'low_fit_start_TCT', 'low_fit_stop_TCT', 'high_fit_start_TCT', 'high_fit_stop_TCT', "upper_fit_params_TCT",
                    'corrected_annealing_time', 'corr_ann_time_err_up', 'corr_ann_time_err_down', 'Blacklisted']

DATABASE_INDEX_LEVEL = ['sensor_id', 'campaign', 'thickness', 'fluence', 'temperature', 'CVF', 'annealing_time']

COLUMN_DTYPES = {
    "sensor_id": str,
    "campaign": str,
    "thickness": np.int64,
    "fluence": np.float64,
    "temperature": np.int64,
    "CVF": np.int64,
    # "path": str,
    "annealing_time": str,
    "annealing_temp": np.float64,
    "type": str,
    "file_IV": str,
    "file_CV": str,
    "open_corr": np.float64,
    "file_TCT": str,
    "TCT_corr": np.float64,
    "sat_V_CV": np.float64,
    "sat_V_err_down_CV": np.float64,
    "sat_V_err_up_CV": np.float64,
    "low_fit_start_CV": np.float64,
    "low_fit_stop_CV": np.float64,
    "high_fit_start_CV": np.float64,
    "high_fit_stop_CV": np.float64,
    "upper_fit_params_CV": object,
    "sat_V_TCT": np.float64,
    "sat_V_err_down_TCT": np.float64,
    "sat_V_err_up_TCT": np.float64,
    "low_fit_start_TCT": np.float64,
    "low_fit_stop_TCT": np.float64,
    "high_fit_start_TCT": np.float64,
    "high_fit_stop_TCT": np.float64,
    "upper_fit_params_TCT": object,
    "corrected_annealing_time": str,
    "corr_ann_time_err_up": str,
    "corr_ann_time_err_down": str,
    "Blacklisted": bool,
}

VALID_HALFMOONS = ["UL", "UR", "UR1", "UR2", "LL2", "LL1", "LR"]

CAMPAIGNS = [
    "HighFluenceIrrNeutron2023",
    "ProtonIrr2024",
    "LowFluenceIrrNeutron2025",
    "DoubleIrrNeutron2025",
    "DoubleIrrSRNeutron2025"
]

CAMPAIGN_TO_SENSOR_OVERVIEW_GOOGLE_ID_GID = {
    "HighFluenceIrrNeutron2023": ["", ""],
    "ProtonIrr2024": ["", ""],
    "LowFluenceIrrNeutron2025": ["", ""],
    "DoubleIrrNeutron2025": ["", ""],
    "DoubleIrrSRNeutron2025": ["", ""]
}

CAMPAIGN_TO_MEAS_LOG_ONPCB_GOOGLE_ID_GID = {
    "HighFluenceIrrNeutron2023": ["", ""],
    "ProtonIrr2024": ["", ""],
    "LowFluenceIrrNeutron2025": ["", ""],
    "DoubleIrrNeutron2025": ["", ""],
    "DoubleIrrSRNeutron2025": ["", ""]
}

CORRECTED_ANNEALING_TIMES_GOOGLE_ID_GID = {
    "HighFluenceIrrNeutron2023": ["", ""],
    "ProtonIrr2024": ["", ""],
    "LowFluenceIrrNeutron2025": ["", ""],
    "DoubleIrrNeutron2025": ["", ""],
    "DoubleIrrSRNeutron2025": ["", ""]
}

CAMPAIGN_TO_DISPLAY_NAME = {
    "HighFluenceIrrNeutron2023": "HF",
    "ProtonIrr2024": "Proton",
    "LowFluenceIrrNeutron2025": "LF",
    "DoubleIrrNeutron2025": "DI",
    "DoubleIrrSRNeutron2025": "DI SR"
}

CAMPAIGN_TO_PARTICLE_DICT = {
    "HighFluenceIrrNeutron2023": "Neutrons",
    "ProtonIrr2024": "Protons",
    "LowFluenceIrrNeutron2025": "Neutrons",
    "DoubleIrrNeutron2025": "Neutrons",
    "DoubleIrrSRNeutron2025": "Neutrons"
}

MEASUREMENT_DIR = [
    "IV_onPCB",
    "CV_onPCB",
    "TCT",
    "IVCV_bare"
]

DEFAULT_MEASUREMENT_DIR_CHECKED = {
    "IV_onPCB": True,
    "CV_onPCB": True,
    "TCT": True,
    "IVCV_bare": False
}

DEFAULT_COLUMNS_TO_DISPLAY_DATABASE = {
    "sensor_id": True,
    "campaign": True,
    "thickness": True,
    "fluence": True, 
    "temperature": False,
    "CVF": False, 
    # "path": False, 
    "annealing_time": True, 
    "annealing_temp": True,
    "type": True, 
    "file_IV": True, 
    "file_CV": True, 
    "open_corr": False,
    "file_TCT": True,
    "TCT_corr": True,
    "sat_V_CV": True,
    "sat_V_err_down_CV": False,
    "sat_V_err_up_CV": False,
    "low_fit_start_CV": True,
    "low_fit_stop_CV": True,
    "high_fit_start_CV": True,
    "high_fit_stop_CV": True,
    "upper_fit_params_CV": False,
    "sat_V_TCT": True,
    "sat_V_err_down_TCT": False,
    "sat_V_err_up_TCT": False,
    "low_fit_start_TCT": True,
    "low_fit_stop_TCT": True,
    "high_fit_start_TCT": True,
    "high_fit_stop_TCT": True,
    "upper_fit_params_TCT": False,
    "corrected_annealing_time": True,
    "corr_ann_time_err_up": False,
    "corr_ann_time_err_down": False,
    "Blacklisted": True
}

DEFAULT_OVERWRITE_COLUMNS_DATABASE = {
    "sensor_id": False,
    "campaign":False,
    "thickness": False,
    "fluence": False, 
    "temperature": False,
    "CVF": False, 
    # "path": False, 
    "annealing_time": False, 
    "annealing_temp": False,
    "type": False, 
    "file_IV": False, 
    "file_CV": False, 
    "open_corr": False,
    "file_TCT": False,
    "TCT_corr": False,
    "sat_V_CV": False,
    "sat_V_err_down_CV": False,
    "sat_V_err_up_CV": False,
    "low_fit_start_CV": False,
    "low_fit_stop_CV": False,
    "high_fit_start_CV": False,
    "high_fit_stop_CV": False,
    "upper_fit_params_CV": False,
    "sat_V_TCT": False,
    "sat_V_err_down_TCT": False,
    "sat_V_err_up_TCT": False,
    "low_fit_start_TCT": False,
    "low_fit_stop_TCT": False,
    "high_fit_start_TCT": False,
    "high_fit_stop_TCT": False,
    "upper_fit_params_TCT": False,
    "corrected_annealing_time": False,
    "corr_ann_time_err_up": False,
    "corr_ann_time_err_down": False,
    "Blacklisted": False
}


MEASUREMENTS = [
    "IV",
    "CV",
    "TCT"
]

ANNEALING_TIME_BARE = [
    "noadd",
]


VOLTAGE_LIST = [
    "100",
    "200",
    "300",
    "400",
    "500",
    "600",
    "700",
    "800",
    "900",
    "Saturation Voltage"
]

# N highest curvature points to fit the straight line
N_HIGHEST_CURVATURE_POINTS = 5

# Color in hex format for the low, high lines and labels
COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED = {
    "sat_V": "#FF0000", # Red
    "low_fit_line": "#FFA500", # Orange
    "low_fit_points": "#FFA500", # Orange
    "high_fit_line": "#FFA500", # Orange
    "high_fit_points": "#FFA500", # Orange
    "low_fit_start": "#6aa84f",   # Light green
    "low_fit_stop": "#274e13",    # Dark green
    "high_fit_start": "#3d85c6",  # Light blue
    "high_fit_stop": "#073763",   # Dark blue
}

COLOR_SAT_V_FIT_RESULTS_ANALYSED = {
    "sat_V": "#FF0000", # Red
    "low_fit_line": "#6aa84f", # Green
    "low_fit_points": "#6aa84f", # Green
    "high_fit_line": "#6aa84f", # Green
    "high_fit_points": "#6aa84f", # Green
    "low_fit_start": "#5b5b5b",   # Gray
    "low_fit_stop": "#5b5b5b",    # Gray
    "high_fit_start": "#5b5b5b",  # Gray
    "high_fit_stop": "#5b5b5b",   # Gray
}

END_INV_CAPACITANCE_2_ASSUMPTION = {
    # "300": 1.2e22,
    # "200": 5.422e21,
    # "120": 1.952e21
    "300": 1.187e22,
    "200": 5.4e21,
    "120": 1.952e21
}

FULLCHARGE_CC_DICT = {
        120: 58,  # fC
        200: 108.99,  # fC
        300: 143  # fC
    }


END_CAP_ERROR_UP = 0.03 # 3% error up
END_CAP_ERROR_DOWN = 0.02 # 2% error down

PLATEAU_ERROR_UP = 0.015 # 1.5% error up
PLATEAU_ERROR_DOWN = 0.005 # 0.5% error down

MANUAL_UPPER_LINE_ERROR_UP = 0.05 # 5% error up
MANUAL_UPPER_LINE_ERROR_DOWN = 0.05 # 5% error down

SAT_V_ERROR_UP_TCT = 0.05 # 5% error up
SAT_V_ERROR_DOWN_TCT = 0.05 # 5% error down

UNCERTAINTY_THICKNESS = 10.0 # 10 μm
UNCERTAINTY_FLUENCE = 0.10 # 10%


ANNEALING_TEMP_OVEN = [
    "30.0",
    "40.0",
    "60.0"
]

LABEL_MODE = "fluence, thickness, annealing_time"
# LABEL_MODE = "fluence, thickness, sensor_id"


# ------------------------------------------------------------------------------
# --------------- Helper function to retrieve config information ---------------
# ------------------------------------------------------------------------------


def get_thickness_color(thickness):
    thickness_colors = {
        120: CUSTOM_COLORS[0],
        200: CUSTOM_COLORS[1],
        300: CUSTOM_COLORS[2]
    }
    
    return thickness_colors.get(thickness, "black")