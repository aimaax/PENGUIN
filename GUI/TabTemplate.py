from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QFileDialog, QSizePolicy, QTabWidget
)
import warnings
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.ticker import NullFormatter
from matplotlib.widgets import RectangleSelector
import pandas as pd
import os
import numpy as np

from config import MEASUREMENTS, VOLTAGE_LIST, VALID_HALFMOONS, CAMPAIGN_TO_DISPLAY_NAME
from config import DEFAULT_DATABASE_PATH, DEFAULT_DIR_PLOT_SENSORS_RESULTS
from Utils.CheckableComboBox import CheckableComboBox
from Utils.create_database_helper import sort_annealing_time
from GUI.SettingsPlot import SettingsPlot

class TabTemplate(QWidget):
    def __init__(self, parent_tab, tab_config, plot_function):
        """
        TabTemplate: reusable widget for plotting tabs
        parent_tab: main tab or container
        tab_config: dictionary specifying which input fields to show
        plot_function: function to call when pressing 'Display Plot'
        
        tab_config format and type of Pyside6:
        [Tab Name] = {
            "title": "Tab Title",
            "save_path": True,
            "campaign": True, (CheckableComboBox)
            "measurement": True, (QComboBox)
            "measurement_type": True, (CheckableComboBox)
            "thickness": False, (CheckableComboBox)
            "annealing_temp": True, (CheckableComboBox)
            "sensor_id": True, (CheckableComboBox)
            "annealing_time": True, (CheckableComboBox)
            "fluence": True, (CheckableComboBox)
            "voltage": True, (QComboBox)
            "plot_saturation_voltage_from_tct": True, (QCheckBox)
        }
        """
        super().__init__()

        self.parent_tab = parent_tab
        self.tab_config = tab_config
        self.plot_function = plot_function

        # Load database and unique values
        self.load_database()

        # Main horizontal layout: left=canvas, right=input tabs
        self.main_layout = QHBoxLayout(self)
        self.setLayout(self.main_layout)

        # --- Left side: Canvas container ---
        self.plot_container = QWidget()
        self.plot_container_layout = QVBoxLayout(self.plot_container)
        self.plot_container_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.addWidget(self.plot_container)

        # Matplotlib figure
        self.fig = Figure(figsize=(4.5, 3))
        self.fig.set_constrained_layout(True)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_container_layout.addWidget(self.canvas)

        # --- Right side: Input tabs ---
        self.input_tabs = QTabWidget()
        self.input_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.input_tabs.setMaximumWidth(300)
        self.main_layout.addWidget(self.input_tabs)

        # Tab from tab_config
        self.tab_custom = QWidget()
        self.tab_custom.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.tab_layout = QVBoxLayout(self.tab_custom)
        
        # self.tab_custom = QWidget()
        # self.tab_custom_scroll = QScrollArea()
        # self.tab_custom_scroll.setWidgetResizable(True)
        # self.tab_custom_scroll.setWidget(self.tab_custom)
        # self.tab_layout = QVBoxLayout(self.tab_custom)

        # Save path
        if tab_config.get("save_path", False):
            self.save_path_input = QLineEdit(DEFAULT_DIR_PLOT_SENSORS_RESULTS)
            self.save_path_button = QPushButton("Browse")
            self.save_path_button.clicked.connect(self.select_save_path)
            self.tab_layout.addWidget(QLabel("Save Path:"))
            self.tab_layout.addWidget(self.save_path_input)
            self.tab_layout.addWidget(self.save_path_button)
            self.tab_layout.addSpacing(1)

        # Campaign
        if tab_config.get("campaign", False):
            self.campaign_input = CheckableComboBox()
            self.campaign_input.addItems(self.CAMPAIGNS)
            if tab_config.get("sensor_id_hf", False): # for DI vs HF Comparison
                self.campaign_input.select_from_list(["DoubleIrrNeutron2025", "DoubleIrrSRNeutron2025", "HighFluenceIrrNeutron2023"])
            else:
                self.campaign_input.select_first_index()
            self.tab_layout.addWidget(QLabel("Campaign:"))
            self.tab_layout.addWidget(self.campaign_input)
            self.tab_layout.addSpacing(1)
            
        # Measurement
        if tab_config.get("measurement", False):
            self.measurement_input = QComboBox()
            self.measurement_input.addItems(MEASUREMENTS)
            self.tab_layout.addWidget(QLabel("Measurement:"))
            self.tab_layout.addWidget(self.measurement_input)
            
            if tab_config.get("incluce_i_tot", False):
                self.measurement_input.currentIndexChanged.connect(self.update_logy_i_tot_check)

        # Include Uncertainty Checkbox
        if tab_config.get("include_uncertainty", False):
            self.include_uncertainty_check = QCheckBox("Include uncertainty")
            self.include_uncertainty_check.setChecked(False)
            self.tab_layout.addWidget(self.include_uncertainty_check)

        # Measurement Type
        if tab_config.get("measurement_type", False):
            self.measurement_type_input = CheckableComboBox()
            self.measurement_type_input.addItems(self.MEASUREMENT_TYPE)
            # self.measurement_type_input.select_first_index()
            self.measurement_type_input.select_from_list(["onPCB"])
            self.tab_layout.addWidget(QLabel("Measurement Type:"))
            self.tab_layout.addWidget(self.measurement_type_input)
            self.tab_layout.addSpacing(1)

        # I_tot Checkbox
        if tab_config.get("incluce_i_tot", False):
            self.i_tot_check = QCheckBox("Include total current (i_tot), bare measurements")
            self.i_tot_check.setChecked(True)
            self.tab_layout.addWidget(self.i_tot_check)

        # Thickness
        if tab_config.get("thickness", False):
            self.thickness_input = CheckableComboBox()
            self.thickness_input.addItems(self.THICKNESS, select_all=True)
            self.tab_layout.addWidget(QLabel("Thickness (µm):"))
            self.tab_layout.addWidget(self.thickness_input)
            self.tab_layout.addSpacing(1)
            
        # Annealing Temp
        if tab_config.get("annealing_temp", False):
            temp_layout = QHBoxLayout()
            temp_layout.addWidget(QLabel("Annealing Temperature:"))
            self.annealing_temp_input = CheckableComboBox()
            # self.update_unique_annealing_temp(select_all=True)
            temp_layout.addWidget(QPushButton("Select All", clicked=self.annealing_temp_input.select_all))
            temp_layout.addWidget(QPushButton("Deselect All", clicked=self.annealing_temp_input.deselect_all))
            self.tab_layout.addLayout(temp_layout)
            self.tab_layout.addWidget(self.annealing_temp_input)
            self.tab_layout.addSpacing(1)
            
        # Sensor ID
        if tab_config.get("sensor_id", False):
            sensor_layout = QHBoxLayout()
            sensor_layout.addWidget(QLabel("Sensor ID:"))
            self.sensor_id_input = CheckableComboBox()
            self.update_unique_sensor_id()
            sensor_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_input.select_all))
            sensor_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_input.deselect_all))
            self.tab_layout.addLayout(sensor_layout)
            self.tab_layout.addWidget(self.sensor_id_input)
            self.tab_layout.addSpacing(1)
            
        if tab_config.get("plot_only_second_round_of_DI", False):
            self.plot_only_second_round_of_DI_input = QCheckBox("Plot only second round of DI")
            self.plot_only_second_round_of_DI_input.setChecked(False)
            self.plot_only_second_round_of_DI_input.stateChanged.connect(self.enable_disable_unique_sensor_id_fr)
            self.tab_layout.addWidget(self.plot_only_second_round_of_DI_input)
            self.tab_layout.addSpacing(1)
            
        if tab_config.get("sensor_id_fr", False):
            sensor_fr_layout = QHBoxLayout()
            sensor_fr_layout.addWidget(QLabel("DI FR: Sensor ID"))
            self.sensor_id_fr_input = CheckableComboBox()
            sensor_fr_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_fr_input.select_all))
            sensor_fr_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_fr_input.deselect_all))
            self.tab_layout.addLayout(sensor_fr_layout)
            self.tab_layout.addWidget(self.sensor_id_fr_input)
            self.tab_layout.addSpacing(1)
            
        if tab_config.get("sensor_id_sr", False):
            sensor_sr_layout = QHBoxLayout()
            sensor_sr_layout.addWidget(QLabel("DI SR: Sensor ID"))
            self.sensor_id_sr_input = CheckableComboBox()
            sensor_sr_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_sr_input.select_all))
            sensor_sr_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_sr_input.deselect_all))
            self.tab_layout.addLayout(sensor_sr_layout)
            self.tab_layout.addWidget(self.sensor_id_sr_input)
            self.tab_layout.addSpacing(1)
            
        # Sensor ID HF for DI vs HF Comparison
        if tab_config.get("sensor_id_hf", False):
            sensor_hf_layout = QHBoxLayout()
            sensor_hf_layout.addWidget(QLabel("HF: Sensor ID"))
            self.sensor_id_hf_input = CheckableComboBox()
            sensor_hf_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_hf_input.select_all))
            sensor_hf_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_hf_input.deselect_all))
            self.tab_layout.addLayout(sensor_hf_layout)
            self.tab_layout.addWidget(self.sensor_id_hf_input)
            self.tab_layout.addSpacing(1)
            
        # Sensor ID LF for DI vs HF Comparison
        if tab_config.get("sensor_id_lf", False):
            sensor_lf_layout = QHBoxLayout()
            sensor_lf_layout.addWidget(QLabel("LF: Sensor ID"))
            self.sensor_id_lf_input = CheckableComboBox()
            sensor_lf_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_lf_input.select_all))
            sensor_lf_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_lf_input.deselect_all))
            self.tab_layout.addLayout(sensor_lf_layout)
            self.tab_layout.addWidget(self.sensor_id_lf_input)
            self.tab_layout.addSpacing(1)
            
        # Annealing points after last annealing step of DI, values between 0 and 20
        if tab_config.get("HF_points_after_last_DI_annealing_step", False):
            self.points_after_last_annealing_step_input = QSpinBox()
            self.points_after_last_annealing_step_input.setRange(0, 40)  # allowed values
            self.points_after_last_annealing_step_input.setValue(5)      # default value
            self.tab_layout.addWidget(QLabel("HF points after last DI annealing step:"))
            self.tab_layout.addWidget(self.points_after_last_annealing_step_input)
            self.tab_layout.addSpacing(1)
            
        # Annealing Time
        if tab_config.get("annealing_time", False):
            time_layout = QHBoxLayout()
            time_layout.addWidget(QLabel("Annealing Time:"))
            self.annealing_time_input = CheckableComboBox()
            self.update_unique_annealing_time()
            time_layout.addWidget(QPushButton("Select All", clicked=self.annealing_time_input.select_all))
            time_layout.addWidget(QPushButton("Deselect All", clicked=self.annealing_time_input.deselect_all))
            self.tab_layout.addLayout(time_layout)
            self.tab_layout.addWidget(self.annealing_time_input)
            self.tab_layout.addSpacing(1)
            
        # Fluence
        if tab_config.get("fluence", False):
            fluence_layout = QHBoxLayout()
            fluence_layout.addWidget(QLabel("Fluence:"))
            self.fluence_input = CheckableComboBox()
            self.fluence_input.addItems(self.FLUENCE, select_all=True)
            fluence_layout.addWidget(QPushButton("Select All", clicked=self.fluence_input.select_all))
            fluence_layout.addWidget(QPushButton("Deselect All", clicked=self.fluence_input.deselect_all))
            self.tab_layout.addLayout(fluence_layout)
            self.tab_layout.addWidget(self.fluence_input)
            self.tab_layout.addSpacing(1)
            
        # Type of Plot for DI vs HF Comparison
        if tab_config.get("type_of_plot", False):
            self.type_of_plot_input = QComboBox()
            self.type_of_plot_input.addItems(["alpha", "saturation voltage", "CC", "CCE"])
            self.type_of_plot_input.setCurrentIndex(0)
            self.type_of_plot_input.currentIndexChanged.connect(lambda: self.enable_disable_plot_from_saturation_voltage_checkbox(self.type_of_plot_input.currentText()))
            self.tab_layout.addWidget(QLabel("Type of Plot vs Annealing Time:"))
            self.tab_layout.addWidget(self.type_of_plot_input)
            self.tab_layout.addSpacing(1)
            
        # Voltage
        if tab_config.get("voltage", False):
            self.voltage_input = QComboBox()
            self.voltage_input.addItems(VOLTAGE_LIST)
            self.voltage_input.setCurrentIndex(VOLTAGE_LIST.index("400"))
            self.sat_volt_cv_tct = QComboBox()
            self.sat_volt_cv_tct.addItems(["CV", "TCT"])
            self.sat_volt_cv_tct.setCurrentIndex(0)
            self.sat_volt_cv_tct.setEnabled(False)
            self.voltage_input.currentIndexChanged.connect(lambda: self.enable_disable_sat_volt_combo_box(self.voltage_input.currentText()))
            self.tab_layout.addWidget(QLabel("Voltage (V):"))
            self.tab_layout.addWidget(self.voltage_input)
            self.tab_layout.addWidget(QLabel("Saturation Voltage extracted from:"))
            self.tab_layout.addWidget(self.sat_volt_cv_tct)
            self.tab_layout.addSpacing(1)
            
        if tab_config.get("add_quarter_ann_time_from_di_first_round", False):
            self.add_quarter_ann_time_from_di_first_round_input = QCheckBox("Add 1/4 ann time from DI FR to SR")
            self.add_quarter_ann_time_from_di_first_round_input.setChecked(False)
            self.tab_layout.addWidget(self.add_quarter_ann_time_from_di_first_round_input)
            
        if tab_config.get("split_x_axis", False):
            self.split_x_axis_input = QCheckBox("Split x-axis")
            self.split_x_axis_input.setChecked(True)
            self.tab_layout.addWidget(self.split_x_axis_input)
        
        if tab_config.get("plot_ratio_DI_vs_HF", False):
            ratio_checkbox_layout = QHBoxLayout()
            self.plot_ratio_DI_vs_HF_input = QCheckBox("Plot ratio DI/HF")
            self.plot_ratio_DI_vs_HF_input.setChecked(False)
            ratio_checkbox_layout.addWidget(self.plot_ratio_DI_vs_HF_input)
            
            self.plot_average_ratio_DI_vs_HF_input = QCheckBox("Plot average ratio DI/HF")
            self.plot_average_ratio_DI_vs_HF_input.setChecked(False)
            ratio_checkbox_layout.addWidget(self.plot_average_ratio_DI_vs_HF_input)
            self.tab_layout.addLayout(ratio_checkbox_layout)
            
            
        if tab_config.get("plot_saturation_voltage_from_tct", False) or tab_config.get("plot_saturation_voltage_from_cv_and_tct", False):
            # Create horizontal layout for saturation voltage checkboxes
            sat_volt_layout = QHBoxLayout()
            
            if tab_config.get("plot_saturation_voltage_from_tct", False):
                self.plot_saturation_voltage_from_tct_input = QCheckBox("Sat Volt TCT")
                self.plot_saturation_voltage_from_tct_input.setChecked(False)
                sat_volt_layout.addWidget(self.plot_saturation_voltage_from_tct_input)
            
            if tab_config.get("plot_saturation_voltage_from_cv_and_tct", False):
                self.plot_saturation_voltage_from_cv_and_tct_input = QCheckBox("Sat Volt CV and TCT")
                self.plot_saturation_voltage_from_cv_and_tct_input.setChecked(False)
                sat_volt_layout.addWidget(self.plot_saturation_voltage_from_cv_and_tct_input)

            if tab_config.get("type_of_plot", False):
                self.enable_disable_plot_from_saturation_voltage_checkbox(self.type_of_plot_input.currentText())
                
            # Add stretch to push checkboxes to the left
            sat_volt_layout.addStretch(1)            

            # Add the horizontal layout to the main tab layout
            self.tab_layout.addLayout(sat_volt_layout)

        # Connect external callbacks
        if tab_config.get("annealing_temp", False):
            if not tab_config.get("sensor_id_hf", False):
                self.campaign_input.add_external_callback(self.update_unique_annealing_temp)
            self.measurement_type_input.add_external_callback(self.update_unique_annealing_temp)
            self.update_unique_annealing_temp(select_all=True)
        if tab_config.get("sensor_id", False):
            self.annealing_temp_input.add_external_callback(self.update_unique_sensor_id)
        if tab_config.get("annealing_time", False):
            self.sensor_id_input.add_external_callback(self.update_unique_annealing_time)
        if tab_config.get("sensor_id_fr", False):
            self.update_unique_sensor_id_fr()
            self.thickness_input.add_external_callback(self.update_unique_sensor_id_fr)
            self.annealing_temp_input.add_external_callback(self.update_unique_sensor_id_fr)
        if tab_config.get("sensor_id_sr", False):
            self.annealing_temp_input.add_external_callback(self.update_unique_sensor_id_sr)
            self.sensor_id_fr_input.add_external_callback(lambda: self.update_unique_sensor_id_sr(select_all=True))
        if tab_config.get("sensor_id_hf", False):
            self.sensor_id_sr_input.add_external_callback(lambda: self.update_unique_sensor_id_hf(select_all=True))
        if tab_config.get("sensor_id_lf", False):
            self.update_unique_sensor_id_lf()
            self.campaign_input.add_external_callback(self.update_unique_sensor_id_lf)
            self.thickness_input.add_external_callback(self.update_unique_sensor_id_lf)
            self.annealing_temp_input.add_external_callback(self.update_unique_sensor_id_lf)
            
        
        # Plot button
        self.plot_button = QPushButton("Display Plot")
        self.plot_button.clicked.connect(self.plot_function)
        self.tab_layout.addWidget(self.plot_button)

        # Save plot button
        self.save_plot_button = QPushButton("Save Plot")
        self.save_plot_button.clicked.connect(self.save_plot)
        self.tab_layout.addWidget(self.save_plot_button)

        # Fig size save 
        self.fig_size_save_input = QComboBox()
        self.fig_size_save_input.addItems([
            "Original",
            "4:3",
            "5:3",
            "16:9",
            "4:2",
            "5:2",
            "6:2",
            "1:1",
            "8:7",
            "9:8",
            "10:9",
            "11:10",
            "3:2",
            "21:9"
        ])
        self.tab_layout.addWidget(QLabel("Fig size save (ratio):"))
        self.tab_layout.addWidget(self.fig_size_save_input)

        self.tab_layout.addStretch(1)

        # Add the custom tab
        self.input_tabs.addTab(self.tab_custom, tab_config.get("title", "Plot Settings"))

        # Settings tab
        self.plot_settings_tab = SettingsPlot(self.plot_function)
        self.input_tabs.addTab(self.plot_settings_tab, "Plot Settings")

        # Zoom state
        self._rect_selector = None
        self._original_xlim = None
        self._original_ylim = None

        # Connect zoom buttons from the settings tab
        self.plot_settings_tab.zoom_button.toggled.connect(self._toggle_zoom_mode)
        self.plot_settings_tab.reset_zoom_button.clicked.connect(self._reset_zoom)

        self.main_layout.setStretch(0, 10)
        self.main_layout.setStretch(1, 1)
    
    
    # -----------------------------------------------------------
    # -------------------- Utility functions --------------------
    # -----------------------------------------------------------

    def load_database(self):
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
            self.CAMPAIGNS = sorted(self.database.index.get_level_values('campaign').unique().tolist())
            self.MEASUREMENT_TYPE = sorted(self.database['type'].unique().tolist())
            self.THICKNESS = sorted([str(th) for th in self.database.index.get_level_values('thickness').unique()])
            self.ANNEALING_TEMP = sorted([str(temp) for temp in self.database["annealing_temp"].unique()])
            self.ANNEALING_TIME = sort_annealing_time(self.database.index.get_level_values('annealing_time').unique())
            self.FLUENCE = sorted([f"{f:.1e}" for f in self.database.index.get_level_values('fluence').unique()])
            self.SENSOR_ID = sorted(self.database.index.get_level_values('sensor_id').unique().tolist())
        else:
            self.database = None
            self.CAMPAIGNS = []
            self.MEASUREMENT_TYPE = []
            self.THICKNESS = []
            self.ANNEALING_TEMP = []
            self.ANNEALING_TIME = []
            self.FLUENCE = []
            self.SENSOR_ID = []

    def select_save_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.save_path_input.setText(directory)
            

    def save_plot(self):
        save_path = os.path.join(self.save_path_input.text(), self.tab_config.get("title", "").replace(" ", ""))
        # Deactivate zoom mode
        selector_existed = False
        if self._rect_selector is not None:
            selector_existed = True
            self._rect_selector.disconnect_events()
        if save_path != "":
            # Create a new directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)
            
            campaign_name = "_".join(CAMPAIGN_TO_DISPLAY_NAME[c].replace(" ", "") for c in self.campaign_input.get_selected_items())
            temperature = "_".join([str(int(float(temp))) for temp in self.annealing_temp_input.get_selected_items()])
            if self.tab_config.get("type_of_plot", False):
                type_of_plot = self.type_of_plot_input.currentText()
            else:
                type_of_plot = ""
            if self.tab_config.get("annealing_time", False):
                annealing_time = "_".join(self.annealing_time_input.get_selected_items())
            else:
                annealing_time = ""
            if self.fig_size_save_input.currentText() != "Original":
                original_fig_size = self.fig.get_size_inches()
                base_width = 5.12
                # base_width = original_fig_size[0]
                # print(base_width)
                ratio_w = float(self.fig_size_save_input.currentText().split(":")[0])
                ratio_h = float(self.fig_size_save_input.currentText().split(":")[1])
                self.fig.set_size_inches(base_width, base_width * (ratio_h / ratio_w))

            # Save plot as pdf to save path
            parts = [campaign_name, temperature, annealing_time, type_of_plot]
            filename = "_".join(part for part in parts if part)
            self.fig.savefig(
                os.path.join(save_path, f"{filename}.pdf"),
                bbox_inches='tight',
                dpi=600
            )
            
            if self.fig_size_save_input.currentText() != "Original":
                self.fig.set_size_inches(original_fig_size)

        if selector_existed:
            self._setup_rectangle_selector()

    def get_fiter_mask(self, list_of_filters: list[str] = None):
        """Create a filter mask based on available input fields."""
        mask = pd.Series(True, index=self.database.index)

        # Campaign filter
        if self.tab_config.get("campaign", False) and hasattr(self, "campaign_input") and "campaign" in list_of_filters:
            selected_campaigns = self.campaign_input.get_selected_items()
            # if selected_campaigns:
            mask &= self.database.index.get_level_values("campaign").isin(selected_campaigns)

        # Measurement type filter
        if self.tab_config.get("measurement_type", False) and hasattr(self, "measurement_type_input") and "measurement_type" in list_of_filters:
            selected_types = self.measurement_type_input.get_selected_items()
            # if selected_types:
            mask &= self.database["type"].isin(selected_types)

        # Annealing temperature filter
        if self.tab_config.get("annealing_temp", False) and hasattr(self, "annealing_temp_input") and "annealing_temp" in list_of_filters:
            selected_temps = [float(temp) for temp in self.annealing_temp_input.get_selected_items()]
            # if selected_temps:
            mask &= self.database["annealing_temp"].isin(selected_temps)

        # Sensor ID filter
        if self.tab_config.get("sensor_id", False) and hasattr(self, "sensor_id_input") and "sensor_id" in list_of_filters:
            selected_sensors = self.sensor_id_input.get_selected_items()
            # if selected_sensors:
            mask &= self.database.index.get_level_values("sensor_id").isin(selected_sensors)

        # Thickness filter
        if self.tab_config.get("thickness", False) and hasattr(self, "thickness_input") and "thickness" in list_of_filters:
            selected_thickness = [float(th) for th in self.thickness_input.get_selected_items()]
            # if selected_thickness:
            mask &= self.database.index.get_level_values("thickness").isin(selected_thickness)

        # Fluence filter
        if self.tab_config.get("fluence", False) and hasattr(self, "fluence_input") and "fluence" in list_of_filters:
            selected_fluence = [float(f) for f in self.fluence_input.get_selected_items()]
            # if selected_fluence:
            mask &= self.database.index.get_level_values("fluence").isin(selected_fluence)

        # Exclude blacklisted entries
        mask &= (self.database["Blacklisted"] == False)

        return mask
    
    
    def enable_disable_unique_sensor_id_fr(self):
        if self.plot_only_second_round_of_DI_input.isChecked():
            self.sensor_id_fr_input.setEnabled(False)
            self.sensor_id_fr_input.clear()
        else:
            self.sensor_id_fr_input.setEnabled(True)
            self.update_unique_sensor_id_fr()
        # Update unique sensor ID SR
        self.update_unique_sensor_id_sr()
            
            
    def enable_disable_plot_from_saturation_voltage_checkbox(self, type_of_plot):
        if type_of_plot == "saturation voltage":
            self.plot_saturation_voltage_from_tct_input.setEnabled(True)
            self.plot_saturation_voltage_from_cv_and_tct_input.setEnabled(True)
        else:
            self.plot_saturation_voltage_from_tct_input.setEnabled(False)
            self.plot_saturation_voltage_from_tct_input.setChecked(False)
            self.plot_saturation_voltage_from_cv_and_tct_input.setEnabled(False)
            self.plot_saturation_voltage_from_cv_and_tct_input.setChecked(False)


    def enable_disable_sat_volt_combo_box(self, voltage):
        if voltage == "Saturation Voltage":
            self.sat_volt_cv_tct.setEnabled(True)
        else:
            self.sat_volt_cv_tct.setEnabled(False)
    
    
    def update_unique_annealing_temp(self, select_all=False):
        previous_annealing_temp = self.annealing_temp_input.get_selected_items()
        unique_annealing_temp = []
        if self.database is not None:
            if self.tab_config.get("sensor_id_hf", False):
                mask = self.get_fiter_mask(["measurement_type"])
                DI_campaigns = ["DoubleIrrNeutron2025", "DoubleIrrSRNeutron2025"]
                mask &= self.database.index.get_level_values("campaign").isin(DI_campaigns)
            else:
                mask = self.get_fiter_mask(["campaign", "measurement_type"])
            unique_annealing_temp = [str(temp) for temp in self.database[mask]["annealing_temp"].unique().tolist()]
            unique_annealing_temp = sorted(unique_annealing_temp, key=float)
            if self.annealing_temp_input is not None:
                self.annealing_temp_input.clear()
                self.annealing_temp_input.addItems(unique_annealing_temp)
                if select_all:
                    self.annealing_temp_input.select_all()
                else:
                    self.annealing_temp_input.select_from_list(previous_annealing_temp)
            if self.tab_config.get("sensor_id", False):
                self.update_unique_sensor_id()
        else:
            if self.annealing_temp_input is not None:
                self.annealing_temp_input.clear()
        
        
    def update_unique_sensor_id(self, select_all=False):
        # Save previous selected sensor ID to select it again after filtering
        previous_sensor_id = self.sensor_id_input.get_selected_items()
        
        if self.database is not None:
            mask = self.get_fiter_mask(["campaign", "measurement_type", "annealing_temp"])
            
            unique_sensor_id = self.database[mask].index.get_level_values("sensor_id").unique().tolist()
            if self.sensor_id_input is not None:
                self.sensor_id_input.clear()
                self.add_sensors_with_info(self.sensor_id_input, self.database[mask], unique_sensor_id, previous_sensor_id, select_all)
        else:
            if self.sensor_id_input is not None:
                self.sensor_id_input.clear()
                
                
    def update_unique_sensor_id_fr(self, select_all=False):
        previous_sensor_id_fr = self.sensor_id_fr_input.get_selected_items()
        if self.database is not None:
            mask = self.get_fiter_mask(["measurement_type", "annealing_temp", "thickness"])

            # Restrict to only the DoubleIrrNeutron2025 campaign
            mask &= self.database.index.get_level_values("campaign").isin(["DoubleIrrNeutron2025"])
            df_filtered = self.database[mask]
            unique_sensor_id_fr = df_filtered.index.get_level_values("sensor_id").unique().tolist()
            if self.sensor_id_fr_input is not None:
                self.sensor_id_fr_input.clear()
                self.add_sensors_with_info(self.sensor_id_fr_input, df_filtered, unique_sensor_id_fr, previous_sensor_id_fr, select_all)

            self.update_unique_sensor_id_sr()
        else:
            if self.sensor_id_fr_input is not None:
                self.sensor_id_fr_input.clear()
    
    
    def update_unique_sensor_id_sr(self, select_all=False):
        previous_sensor_id_sr = self.sensor_id_sr_input.get_selected_items()
        if self.plot_only_second_round_of_DI_input.isChecked():
            if self.database is not None:
                mask = self.get_fiter_mask(["measurement_type", "annealing_temp", "thickness"])
                # Restrict to only the DoubleIrrSRNeutron2025 campaign
                mask &= self.database.index.get_level_values("campaign").isin(["DoubleIrrSRNeutron2025"])
                df_filtered = self.database[mask]
                
                unique_sensor_id_sr = df_filtered.index.get_level_values("sensor_id").unique().tolist()
                if self.sensor_id_sr_input is not None:
                    self.add_sensors_with_info(self.sensor_id_sr_input, df_filtered, unique_sensor_id_sr, previous_sensor_id_sr, select_all)
                    
                self.update_unique_sensor_id_hf()
            else:
                if self.sensor_id_sr_input is not None:
                    self.sensor_id_sr_input.clear()
        else:
            if self.database is not None:
                sensor_id_fr = self.sensor_id_fr_input.get_selected_items()
                if self.sensor_id_sr_input is not None:
                    self.sensor_id_sr_input.clear()
                    
                # All possible SR sensor IDs from database
                df_filtered = self.database[self.database["Blacklisted"] == False]
                valid_ids = df_filtered.index.get_level_values("sensor_id").unique().tolist()

                # Generate SR IDs from FR IDs
                unique_sensor_id_sr = []
                for sid in sensor_id_fr:
                    for hm in VALID_HALFMOONS:
                        if sid.endswith("_" + hm):
                            sr_candidate = sid.replace("_" + hm, "_SR_" + hm)
                            if sr_candidate in valid_ids:
                                unique_sensor_id_sr.append(sr_candidate)
                            break  # stop checking once a halfmoon is matched
                    
                if self.sensor_id_sr_input is not None:
                    self.add_sensors_with_info(self.sensor_id_sr_input, df_filtered, unique_sensor_id_sr, previous_sensor_id_sr, select_all)
                self.update_unique_sensor_id_hf()
            else:
                if self.sensor_id_sr_input is not None:
                    self.sensor_id_sr_input.clear()
        
    
    def update_unique_sensor_id_hf(self, select_all=False):
        # Get unique sensor IDs from campaigns other than DoubleIrrNeutron2025 and DoubleIrrSRNeutron2025
        campaigns = self.campaign_input.get_selected_items()
        campaigns = [c for c in campaigns if c in ["HighFluenceIrrNeutron2023"]]
        
        previous_sensor_id_hf = self.sensor_id_hf_input.get_selected_items()
        if self.database is not None:
            # Get sensor ID from double irradiation measurements
            sensor_id_sr = self.sensor_id_sr_input.get_selected_items()
            if not sensor_id_sr:
                self.sensor_id_hf_input.clear()
                return
      
            # Get corresponding fluences from double irradiation measurements
            fluences = self.database.index.get_level_values("fluence")[
                self.database.index.get_level_values("sensor_id").isin(sensor_id_sr)
            ].unique().tolist()

            thickness = self.database.index.get_level_values("thickness")[
                self.database.index.get_level_values("sensor_id").isin(sensor_id_sr)
            ].unique().tolist()
            
            annealing_temp = self.database["annealing_temp"][
                self.database.index.get_level_values("sensor_id").isin(sensor_id_sr)
            ].unique().tolist()

            # Create mask for HF sensors
            mask = (
                (self.database.index.get_level_values("campaign").isin(campaigns)) &
                (self.database.index.get_level_values("thickness").isin(thickness)) &
                (self.database["annealing_temp"].isin(annealing_temp))
            )
            
            # Apply fluence filter only if HighFluenceIrrNeutron2023 campaign is the only selected campaign expect for DI
            if set(campaigns) == {"HighFluenceIrrNeutron2023"}:
                mask &= self.database.index.get_level_values("fluence").isin(fluences)

            # Extract HF sensor IDs
            unique_sensor_id_hf = self.database[mask].index.get_level_values("sensor_id").unique().tolist()
            df_filtered = self.database[mask]
            # Update HF dropdown
            self.add_sensors_with_info(self.sensor_id_hf_input, df_filtered, unique_sensor_id_hf, previous_sensor_id_hf, select_all)
        else:
            if self.sensor_id_hf_input is not None:
                self.sensor_id_hf_input.clear()
                
    def update_unique_sensor_id_lf(self, select_all=False):
        previous_sensor_id_lf = self.sensor_id_lf_input.get_selected_items()
        campaigns = self.campaign_input.get_selected_items()
        campaigns = [c for c in campaigns if c in ["LowFluenceIrrNeutron2025"]]
        
        if self.database is not None:
            mask = self.get_fiter_mask(["measurement_type", "annealing_temp", "thickness"])

            # Restrict to only the LowFluenceIrrNeutron2025 campaign
            mask &= self.database.index.get_level_values("campaign").isin(campaigns)
            df_filtered = self.database[mask]
            unique_sensor_id_lf = df_filtered.index.get_level_values("sensor_id").unique().tolist()
            if self.sensor_id_lf_input is not None:
                self.sensor_id_lf_input.clear()
                self.add_sensors_with_info(self.sensor_id_lf_input, df_filtered, unique_sensor_id_lf, previous_sensor_id_lf, select_all)
        else:
            if self.sensor_id_lf_input is not None:
                self.sensor_id_lf_input.clear()
            
                
    def add_sensors_with_info(self, target_input, df_filtered, sensor_ids, previous_selection, select_all=False):
        """
        Add sensors to a target combo box with info text (fluence, thickness, annealing_temp).
        """
        target_input.clear()

        for sid in sensor_ids:
            subdf = df_filtered.xs(sid, level="sensor_id", drop_level=False)

            # Extract unique values
            fluence = subdf.index.get_level_values("fluence").unique().tolist()
            thickness = subdf.index.get_level_values("thickness").unique().tolist()
            annealing_temp = subdf["annealing_temp"].unique().tolist()

            # Format into a string (pick first if only one exists)
            info_parts = []
            if fluence: info_parts.append(f"{fluence[0]:.1e}".replace("e+", "e"))
            if thickness: info_parts.append(f"{thickness[0]}µm")
            if annealing_temp: info_parts.append(f"{annealing_temp[0]}°C")

            # Add items with their info text
            target_input.addItem(
                sid,
                show_sensor_info_text=True,
                sensor_info_text=info_parts
            )

        # Restore selection state
        if select_all:
            target_input.select_all()
        else:
            target_input.select_from_list(previous_selection)

        
                
    def update_unique_annealing_time(self, select_all=False):
        # Save previous selected annealing time to select it again after filtering
        previous_annealing_time = self.annealing_time_input.get_selected_items()
        unique_annealing_times = []
        if self.database is not None:
            # Get unique annealing times for the given campaign and measurement type
            mask = self.get_fiter_mask(["sensor_id"])
            
            unique_annealing_times = self.database[mask].index.get_level_values("annealing_time").unique().tolist()

            if self.annealing_time_input is not None:
                self.annealing_time_input.clear()
                self.annealing_time_input.addItems(sort_annealing_time(unique_annealing_times))
                if select_all:
                    self.annealing_time_input.select_all()
                else:
                    self.annealing_time_input.deselect_all()
                self.annealing_time_input.select_from_list(previous_annealing_time)
        else:
            if self.annealing_time_input is not None:
                self.annealing_time_input.clear()
            
            
    def update_logy_i_tot_check(self):
        measurement = self.measurement_input.currentText()
        if measurement == "IV":
            self.plot_settings_tab.logy_input.setChecked(False)
            self.i_tot_check.setDisabled(False)
        elif measurement == "CV":
            self.plot_settings_tab.logy_input.setChecked(False)
            self.i_tot_check.setDisabled(True)
            

    def refresh_unique_lists_plot_tab(self):
        # Load database and extract unique values
        self.load_database()
        
        # reset all comboboxes
        if self.tab_config.get("campaign", False):
            previous_campaign = self.campaign_input.get_selected_items()
            self.campaign_input.clear()
            self.campaign_input.addItems(self.CAMPAIGNS)
            self.campaign_input.select_from_list(previous_campaign)
        if self.tab_config.get("measurement", False):
            previous_measurement = self.measurement_input.currentText()
            self.measurement_input.clear()
            self.measurement_input.addItems(MEASUREMENTS)
            self.measurement_input.setCurrentText(previous_measurement)
        if self.tab_config.get("measurement_type", False):
            previous_measurement_type = self.measurement_type_input.get_selected_items()
            self.measurement_type_input.clear()
            self.measurement_type_input.addItems(self.MEASUREMENT_TYPE)
            self.measurement_type_input.select_from_list(previous_measurement_type)
        if self.tab_config.get("annealing_temp", False):
            previous_annealing_temp = self.annealing_temp_input.get_selected_items()
            self.annealing_temp_input.clear()
            self.annealing_temp_input.addItems(self.ANNEALING_TEMP)
            self.annealing_temp_input.select_from_list(previous_annealing_temp)
        if self.tab_config.get("annealing_time", False):
            previous_annealing_time = self.annealing_time_input.get_selected_items()
            self.annealing_time_input.clear()
            self.annealing_time_input.addItems(self.ANNEALING_TIME)
            self.annealing_time_input.select_from_list(previous_annealing_time)
        if self.tab_config.get("sensor_id", False):
            previous_sensor_id = self.sensor_id_input.get_selected_items()
            self.sensor_id_input.clear()
            self.sensor_id_input.addItems(self.SENSOR_ID)
            self.sensor_id_input.select_from_list(previous_sensor_id)
        if self.tab_config.get("thickness", False):
            previous_thickness = self.thickness_input.get_selected_items()
            self.thickness_input.clear()
            self.thickness_input.addItems(self.THICKNESS)
            self.thickness_input.select_from_list(previous_thickness)
        if self.tab_config.get("fluence", False):
            previous_fluence = self.fluence_input.get_selected_items()
            self.fluence_input.clear()
            self.fluence_input.addItems(self.FLUENCE)
            self.fluence_input.select_from_list(previous_fluence)
        if self.tab_config.get("voltage", False):
            previous_voltage = self.voltage_input.currentText()
            self.voltage_input.clear()
            self.voltage_input.addItems(VOLTAGE_LIST)
            # self.voltage_input.setCurrentIndex(VOLTAGE_LIST.index("600"))
            self.voltage_input.setCurrentText(previous_voltage)
            

    def display_plot(self):
        """Display the generated plot in the canvas while ensuring it fits within the layout."""

        # Always work with a list of axes, whether single or multiple
        if isinstance(self.ax, (list, tuple, np.ndarray)):
            axes = self.ax
        else:
            axes = [self.ax]
            
        # Store custom tick labels BEFORE applying any settings (for average ratio plot)
        stored_xtick_positions = []
        stored_xtick_labels = []
        for ax in axes:
            positions = ax.get_xticks()
            labels = [label.get_text() for label in ax.get_xticklabels()]
            stored_xtick_positions.append(positions)
            stored_xtick_labels.append(labels)
            
        # Apply settings to all axes
        for index_axes, ax in enumerate(axes):
            # --- Title ---
            if self.plot_settings_tab.title_check.isChecked():
                if self.plot_settings_tab.title_input.text() != "":
                    ax.set_title(self.plot_settings_tab.title_input.text(), fontsize=5)
                else:
                    ax.set_title(ax.get_title(), fontsize=5)
            else:
                ax.set_title("")

            # --- Labels ---
            if self.plot_settings_tab.xlabel_input.text() != "":
                ax.set_xlabel(self.plot_settings_tab.xlabel_input.text(),
                            fontsize=self.plot_settings_tab.fontsize_slider.value(), fontweight='bold')
            else:
                ax.set_xlabel(ax.get_xlabel(),
                            fontsize=self.plot_settings_tab.fontsize_slider.value(), fontweight='bold')

            if self.plot_settings_tab.ylabel_input.text() != "":
                ax.set_ylabel(self.plot_settings_tab.ylabel_input.text(),
                            fontsize=self.plot_settings_tab.fontsize_slider.value(), fontweight='bold')
            else:
                ax.set_ylabel(ax.get_ylabel(),
                            fontsize=self.plot_settings_tab.fontsize_slider.value(), fontweight='bold')

            # --- Log scales ---
            if len(axes) > 1:
                if index_axes == 0 and hasattr(self, "split_x_axis_input") and self.split_x_axis_input.isChecked():
                    ax.set_xscale("linear")
                else:
                    ax.set_xscale("log" if self.plot_settings_tab.logx_input.isChecked() else "linear")
            else:
                ax.set_xscale("log" if self.plot_settings_tab.logx_input.isChecked() else "linear")
            
            ax.set_yscale("log" if self.plot_settings_tab.logy_input.isChecked() else "linear")

            # --- Axis limits ---
            if self.plot_settings_tab.xlim_min_input.text() != "":
                if len(axes) > 1 and index_axes == 1:
                    ax.set_xlim(float(self.plot_settings_tab.xlim_min_input.text()),
                                float(self.plot_settings_tab.xlim_max_input.text()))
            if self.plot_settings_tab.ylim_min_input.text() != "":
                ax.set_ylim(float(self.plot_settings_tab.ylim_min_input.text()),
                            float(self.plot_settings_tab.ylim_max_input.text()))
            elif self.plot_settings_tab.ylim_max_input.text() == "" and hasattr(self, 'plot_ratio_DI_vs_HF_input') and self.plot_ratio_DI_vs_HF_input.isChecked():
                ax.set_ylim(0, 2)

            ax.grid(True, linestyle=":", linewidth=0.3)

            # --- Line & marker properties ---
            for line in ax.get_lines():
                line.set_markersize(self.plot_settings_tab.marker_size_slider.value())
                line.set_linewidth(self.plot_settings_tab.line_width_slider.value())
                
            # Error bar arms (LineCollection)
            for coll in ax.collections:
                if isinstance(coll, LineCollection):
                    coll.set_linewidth(self.plot_settings_tab.line_width_slider.value())

            # Error bar caps (Line2D without markers)
            for line in ax.lines:
                if line.get_marker() == "":  # caps have no marker
                    line.set_linewidth(self.plot_settings_tab.line_width_slider.value())
                    
            # Axis break diagonal cuts (if any)
            for line in ax.get_lines():
                if line.get_transform() == ax.transAxes:  # only transform relative to axes
                    line.set_linewidth(self.plot_settings_tab.line_width_slider.value())

            # --- Spine properties ---
            for spine in ax.spines.values():
                spine.set_linewidth(self.plot_settings_tab.border_width_slider.value())

            # --- Tick parameters ---
            ax.tick_params(axis='x', which='major',
                        size=self.plot_settings_tab.tick_size_major_slider.value(),
                        width=self.plot_settings_tab.tick_width_major_slider.value())
            ax.tick_params(axis='x', which='minor',
                        size=self.plot_settings_tab.tick_size_minor_slider.value(),
                        width=self.plot_settings_tab.tick_width_minor_slider.value())
            ax.tick_params(axis='y', which='major',
                        size=self.plot_settings_tab.tick_size_major_slider.value(),
                        width=self.plot_settings_tab.tick_width_major_slider.value())
            ax.tick_params(axis='y', which='minor',
                        size=self.plot_settings_tab.tick_size_minor_slider.value(),
                        width=self.plot_settings_tab.tick_width_minor_slider.value())

            # Tick label sizes
            ax.tick_params(axis='x', which='major',
                        labelsize=self.plot_settings_tab.tick_label_size_slider.value())
            ax.tick_params(axis='y', which='major',
                        labelsize=self.plot_settings_tab.tick_label_size_slider.value())
            ax.xaxis.get_offset_text().set_fontsize(self.plot_settings_tab.tick_label_size_slider.value())
            ax.yaxis.get_offset_text().set_fontsize(self.plot_settings_tab.tick_label_size_slider.value())

            # --- Custom text box ---
            if self.plot_settings_tab.custom_text_check.isChecked():
                ax.text(
                    0.94, 0.1, self.plot_settings_tab.custom_text_input.text(),
                    transform=ax.transAxes, ha="right", va="bottom",
                    fontsize=self.plot_settings_tab.text_box_slider.value(),
                    bbox=dict(facecolor="white", alpha=1, edgecolor="none", pad=3)
                )

            # --- Legend ---
            if self.plot_settings_tab.legend_check.isChecked():
                if self.plot_settings_tab.legend_size_slider.value() == 1:
                    fontsize = 3
                    desired_markerscale = 2 # marker size in points
                elif self.plot_settings_tab.legend_size_slider.value() == 2:
                    fontsize = 3.5
                    desired_markerscale = 2.25 # marker size in points
                elif self.plot_settings_tab.legend_size_slider.value() == 3:
                    fontsize = 4
                    desired_markerscale = 2.5 # marker size in points
                elif self.plot_settings_tab.legend_size_slider.value() == 4:
                    fontsize = 4.5
                    desired_markerscale = 2.75 # marker size in points
                elif self.plot_settings_tab.legend_size_slider.value() == 5:
                    fontsize = 5
                    desired_markerscale = 3 # marker size in points
                elif self.plot_settings_tab.legend_size_slider.value() == 6:
                    fontsize = 6
                    desired_markerscale = 3.5 # marker size in points
                elif self.plot_settings_tab.legend_size_slider.value() == 7:
                    fontsize = 7
                    desired_markerscale = 4 # marker size in points
                    
                current_markerscale = self.plot_settings_tab.marker_size_slider.value()
                markerscale = desired_markerscale / current_markerscale
                    
                legend = ax.legend(
                    fontsize=fontsize, markerscale=markerscale, 
                    loc=self.plot_settings_tab.legend_placement_input.currentText(), shadow=False,
                    frameon=True, borderaxespad=1.2, 
                    fancybox=True, framealpha=0.7,
                    handlelength=2.4,
                    labelspacing=0.5
                )
                    
                legend.get_frame().set_linewidth(0.3)
                legend.get_frame().set_edgecolor("black")
            else:
                leg = ax.get_legend()
                if leg is not None:
                    leg.remove()

            ax.yaxis.set_minor_formatter(NullFormatter())
            ax.xaxis.set_minor_formatter(NullFormatter())
            
            # Restore custom x-tick labels for average ratio plot (after all settings applied)
            if (self.tab_config.get("plot_ratio_DI_vs_HF", False) and 
                hasattr(self, 'plot_average_ratio_DI_vs_HF_input') and 
                self.plot_average_ratio_DI_vs_HF_input.isChecked()):
                # Check if we have stored custom labels (non-default labels)
                if stored_xtick_labels[index_axes] and any(label for label in stored_xtick_labels[index_axes] if label and '\n' in label):
                    # Reapply the custom positions and labels
                    ax.set_xticks(stored_xtick_positions[index_axes])
                    ax.set_xticklabels(stored_xtick_labels[index_axes], 
                                      rotation=0, 
                                      ha='center',
                                      fontsize=self.plot_settings_tab.tick_label_size_slider.value())
                # Remove x-axis tick marks 
                ax.tick_params(axis='x', which='minor', length=0)
                # ax.xaxis.set_minor_locator(None)

        # --- Store original limits for zoom reset (before canvas refresh) ---
        if isinstance(self.ax, (list, tuple, np.ndarray)):
            self._original_xlim = [ax.get_xlim() for ax in self.ax]
            self._original_ylim = [ax.get_ylim() for ax in self.ax]
        else:
            self._original_xlim = [self.ax.get_xlim()]
            self._original_ylim = [self.ax.get_ylim()]

        # --- Refresh canvas ---
        if self.canvas is not None:
            self.plot_container_layout.removeWidget(self.canvas)
            self.canvas.deleteLater()

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.plot_container_layout.addWidget(self.canvas)

        with warnings.catch_warnings():
            warnings.simplefilter("error", UserWarning)
            try:
                self.fig.set_constrained_layout(True)
                self.canvas.draw()
            except UserWarning:
                print("\nCan't fit legend in the plot, too many input labels to legend!\n")

        # Re-attach the rectangle selector to the new canvas
        self._setup_rectangle_selector()

    ### --- Zoom mode ---
    def _on_rectangle_select(self, eclick, erelease):
        """Callback fired when the user finishes drawing a rectangle."""
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        if x1 is None or x2 is None or y1 is None or y2 is None:
            return

        # Determine the selected region boundaries
        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])

        # Apply to all axes (handles split-axis case)
        if isinstance(self.ax, (list, tuple, np.ndarray)):
            axes = self.ax
        else:
            axes = [self.ax]

        for ax in axes:
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)

        self.canvas.draw_idle()


    def _setup_rectangle_selector(self):
        """Create (or recreate) the RectangleSelector on the current axes."""
        # Determine target axis (use first axis if split)
        if isinstance(self.ax, (list, tuple, np.ndarray)):
            target_ax = self.ax[0]
        else:
            target_ax = self.ax

        self._rect_selector = RectangleSelector(
            target_ax,
            self._on_rectangle_select,
            useblit=True,
            button=[1],           # left mouse button only
            interactive=False,    # disappears after selection
            minspanx=5,           # minimum pixel span to register
            minspany=5,
            spancoords="pixels",
            props=dict(facecolor="lightblue", edgecolor="blue",
                    alpha=0.3, linewidth=1.5),
        )
        self._rect_selector.set_active(
            self.plot_settings_tab.zoom_button.isChecked()
        )


    def _toggle_zoom_mode(self, enabled):
        """Enable or disable the RectangleSelector when the Zoom button is toggled."""
        if self._rect_selector is not None:
            self._rect_selector.set_active(enabled)

        # Visual feedback: change button style when active
        if enabled:
            self.plot_settings_tab.zoom_button.setStyleSheet(
                "background-color: #4a90d9; color: white;"
            )
        else:
            self.plot_settings_tab.zoom_button.setStyleSheet("")


    def _reset_zoom(self):
        """Restore the original axis limits saved at plot time."""
        if self._original_xlim is None or self._original_ylim is None:
            return

        if isinstance(self.ax, (list, tuple, np.ndarray)):
            axes = self.ax
        else:
            axes = [self.ax]

        for i, ax in enumerate(axes):
            if i < len(self._original_xlim):
                ax.set_xlim(self._original_xlim[i])
                ax.set_ylim(self._original_ylim[i])

        self.canvas.draw_idle()
