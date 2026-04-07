from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, 
    QCheckBox, QFileDialog, QSizePolicy, QTabWidget
)
import matplotlib.pyplot as plt
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.ticker import NullFormatter
from matplotlib.widgets import RectangleSelector
import pandas as pd
import numpy as np
import math
import os

from config import RC_PLOT_STYLE, MARKERSIZE, FILLSTYLE, LEGEND_SIZE, LABEL_MODE
from config import DEFAULT_DATABASE_PATH, DEFAULT_DIR_SATURATION_VOLTAGE_RESULTS, END_INV_CAPACITANCE_2_ASSUMPTION
from config import COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED, COLOR_SAT_V_FIT_RESULTS_ANALYSED
from config import END_CAP_ERROR_UP, END_CAP_ERROR_DOWN, PLATEAU_ERROR_UP, PLATEAU_ERROR_DOWN, MANUAL_UPPER_LINE_ERROR_UP, MANUAL_UPPER_LINE_ERROR_DOWN
from config import SAT_V_ERROR_UP_TCT, SAT_V_ERROR_DOWN_TCT
from Utils.dataframe_helper import get_saturation_voltage_df_list_sensor
from Utils.saturation_voltage_fit_helper import find_saturation_voltage_from_curvature_fit, find_intersection_of_two_lines, calculate_saturation_voltage_with_uncertainty
from Utils.CheckableComboBox import CheckableComboBox
from Utils.create_database_helper import sort_annealing_time, annealing_sort_key
from GUI.SettingsPlot import SettingsPlot


class SaturationVoltageFitTab(QWidget):
    def __init__(self):
        super().__init__()# Load database and extract unique values
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
            # Get unique values from index levels and columns
            self.CAMPAIGNS = sorted(self.database.index.get_level_values('campaign').unique().tolist())
            self.ANNEALING_TEMP = sorted([str(temp) for temp in self.database["annealing_temp"].unique().tolist()])
            self.ANNEALING_TIME = sort_annealing_time(self.database.index.get_level_values('annealing_time').unique().tolist())
            # self.ANNEALING_TIME = self.database.index.get_level_values('annealing_time').unique().tolist()
            self.MEASUREMENT_TYPE = sorted(self.database['type'].unique().tolist())
        else:
            # Fallback to empty lists if database doesn't exist
            self.database = None
            self.CAMPAIGNS = []
            self.ANNEALING_TEMP = []
            self.ANNEALING_TIME = []
            self.MEASUREMENT_TYPE = []

        self.interactive_saturation_voltage_fit_tab()
        
        # Initialize the fit start and stop values
        self.low_fit_start_value = None
        self.low_fit_stop_value = None
        self.high_fit_start_value = None
        self.high_fit_stop_value = None

        # Initialise upper line fit parameters
        self.upper_line_fit_params = None
        
        # Initialise previously clicked low and high fit start and stop values and manual upper line fit parameters
        self.previously_clicked_low_fit_start_value = None
        self.previously_clicked_low_fit_stop_value = None
        self.previously_clicked_high_fit_start_value = None
        self.previously_clicked_high_fit_stop_value = None
        self.previously_clicked_manual_upper_line_x_value = None
        self.previously_clicked_manual_upper_line_y_value = None
        self.previously_clicked_manual_upper_line_rotation_angle = None

        # Track when SHIFT key is pressed
        self.shift_pressed = False

        # Zoom state
        self._rect_selector = None
        self._original_xlim = None
        self._original_ylim = None
        
        # Track if the endcap assumption fit mode is activated
        self.endcap_assumption_activated = False
        self.manual_upper_fit_activated = False
        

    def interactive_saturation_voltage_fit_tab(self):
        # Layout for the saturation voltage
        self.saturation_voltage_fit_tab_layout = QHBoxLayout(self)

        # Left side: Plot area inside a container
        self.fig = Figure(figsize=(6, 4), dpi=300)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.saturation_voltage_fit_tab_layout.addWidget(self.canvas)

        # Right side: Input area
        self.input_tabs = QTabWidget()
        self.saturation_voltage_fit_tab_layout.addWidget(self.input_tabs)  

        # Tab Saturation Voltage
        self.plot_diodes_tab = QWidget()
        self.saturation_voltage_fit_layout = QVBoxLayout(self.plot_diodes_tab)
        
        # Save path
        self.save_path_input = QLineEdit()
        self.save_path_input.setText(DEFAULT_DIR_SATURATION_VOLTAGE_RESULTS)
        self.save_path_button = QPushButton("Browse")
        self.save_path_button.clicked.connect(self.select_save_path)
        self.saturation_voltage_fit_layout.addWidget(QLabel("Save Path:"))
        self.saturation_voltage_fit_layout.addWidget(self.save_path_input)
        self.saturation_voltage_fit_layout.addWidget(self.save_path_button)

        # Add save button to save the plot
        self.save_plot_button = QPushButton("Save Plot")
        self.save_plot_button.clicked.connect(self.save_plot)
        self.saturation_voltage_fit_layout.addWidget(self.save_plot_button)

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
        self.saturation_voltage_fit_layout.addWidget(QLabel("Fig size save (ratio):"))
        self.saturation_voltage_fit_layout.addWidget(self.fig_size_save_input)

        # Campaign
        self.campaign_input = QComboBox()
        self.campaign_input.addItems(self.CAMPAIGNS)
        self.campaign_input.currentTextChanged.connect(self.update_unique_annealing_temp)
        self.saturation_voltage_fit_layout.addWidget(QLabel("Campaign:"))
        self.saturation_voltage_fit_layout.addWidget(self.campaign_input)

        # Use TCT Checkbox
        self.fit_from_TCT_check = QCheckBox("Fit from TCT | CC vs V")
        self.saturation_voltage_fit_layout.addWidget(self.fit_from_TCT_check)
        self.fit_from_TCT_check.stateChanged.connect(self.update_unique_annealing_temp)

        # Measurement Type
        self.measurement_type_input = QComboBox()
        self.measurement_type_input.addItems(self.MEASUREMENT_TYPE)
        try:
            self.measurement_type_input.setCurrentIndex(self.MEASUREMENT_TYPE.index("onPCB"))
        except:
            pass
        self.measurement_type_input.currentIndexChanged.connect(self.update_unique_annealing_temp)
        self.saturation_voltage_fit_layout.addWidget(QLabel("Measurement Type:"))
        self.saturation_voltage_fit_layout.addWidget(self.measurement_type_input)

        # CheckableComboBox for ANNEALING_TEMP
        annealing_temp_header_layout = QHBoxLayout()
        annealing_temp_header_layout.setSpacing(5)
        annealing_temp_header_layout.addWidget(QLabel("Annealing Temperature:"))
        annealing_temp_select_all = QPushButton("Select All")
        annealing_temp_select_all.setFixedWidth(70)
        annealing_temp_select_all.setStyleSheet("font-size: 10px;")
        annealing_temp_deselect_all = QPushButton("Deselect All")
        annealing_temp_deselect_all.setFixedWidth(70) 
        self.annealing_temp_input = CheckableComboBox()
        self.annealing_temp_input.add_external_callback(self.update_unique_sensor_id)
        annealing_temp_deselect_all.setStyleSheet("font-size: 10px;")

        annealing_temp_header_layout.addWidget(annealing_temp_select_all)
        annealing_temp_header_layout.addWidget(annealing_temp_deselect_all)

        annealing_temp_select_all.clicked.connect(self.annealing_temp_input.select_all) 
        annealing_temp_deselect_all.clicked.connect(self.annealing_temp_input.deselect_all)

        self.saturation_voltage_fit_layout.addLayout(annealing_temp_header_layout)
        self.saturation_voltage_fit_layout.addWidget(self.annealing_temp_input)

        # Sensor ID
        sensor_layout = QHBoxLayout()
        sensor_layout.addWidget(QLabel("Sensor ID:"))
        self.sensor_id_input = CheckableComboBox()
        self.sensor_id_input.add_external_callback(self.update_unique_annealing_time)
        sensor_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_input.select_all))
        sensor_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_input.deselect_all))
        self.saturation_voltage_fit_layout.addLayout(sensor_layout)
        self.saturation_voltage_fit_layout.addWidget(self.sensor_id_input)
        self.saturation_voltage_fit_layout.addSpacing(5)

        # Annealing Time
        annealing_time_layout = QHBoxLayout()
        annealing_time_layout.addWidget(QLabel("Annealing Time:"))
        self.annealing_time_input = CheckableComboBox()
        annealing_time_layout.addWidget(QPushButton("Select All", clicked=self.annealing_time_input.select_all))
        annealing_time_layout.addWidget(QPushButton("Deselect All", clicked=self.annealing_time_input.deselect_all))
        self.saturation_voltage_fit_layout.addLayout(annealing_time_layout)
        self.saturation_voltage_fit_layout.addWidget(self.annealing_time_input)
        self.saturation_voltage_fit_layout.addSpacing(5)
        
        # Only iterate through the annealing times that are not fitted
        self.only_iterate_through_not_fitted_annealing_times = QCheckBox("Only iterate through non analysed annealing times")
        self.saturation_voltage_fit_layout.addWidget(self.only_iterate_through_not_fitted_annealing_times)
        self.saturation_voltage_fit_layout.addSpacing(5)
        

        # Plot Button
        self.interactive_sat_volt_button = QPushButton("Interactive Fit Saturation Voltage [F]")
        self.interactive_sat_volt_button.clicked.connect(self.interactive_saturation_voltage_fit)
        self.saturation_voltage_fit_layout.addWidget(self.interactive_sat_volt_button)
        self.saturation_voltage_fit_layout.addSpacing(5)
        
        # Line for design purpose
        line_input = QLabel("====================================")
        self.saturation_voltage_fit_layout.addWidget(line_input)        
        # Next Sensor Button
        self.next_sensor_button = QPushButton("Next Sensor [N]")
        self.next_sensor_button.clicked.connect(lambda: self.next_previous_sensor(next_sensor=True))
        self.saturation_voltage_fit_layout.addWidget(self.next_sensor_button)
        self.saturation_voltage_fit_layout.addSpacing(5)
        
        # Previous Sensor Button
        self.previous_sensor_button = QPushButton("Previous Sensor [P]")
        self.previous_sensor_button.clicked.connect(lambda: self.next_previous_sensor(next_sensor=False))
        self.saturation_voltage_fit_layout.addWidget(self.previous_sensor_button)
        self.saturation_voltage_fit_layout.addSpacing(5)

        # Line for design purpose
        line_input = QLabel("====================================")
        self.saturation_voltage_fit_layout.addWidget(line_input)  

        # Add text to explain the user response
        self.user_response_text = QLabel(
            """
            <table>
                <tr>
                    <td><b>Manual</b></td>
                    <td>--></td>
                    <td>(Ctrl +) Left + Right, (high) low lines</td>
                </tr>
                <tr>
                    <td><b>Fit (manual)</b></td>
                    <td>--></td>
                    <td>Fit within the selected range</td>
                </tr>
                <tr>
                    <td><b>Skip</b></td>
                    <td>--></td>
                    <td><b>Save</b> as 0V and go to next sensor</td>
                </tr>
                <tr>
                    <td><b>Fit OK</b></td>
                    <td>--></td>
                    <td><b>Save</b> and go to next sensor</td>
                </tr>
                <tr>
                    <td><b>Retry Auto Fit</b></td>
                    <td>--></td>
                    <td>Retry automatic fit</td>
                </tr>
            </table>
            """
        )
        self.saturation_voltage_fit_layout.addWidget(self.user_response_text)

        # User Response in interactive fit mode
        self.manual_fit_skip_buttons_layout = QHBoxLayout()
        self.manual_fit_button = QPushButton("Manual [1]")
        self.manual_fit_button.setEnabled(False)
        self.manual_fit_skip_buttons_layout.addWidget(self.manual_fit_button)
        self.fit_button = QPushButton("Fit [2]")
        self.fit_button.setEnabled(False)
        self.manual_fit_skip_buttons_layout.addWidget(self.fit_button)
        self.skip_button = QPushButton("Skip [3]")
        self.skip_button.setEnabled(False)
        self.manual_fit_skip_buttons_layout.addWidget(self.skip_button)
        self.saturation_voltage_fit_layout.addLayout(self.manual_fit_skip_buttons_layout)

        # Add buttons to add a manual interactive line for the upper fit
        self.manual_upper_fit_buttons_layout = QHBoxLayout()
        self.rotate_anti_clockwise_button = QPushButton("Rot. Left [A]")
        self.rotate_anti_clockwise_button.setEnabled(False)
        self.manual_upper_fit_buttons_layout.addWidget(self.rotate_anti_clockwise_button)
        self.manual_upper_line_button = QPushButton("Add Upper Line [S]")
        self.manual_upper_line_button.setEnabled(False)
        self.manual_upper_fit_buttons_layout.addWidget(self.manual_upper_line_button)
        self.rotate_clockwise_button = QPushButton("Rot. Right [D]")
        self.rotate_clockwise_button.setEnabled(False)
        self.manual_upper_fit_buttons_layout.addWidget(self.rotate_clockwise_button)
        self.saturation_voltage_fit_layout.addLayout(self.manual_upper_fit_buttons_layout)

        # Add buttons below for Fit OK and retry the automatic fit 
        self.fit_ok_retry_automatic_fit_buttons_layout = QHBoxLayout()
        self.fit_ok_button = QPushButton("Fit OK [SPACE]")
        self.fit_ok_button.setEnabled(False)
        self.fit_ok_retry_automatic_fit_buttons_layout.addWidget(self.fit_ok_button)
        self.endcap_assumption_button = QPushButton("EndCap [E]")
        self.endcap_assumption_button.setEnabled(False)
        self.fit_ok_retry_automatic_fit_buttons_layout.addWidget(self.endcap_assumption_button)
        self.retry_automatic_fit_button = QPushButton("Retry Auto [R]")
        self.retry_automatic_fit_button.setEnabled(False)
        self.fit_ok_retry_automatic_fit_buttons_layout.addWidget(self.retry_automatic_fit_button)
        self.saturation_voltage_fit_layout.addLayout(self.fit_ok_retry_automatic_fit_buttons_layout)
        self.saturation_voltage_fit_layout.addStretch(1)

        # Connect the buttons to the logic
        self.fit_ok_button.clicked.connect(self.save_and_go_to_next_sensor)
        self.manual_fit_button.clicked.connect(self.manual_fit_mode)
        self.fit_button.clicked.connect(self.find_saturation_voltage_from_user_defined_intervals)
        self.skip_button.clicked.connect(self.skip_sensor_and_go_to_next)
        self.retry_automatic_fit_button.clicked.connect(self.retry_automatic_fit)
        self.endcap_assumption_button.clicked.connect(self.endcap_assumption_fit_mode)
        self.manual_upper_line_button.clicked.connect(self.manual_upper_fit_mode)
        self.rotate_anti_clockwise_button.clicked.connect(lambda: self.rotate_manual_upper_line_button(rotation_direction="anti_clockwise"))
        self.rotate_clockwise_button.clicked.connect(lambda: self.rotate_manual_upper_line_button(rotation_direction="clockwise"))

        # Add the Plot Diodes tab to the QTabWidget
        self.input_tabs.addTab(self.plot_diodes_tab, "Fit Saturation Voltage")
        
        # Settings tab
        self.plot_settings_tab = SettingsPlot(self.display_plot)
        self.input_tabs.addTab(self.plot_settings_tab, "Plot Settings")

        # Connect zoom buttons from the settings tab
        self.plot_settings_tab.zoom_button.toggled.connect(self._toggle_zoom_mode)
        self.plot_settings_tab.reset_zoom_button.clicked.connect(self._reset_zoom)

        # Add input tabs to the plot tab
        self.saturation_voltage_fit_tab_layout.addWidget(self.input_tabs)
        self.saturation_voltage_fit_tab_layout.setStretch(0, 7)
        self.saturation_voltage_fit_tab_layout.setStretch(1, 1)

        # Trigger update annealing temperature  
        self.update_unique_annealing_temp()
        
    
    def interactive_saturation_voltage_fit(self):
        # Access the first index
        self.plot_first_index = True

        # Get input values
        self.campaign = self.campaign_input.currentText()
        self.fit_from_TCT = self.fit_from_TCT_check.isChecked()
        self.measurement_type = self.measurement_type_input.currentText()
        self.sensor_id = self.sensor_id_input.get_selected_items()
        self.annealing_temp = [float(temp) for temp in self.annealing_temp_input.get_selected_items()]
        self.annealing_time = self.annealing_time_input.get_selected_items()

        # Load the DataFrame from the pickle file
        self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)

        df = self.database[
                (self.database.index.get_level_values('annealing_time').isin(self.annealing_time)) &
                (self.database.index.get_level_values("campaign").isin([self.campaign])) &
                (self.database.index.get_level_values("sensor_id").isin(self.sensor_id)) & 
                (self.database["annealing_temp"].isin(self.annealing_temp)) &
                (self.database["type"] == self.measurement_type) &
                (self.database['Blacklisted']==False) &
                ((self.database['file_TCT'] != "None") if self.fit_from_TCT else (self.database['file_CV'] != "None"))
            ].copy()
        
        if self.only_iterate_through_not_fitted_annealing_times.isChecked():
            col = 'sat_V_TCT' if self.fit_from_TCT else 'sat_V_CV'
            df = df[df[col].isna()]
        
        # Sort df by sensor_id from checkable combo box and then annealing_time in ascending order starting from noadd to higher 
        sensor_order_map = {sensor: idx for idx, sensor in enumerate(self.sensor_id)}
        
        # Ensure index levels are accessible as columns
        df_reset = df.reset_index()

        df_reset = df_reset.sort_values(
            by=["sensor_id", "annealing_time"],
            key=lambda col: col.map(
                lambda v: sensor_order_map[v] if col.name == "sensor_id" else annealing_sort_key(v)
            )
        )

        # Put them back into the index
        df = df_reset.set_index(df.index.names)
        
        # Get sensors, thickness and fluence 
        self.list_annealing_time = df.index.get_level_values("annealing_time").tolist()
        self.sensor_ids = df.index.get_level_values("sensor_id").tolist()
        self.list_thickness = df.index.get_level_values("thickness").tolist()
        self.list_fluence = df.index.get_level_values("fluence").tolist()
        
        self.current_sensor_index = 0

        self.list_sensor_id, self.cv_tct_df = get_saturation_voltage_df_list_sensor(df=df, measrement_type=self.measurement_type, fit_from_TCT=self.fit_from_TCT)
            
        self.next_previous_sensor(next_sensor=True)
        
        
    # --------------------------------------------------------------------------------------------------------------------------------------------
    #                                                                Fit Logic                                                                   #
    # --------------------------------------------------------------------------------------------------------------------------------------------
        
        
    def next_previous_sensor(self, next_sensor):
        """Move to the next sensor in the list and re-plot."""
        # Update the annealing time for checkboxes to show the correct fitted status
        self.update_unique_annealing_time()
        
        # Reset the endcap assumption activation
        self.endcap_assumption_activated = False

        # Reset the manual upper fit activation
        self.manual_upper_fit_activated = False

        # Reset upper line fit parameters
        self.upper_line_fit_params = None

        if self.plot_first_index == True:
            self.plot_first_index = False
        else:
            if next_sensor == True:
                self.current_sensor_index += 1
            else:
                self.current_sensor_index -= 1
        
        if self.sensor_ids and 0 <= self.current_sensor_index < len(self.sensor_ids):
            # self.output_text.setPlainText("")
            self.single_sensor_annealing_time = self.list_annealing_time[self.current_sensor_index]
            self.single_sensor_id = self.sensor_ids[self.current_sensor_index]
            self.single_sensor_thickness = self.list_thickness[self.current_sensor_index]
            self.single_sensor_fluence = self.list_fluence[self.current_sensor_index] 
            
            try:
                self.fig, self.ax = self.plot_saturation_voltage_single_sensor(df=self.cv_tct_df, fit_from_TCT=self.fit_from_TCT)
                # Store the current y|x-axis limits
                self.y_min, self.y_max = self.ax.get_ylim()
                self.x_min, self.x_max = self.ax.get_xlim()
                # for saturation voltage, low and high fit labels to fit nicely with the plot
                self.line_label_y_pos = self.y_min + (self.y_max - self.y_min) * 0.02
            except:
                self.fig, self.ax = plt.subplots(dpi=300)
                self.ax.set_title("No data found for the selected criteria")
                # self.output_text.setPlainText("No data found for the selected criteria")

            # Get the mask for the current sensor to find it in the database
            self.mask_single_sensor = (
                (self.database.index.get_level_values('sensor_id') == self.single_sensor_id) &
                (self.database.index.get_level_values('campaign') == self.campaign) &
                (self.database.index.get_level_values('annealing_time') == self.single_sensor_annealing_time) &
                (self.database['type'] == self.measurement_type) &
                (self.database['Blacklisted']==False) &
                ((self.database['file_TCT'] != "None") if self.fit_from_TCT else (self.database['file_CV'] != "None"))
            )

            # Check if the sensor has already been analysed
            self.saturation_voltage_fit_status = self.check_sensor_analysis_status() 

            if self.saturation_voltage_fit_status == "Not_Analysed" or self.saturation_voltage_fit_status == "Auto":
                # If the sensor has not been analysed or automatic fit has already been performed, do automatic fit to find the saturation voltage or to reproduce the previous fit
                self.automatic_fit_saturation_voltage()
            elif self.saturation_voltage_fit_status in ["Manual_Analysed", "Manual_Analysed_EndCap", "Manual_Analysed_UpperLine"]:
                # If the sensor has been manually fitted, plot the low and high fit lines with the fit results
                self.activate_interactive_lines_for_manual_fit()
                self.find_saturation_voltage_from_user_defined_intervals()
            elif self.saturation_voltage_fit_status == "Skipped":
                # If the sensor has been skipped, plot without any fit results and add a message to the output text
                # self.output_text.setPlainText("Sensor was skipped from previous analysis")
                pass

            # Display the generated plot in the GUI
            self.display_plot()

        else:
            # Plot empty plot
            self.saturation_voltage_fit_status = "All_Sensors_Checked"
            self.fig, self.ax = plt.subplots(dpi=300)
            # set box in the center of the plot
            self.ax.text(0.5, 0.5, "All sensors are checked\n" + "Reseting current index to 0", 
                         horizontalalignment='center', verticalalignment='center',
                         fontsize=18, fontweight='bold', color='black')
            self.current_sensor_index = 0
            self.plot_first_index = True
            if hasattr(self, 'fig'):
                plt.close(self.fig)
            self.display_plot()
            
        # Connect the canvas to the mouse events
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # Connect the canvas to the keyboard events
        self.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.canvas.mpl_connect('key_release_event', self.on_key_release)
        self.canvas.mpl_connect('figure_leave_event', self.release_canvas_focus)
        self.canvas.mpl_connect('figure_enter_event', self.grab_canvas_focus)

        # Set focus to the canvas to be able to use the keyboard
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
    

    def check_sensor_analysis_status(self):
        """ 
        Check if the sensor has already been analysed.
        Returns a string that tells the user the current status of the sensor analysis. 

        5 cases:
        - Auto = sat_V_CV|TCT == np.float64 and low|high_fit_start|stop_CV|TCT == 0 
        - Manual_Analysed = sat_V_CV|TCT == np.float64 and low|high_fit_start|stop_CV|TCT == np.float64, analysed from previous manual fit
        - Manual_Analysed_EndCap = sat_V_CV|TCT == np.float64 and low_fit_start|stop_CV|TCT == np.float64, high_fit_start == high_fit_stop == 0, endcap assumption is used for the fit
        - Manual_Analysed_UpperLine = upper_line_params_CV|TCT == tuple of (x, y, rotation_angle) saved from previous manual upper line fit, otherwise None
        - Skipped = sat_V_CV|TCT == 0 and low|high_fit_start|stop_CV|TCT == 0
        - Not_Analysed = sat_V_CV|TCT == np.nan and low|high_fit_start|stop_CV|TCT == np.nan  --> self.saturation_V = None, low and high are kept to the previous values for faster manual fitting
        """
        if self.fit_from_TCT:
            if not self.database.loc[self.mask_single_sensor, 'sat_V_TCT'].isna().any() and not self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'].isna().any() and not self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'].isna().any() and not self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'].isna().any() and not self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'].isna().any():
                self.low_fit_start_value = self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'].values[0]
                self.low_fit_stop_value = self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'].values[0]
                self.high_fit_start_value = self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'].values[0]
                self.high_fit_stop_value = self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'].values[0]
                self.saturation_V = self.database.loc[self.mask_single_sensor, 'sat_V_TCT'].values[0]
                self.upper_line_fit_params = self.database.loc[self.mask_single_sensor, 'upper_fit_params_TCT'].values[0]
            else:
                self.saturation_V = None
        else:
            if not self.database.loc[self.mask_single_sensor, 'sat_V_CV'].isna().any() and not self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'].isna().any() and not self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'].isna().any() and not self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'].isna().any() and not self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'].isna().any():
                self.low_fit_start_value = self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'].values[0]
                self.low_fit_stop_value = self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'].values[0]
                self.high_fit_start_value = self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'].values[0]
                self.high_fit_stop_value = self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'].values[0]
                self.saturation_V = self.database.loc[self.mask_single_sensor, 'sat_V_CV'].values[0]
                self.upper_line_fit_params = self.database.loc[self.mask_single_sensor, 'upper_fit_params_CV'].values[0]
            else:
                self.saturation_V = None

        if self.upper_line_fit_params is not None:
            self.upper_line_point_x = self.upper_line_fit_params[0]
            self.upper_line_point_y = self.upper_line_fit_params[1]
            self.upper_line_rotation_angle = self.upper_line_fit_params[2]
        else:
            self.upper_line_point_x = None
            self.upper_line_point_y = None
            self.upper_line_rotation_angle = None

        if self.saturation_V is None:
            return "Not_Analysed"
        elif self.saturation_V is not None and self.saturation_V != 0 and (self.low_fit_start_value == 0 and self.low_fit_stop_value == 0 and self.high_fit_start_value == 0 and self.high_fit_stop_value == 0):
            return "Auto"
        elif self.saturation_V is not None and (self.low_fit_start_value != 0 and self.low_fit_stop_value != 0 and self.high_fit_start_value != 0 and self.high_fit_stop_value != 0):
            return "Manual_Analysed"
        elif self.saturation_V is not None and (self.low_fit_start_value != 0 and self.low_fit_stop_value != 0 and self.high_fit_start_value == 0 and self.high_fit_stop_value == 0) and self.upper_line_fit_params is None:
            self.endcap_assumption_activated = True
            return "Manual_Analysed_EndCap"
        elif self.saturation_V == 0 and (self.low_fit_start_value == 0 and self.low_fit_stop_value == 0 and self.high_fit_start_value == 0 and self.high_fit_stop_value == 0):
            return "Skipped"
        elif self.upper_line_fit_params is not None:
            self.manual_upper_fit_activated = True
            return "Manual_Analysed_UpperLine"


    def automatic_fit_saturation_voltage(self):
        """Perform linear fits and plot the fitted lines with intersection point, i.e. the saturation voltage"""
        # Perform automatic fit with curvature 
        first_derivative = np.gradient(self.y_data_norm, self.x_data_norm)
        second_derivative = np.gradient(first_derivative, self.x_data_norm)

        curvature_list = np.abs(((1 + first_derivative**2)**1.5) / second_derivative)

        # Find indices used for low and high fit lines and intersection point, i.e. the saturation voltage
        self.low_fit_indices, self.high_fit_indices, self.low_fit_coeffs, self.high_fit_coeffs, self.saturation_V, self.intersection_y = find_saturation_voltage_from_curvature_fit(x_data=self.x_data, y_data=self.y_data, curvature_list=curvature_list)
        
        if self.low_fit_indices is None and self.high_fit_indices is None and self.low_fit_coeffs is None and self.high_fit_coeffs is None and self.saturation_V is None and self.intersection_y is None:
            self.saturation_voltage_fit_status = "Skipped"
        else:
            if self.high_fit_coeffs[0] == 0:
                plateau_center = self.high_fit_coeffs[1]
                plateau_lower = plateau_center * (1 - PLATEAU_ERROR_DOWN)
                plateau_upper = plateau_center * (1 + PLATEAU_ERROR_UP)
                
                # Get data points used for the low fit
                x_low_fit = self.x_data.iloc[self.low_fit_indices]
                y_low_fit = self.y_data.iloc[self.low_fit_indices]
                
                # Calculate saturation voltage with uncertainty
                sat_V_mean, sat_V_lower, sat_V_upper = calculate_saturation_voltage_with_uncertainty(
                    x_low_fit, y_low_fit, self.high_fit_coeffs, plateau_lower, plateau_upper
                )
                
                if sat_V_mean is not None:
                    self.saturation_V = sat_V_mean
                    self.saturation_V_lower = sat_V_lower
                    self.saturation_V_upper = sat_V_upper
                else:
                    self.saturation_V_lower = None
                    self.saturation_V_upper = None
            else:
                self.saturation_V_lower = None
                self.saturation_V_upper = None
            
            # Display the automatic fit results and ask user for confirmation 
            self.display_fit_results()

        # Ask user for fit response of the automatic fit
        self.ask_user_for_fit_response()
        
    
    def find_saturation_voltage_from_user_defined_intervals(self):
        """Find the saturation voltage from the user defined intervals."""
        # All indices of the data to return highlight points for the plot 
        all_indices = np.arange(len(self.x_data))

        # ---- LOW FIT ----
        mask_low_fit = (self.x_data >= self.low_fit_start_value) & (self.x_data <= self.low_fit_stop_value)
        x_low_fit = self.x_data[mask_low_fit]
        y_low_fit = self.y_data[mask_low_fit]

        if len(x_low_fit) < 2:
            print("Need at least 2 points for low fit.")
            return

        # Fit the low region
        self.low_fit_coeffs = np.polyfit(x_low_fit, y_low_fit, deg=1)
        self.low_fit_indices = all_indices[mask_low_fit]
        
        # print("slope of low fit: ", self.low_fit_coeffs[0])

        # ---- HIGH FIT or END-CAP ASSUMPTION ----
        if not self.endcap_assumption_activated and not self.manual_upper_fit_activated:
            # Normal high fit
            mask_high_fit = (self.x_data >= self.high_fit_start_value) & (self.x_data <= self.high_fit_stop_value)
            x_high_fit = self.x_data[mask_high_fit]
            y_high_fit = self.y_data[mask_high_fit]

            if len(x_high_fit) < 2:
                print("Need at least 2 points for high fit.")
                return

            # If fitting from CV, use mean (plateau); if from TCT, use linear fit
            if not self.fit_from_TCT:
                plateau_y = np.mean(y_high_fit)
                self.high_fit_coeffs = [0, plateau_y]  # slope=0, intercept=mean value
                # print("mean of high fit points (plateau): ", plateau_y)
            else:
                self.high_fit_coeffs = np.polyfit(x_high_fit, y_high_fit, deg=1)
                # print("slope of high fit: ", self.high_fit_coeffs[0])
            
            self.high_fit_indices = all_indices[mask_high_fit]
            
            # print("mean of high fit points: ", np.mean(y_high_fit))

        elif self.endcap_assumption_activated:
            # Convert to string because dictionary keys are strings
            thickness_key = str(int(self.single_sensor_thickness))

            if thickness_key not in END_INV_CAPACITANCE_2_ASSUMPTION:
                print(f"No endcap assumption value found for thickness {self.single_sensor_thickness}.")
                return

            plateau_y = END_INV_CAPACITANCE_2_ASSUMPTION[thickness_key]
            self.high_fit_coeffs = [0, plateau_y]   # slope=0, intercept=plateau value
            self.high_fit_indices = np.array([])    # No actual data points on plateau

        elif self.manual_upper_fit_activated:
            # high fit coeffs are already defined, skip this step
            pass

        # ---- INTERSECTION ----
        try:
            # Calculate center point of the intersection
            self.saturation_V, self.intersection_y = find_intersection_of_two_lines(
                self.low_fit_coeffs, self.high_fit_coeffs
            )
            
            # Calculate saturation voltage from error bounds of plateau or end capacitance assumption
            if self.high_fit_coeffs[0] == 0 and not self.manual_upper_fit_activated: #  high_fit_coeffs[0] == 0  = for the CV case! 
                plateau_center = self.high_fit_coeffs[1]
                
                if self.endcap_assumption_activated:
                    # Use endcap errors
                    plateau_lower = self.end_cap_lower
                    plateau_upper = self.end_cap_upper
                else:
                    # Use plateau errors
                    plateau_lower = plateau_center * (1 - PLATEAU_ERROR_DOWN)
                    plateau_upper = plateau_center * (1 + PLATEAU_ERROR_UP)
                    
                # Calculate uncertainty using all possible combinations
                sat_V_mean, sat_V_lower, sat_V_upper = calculate_saturation_voltage_with_uncertainty(
                    x_low_fit, y_low_fit, self.high_fit_coeffs, plateau_lower, plateau_upper
                )

                if sat_V_mean is not None:
                    # Use the uncertainty-weighted values
                    self.saturation_V = sat_V_mean
                    self.saturation_V_lower = sat_V_lower
                    self.saturation_V_upper = sat_V_upper
                    self.saturation_V_error_down = self.saturation_V - self.saturation_V_lower
                    self.saturation_V_error_up = self.saturation_V_upper - self.saturation_V
                else:
                    # Fallback to no uncertainty
                    self.saturation_V_lower = None
                    self.saturation_V_upper = None
            elif self.manual_upper_fit_activated:
                # Add static 5% error up and down to the saturation voltage
                self.saturation_V_lower = self.saturation_V * (1 - MANUAL_UPPER_LINE_ERROR_DOWN)
                self.saturation_V_upper = self.saturation_V * (1 + MANUAL_UPPER_LINE_ERROR_UP)
                self.saturation_V_error_down = self.saturation_V - self.saturation_V_lower
                self.saturation_V_error_up = self.saturation_V_upper - self.saturation_V
            elif self.fit_from_TCT and not self.manual_upper_fit_activated:
                # Add static 5% error up and down to the saturation voltage
                self.saturation_V_lower = self.saturation_V * (1 - SAT_V_ERROR_DOWN_TCT)
                self.saturation_V_upper = self.saturation_V * (1 + SAT_V_ERROR_UP_TCT)
                self.saturation_V_error_down = self.saturation_V - self.saturation_V_lower
                self.saturation_V_error_up = self.saturation_V_upper - self.saturation_V
            else: 
                self.saturation_V_lower = None
                self.saturation_V_upper = None
                
        except Exception as e:
            print(f"Error finding intersection: {e}")
            return

        # Display the manual fit results
        self.display_fit_results()

        # Ask user for fit response of the manual fit
        self.ask_user_for_fit_response()


    def manual_fit_mode(self):
        # Set the fit status to Manual_Fit
        self.saturation_voltage_fit_status = "Manual_Fit"
        
        # Reset the endcap assumption and upper fit activated flags
        self.endcap_assumption_activated = False
        self.manual_upper_fit_activated = False
        
        # Enable the buttons
        self.fit_ok_button.setEnabled(False)
        self.manual_fit_button.setEnabled(False)
        self.fit_button.setEnabled(True)
        self.skip_button.setEnabled(True)
        self.manual_upper_line_button.setEnabled(True)
        self.rotate_anti_clockwise_button.setEnabled(False)
        self.rotate_clockwise_button.setEnabled(False)
        self.endcap_assumption_button.setEnabled(True)
        self.retry_automatic_fit_button.setEnabled(False)
        self.activate_interactive_lines_for_manual_fit()
        
        
    def endcap_assumption_fit_mode(self):
        """Endcap assumption fit mode."""
        # self.saturation_voltage_fit_status = "Manual_Analysed_EndCap"
        
        self.high_fit_start_value = 0
        self.high_fit_stop_value = 0
        self.endcap_assumption_activated = True
        self.manual_fit_button.setEnabled(True)
        self.activate_interactive_lines_for_manual_fit()

    def manual_upper_fit_mode(self):
        """Manual upper line fit mode."""
        
        self.high_fit_start_value = 0
        self.high_fit_stop_value = 0
        self.manual_upper_fit_activated = True
        self.rotate_anti_clockwise_button.setEnabled(True)
        self.rotate_clockwise_button.setEnabled(True)
        self.activate_interactive_lines_for_manual_fit()
        
        
    def save_and_go_to_next_sensor(self):
        """ 
        Save the fit result based on the user response to the database
        Automatic Fit = If user is satisfied with the automatic fit, save saturation voltage and set low and high values to 0
        Manual Fit = If user is not satisfied with the automatic fit, save saturation voltage and the manually defined low and high values

        Saturation Voltage is rounded to the nearest integer because of resolution of the data
        """
        # Change from Manual_Fit to Manual_Analysed_EndCap if endcap assumption is activated
        if self.endcap_assumption_activated:
            self.saturation_voltage_fit_status = "Manual_Analysed_EndCap"
        elif self.manual_upper_fit_activated:
            self.saturation_voltage_fit_status = "Manual_Analysed_UpperLine"

        # Press fit OK button when sensor is previously skipped will save skip sensor value and go to next sensor
        if self.saturation_voltage_fit_status == "Skipped":
            self.skip_sensor_and_go_to_next()
            return

        # Save the fit results
        if self.saturation_voltage_fit_status in ["Auto", "Not_Analysed"]:
            if self.fit_from_TCT:
                self.database.loc[self.mask_single_sensor, 'sat_V_TCT'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'upper_fit_params_TCT'] = None
            else:
                self.database.loc[self.mask_single_sensor, 'sat_V_CV'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'sat_V_err_down_CV'] = float(round(self.saturation_V_error_down, 0))
                self.database.loc[self.mask_single_sensor, 'sat_V_err_up_CV'] = float(round(self.saturation_V_error_up, 0))
                self.database.loc[self.mask_single_sensor, 'upper_fit_params_CV'] = None
        elif self.saturation_voltage_fit_status in ["Manual_Fit", "Manual_Analysed"]:
            if self.fit_from_TCT:
                self.database.loc[self.mask_single_sensor, 'sat_V_TCT'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'] = float(math.floor(self.low_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'] = float(math.ceil(self.low_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'] = float(math.floor(self.high_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'] = float(math.ceil(self.high_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'sat_V_err_down_TCT'] = float(round(self.saturation_V_error_down, 0))
                self.database.loc[self.mask_single_sensor, 'sat_V_err_up_TCT'] = float(round(self.saturation_V_error_up, 0))
                self.database.loc[self.mask_single_sensor, 'upper_fit_params_TCT'] = None
            else:
                self.database.loc[self.mask_single_sensor, 'sat_V_CV'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'] = float(math.floor(self.low_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'] = float(math.ceil(self.low_fit_stop_value))   
                self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'] = float(math.floor(self.high_fit_start_value))  
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'] = float(math.ceil(self.high_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'sat_V_err_down_CV'] = float(round(self.saturation_V_error_down, 0))
                self.database.loc[self.mask_single_sensor, 'sat_V_err_up_CV'] = float(round(self.saturation_V_error_up, 0))
                self.database.loc[self.mask_single_sensor, 'upper_fit_params_CV'] = None
        elif self.saturation_voltage_fit_status == "Manual_Analysed_EndCap":
            if self.fit_from_TCT:
                self.database.loc[self.mask_single_sensor, 'sat_V_TCT'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'] = float(math.floor(self.low_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'] = float(math.ceil(self.low_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'upper_fit_params_TCT'] = None
            else:
                self.database.loc[self.mask_single_sensor, 'sat_V_CV'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'] = float(math.floor(self.low_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'] = float(math.ceil(self.low_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'sat_V_err_down_CV'] = float(round(self.saturation_V_error_down, 0))
                self.database.loc[self.mask_single_sensor, 'sat_V_err_up_CV'] = float(round(self.saturation_V_error_up, 0))
                self.database.loc[self.mask_single_sensor, 'upper_fit_params_CV'] = None
        elif self.saturation_voltage_fit_status == "Manual_Analysed_UpperLine":
            if self.fit_from_TCT:
                self.database.loc[self.mask_single_sensor, 'sat_V_TCT'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'] = float(math.floor(self.low_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'] = float(math.ceil(self.low_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'] = 0.0
                matching_index = self.database.loc[self.mask_single_sensor].index[0]
                self.database.at[matching_index, 'upper_fit_params_TCT'] = (
                    float(round(self.upper_line_point_x, 3)),
                    float(round(self.upper_line_point_y, 3)),
                    float(self.upper_line_rotation_angle)
                )
            else:
                self.database.loc[self.mask_single_sensor, 'sat_V_CV'] = float(round(self.saturation_V, 0))
                self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'] = float(math.floor(self.low_fit_start_value))
                self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'] = float(math.ceil(self.low_fit_stop_value))
                self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'] = 0.0
                self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'] = 0.0
                # matching_index = self.database.loc[self.mask_single_sensor].index[0]
                matching_index = self.database.loc[self.mask_single_sensor].index[0]
                self.database.at[matching_index, 'upper_fit_params_CV'] = (
                    float(round(self.upper_line_point_x, 3)),
                    float(f"{self.upper_line_point_y:.3e}"),
                    float(self.upper_line_rotation_angle)
                )
        
        # Save database
        self.database.to_pickle(DEFAULT_DATABASE_PATH)

        # Go to next sensor
        self.next_previous_sensor(next_sensor=True)


    def skip_sensor_and_go_to_next(self):
        """Skip the current sensor and go to the next one."""
        if self.fit_from_TCT:
            self.database.loc[self.mask_single_sensor, 'sat_V_TCT'] = 0.0
            self.database.loc[self.mask_single_sensor, 'low_fit_start_TCT'] = 0.0
            self.database.loc[self.mask_single_sensor, 'low_fit_stop_TCT'] = 0.0
            self.database.loc[self.mask_single_sensor, 'high_fit_start_TCT'] = 0.0
            self.database.loc[self.mask_single_sensor, 'high_fit_stop_TCT'] = 0.0
            self.database.loc[self.mask_single_sensor, 'upper_fit_params_TCT'] = None
        else:
            self.database.loc[self.mask_single_sensor, 'sat_V_CV'] = 0.0
            self.database.loc[self.mask_single_sensor, 'low_fit_start_CV'] = 0.0
            self.database.loc[self.mask_single_sensor, 'low_fit_stop_CV'] = 0.0
            self.database.loc[self.mask_single_sensor, 'high_fit_start_CV'] = 0.0
            self.database.loc[self.mask_single_sensor, 'high_fit_stop_CV'] = 0.0
            self.database.loc[self.mask_single_sensor, 'upper_fit_params_CV'] = None

        # Save database
        self.database.to_pickle(DEFAULT_DATABASE_PATH)

        self.next_previous_sensor(next_sensor=True)


    def retry_automatic_fit(self):
        """Retry the automatic fit."""
        self.saturation_voltage_fit_status = "Not_Analysed"
        self.endcap_assumption_activated = False
        self.remove_interactive_lines_for_manual_fit()
        self.automatic_fit_saturation_voltage()
    
    
    # --------------------------------------------------------------------------------------------------------------------------------------------
    #                                                              GUI FUNCTIONS                                                                 #
    # --------------------------------------------------------------------------------------------------------------------------------------------
    
    def plot_saturation_voltage_single_sensor(self, df, fit_from_TCT):
        plt.rcParams.update(RC_PLOT_STYLE) # use RC_PLOT_STYLE by default
        fig, ax = plt.subplots(dpi=300)
        ax.grid()
        
        single_sensor_df = df[(df['sensor_id'] == self.single_sensor_id) & (df['annealing_time'] == self.single_sensor_annealing_time)]
        
        if self.measurement_type == "bare":
            self.single_sensor_voltage = single_sensor_df["v_nom"] 
            single_sensor_cap = single_sensor_df["cs"]
            single_sensor_cap_inv = 1/single_sensor_cap**2
            self.single_sensor_norm_cap_inv = single_sensor_cap_inv/max(single_sensor_cap_inv)
            self.y_data = self.single_sensor_norm_cap_inv
        elif self.measurement_type == "onPCB":
            self.single_sensor_voltage = single_sensor_df["Voltage"]
            if not fit_from_TCT:
                single_sensor_cap = single_sensor_df["ser_cap"]
                single_sensor_cap_inv = 1/single_sensor_cap**2
                self.y_data = single_sensor_cap_inv
            else:
                self.single_sensor_CC = single_sensor_df["CC_corr"]
                self.y_data = self.single_sensor_CC

        self.x_data = self.single_sensor_voltage

        # Normalize y-data to 0-1
        self.y_data_norm = (self.y_data - min(self.y_data)) / (max(self.y_data) - min(self.y_data))
        self.x_data_norm = (self.x_data - min(self.x_data)) / (max(self.x_data) - min(self.x_data))
        
        self.text_content = (
        r"$\bf{Saturation}$" + " " + r"$\bf{Voltage}$" + "\n\n"
        f"{self.campaign}\n"
        f"===========\n"
        f"{self.single_sensor_id}\n"
        r"$\bf{A. Time:}$" + self.single_sensor_annealing_time + "\n"
        r"$\bf{Material:}$" + f"{'EPI' if self.single_sensor_thickness == 120 else 'FZ'}\n"
        r"$\bf{Thickness:}$" + f"{self.single_sensor_thickness}\n"
        r"$\bf{Fluence:}$" +f"{self.single_sensor_fluence:.2e}\n"
        
        f"\n\n\n"
        )
        fluence_label = f"{self.single_sensor_fluence:.1e}".replace("e+", "e")
        if LABEL_MODE == "fluence, thickness, annealing_time":
            label = f"{fluence_label}, {self.single_sensor_thickness}μm ({self.single_sensor_annealing_time})"
        elif LABEL_MODE == "fluence, thickness, sensor_id":
            label = f"{fluence_label}, {self.single_sensor_thickness}μm ({self.single_sensor_id})"
        plt.plot(self.x_data, self.y_data, label=label, marker="o", color="black", fillstyle=FILLSTYLE, markersize=MARKERSIZE)
    
        if fit_from_TCT:
            ax.set_ylabel("Normalized Charge Collection", fontweight="bold")
        else:
            ax.set_ylabel("1/Capacitance² [1/F²]", fontweight="bold")
        ax.set_yscale("linear")
        ax.set_xlabel("Voltage [V]", fontweight="bold")
        self.text_box = plt.text(1.02, 1, self.text_content, transform=ax.transAxes, fontsize=14, verticalalignment='top', horizontalalignment='left')
        plt.legend(bbox_to_anchor=(1.02, 0), fontsize=LEGEND_SIZE, loc="lower left", frameon=True)
        plt.close(fig)

        return fig, ax
    
    
    def display_fit_results(self):
        """Display the automatic fit results. """
        # extend the fitted lines to the whole canvas
        x_extended = np.linspace(self.x_min, self.x_max, 100)  # 100 points between x_min and x_max

        # Color of the lines and points
        if self.saturation_voltage_fit_status in ["Manual_Analysed", "Auto", "Manual_Analysed_EndCap", "Manual_Analysed_UpperLine"]:
            color_low_fit_line = COLOR_SAT_V_FIT_RESULTS_ANALYSED["low_fit_line"]
            color_high_fit_line = COLOR_SAT_V_FIT_RESULTS_ANALYSED["high_fit_line"]
            color_low_fit_points = COLOR_SAT_V_FIT_RESULTS_ANALYSED["low_fit_points"]
            color_high_fit_points = COLOR_SAT_V_FIT_RESULTS_ANALYSED["high_fit_points"]
            color_sat_V = COLOR_SAT_V_FIT_RESULTS_ANALYSED["sat_V"]
        else:
            color_low_fit_line = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["low_fit_line"]
            color_high_fit_line = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_line"]
            color_low_fit_points = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["low_fit_points"]
            color_high_fit_points = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_points"]
            color_sat_V = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["sat_V"]

        
        self.low_fit_line, = self.ax.plot(x_extended, np.poly1d(self.low_fit_coeffs)(x_extended), color=color_low_fit_line, linestyle='--', linewidth=0.8)

        # Remove manual upper fit line and replace with the fitted one
        if hasattr(self, 'high_fit_line') and self.high_fit_line is not None:
            self.high_fit_line.remove()

        self.high_fit_line, = self.ax.plot(x_extended, np.poly1d(self.high_fit_coeffs)(x_extended), color=color_high_fit_line, linestyle='--', linewidth=0.8)
        
        # Add plateau/endcap uncertainty bounds
        if self.high_fit_coeffs[0] == 0 and not self.manual_upper_fit_activated: #  high_fit_coeffs[0] == 0  = for the CV case! 
            plateau_y = self.high_fit_coeffs[1]
            
            if self.endcap_assumption_activated:
                # Use endcap errors
                plateau_lower = self.end_cap_lower
                plateau_upper = self.end_cap_upper
            else:
                # Use plateau errors
                plateau_lower = plateau_y * (1 - PLATEAU_ERROR_DOWN)
                plateau_upper = plateau_y * (1 + PLATEAU_ERROR_UP)
                
            self.plateau_error_bound_fill = self.ax.axhspan(
                plateau_lower, 
                plateau_upper, 
                color="black", 
                alpha=0.2,  # Transparency
                linewidth=0
            )

        # Add highlighting for points used in the fit for both manual and automatic fit
        self.low_fit_points, = self.ax.plot(self.x_data.iloc[self.low_fit_indices], self.y_data.iloc[self.low_fit_indices], color=color_low_fit_points, marker="o", linestyle='none', markersize=3, alpha=1)
        if not self.endcap_assumption_activated and not self.manual_upper_fit_activated: # No points are selected when endcap assumption or manual upper fit is activated
            self.high_fit_points, = self.ax.plot(self.x_data.iloc[self.high_fit_indices], self.y_data.iloc[self.high_fit_indices], color=color_high_fit_points, marker="o", linestyle='none', markersize=3, alpha=1)

        # Plot the intersection point
        self.sat_V_point, = self.ax.plot(self.saturation_V, self.intersection_y, color=color_sat_V, marker="o", markersize=3)

        # Restore the original y-axis and y-axis limits
        if not self.endcap_assumption_activated:
            self.ax.set_ylim(self.y_min, self.y_max)
        else:
            self.ax.set_ylim(self.y_min, self.y_max_endcap_assumption)
        self.ax.set_xlim(self.x_min, self.x_max)
            

        # Add saturation voltage value line to the plot
        self.sat_V_line = self.ax.axvline(x=self.saturation_V, color=color_sat_V, linestyle='--', linewidth=0.8)
        
        # Add saturation voltage uncertainty band if error bounds exist
        if hasattr(self, 'saturation_V_lower') and self.saturation_V_lower is not None:
            self.sat_V_error_bound_fill = self.ax.axvspan(
                self.saturation_V_lower,
                self.saturation_V_upper,
                color=color_sat_V,
                alpha=0.2,
                linewidth=0
            )

        # Add saturation voltage label
        self.sat_V_label = self.ax.text(self.saturation_V, self.line_label_y_pos, f" Sat. Volt. = {self.saturation_V:.0f} V ", 
                                            color='white', fontsize=5, ha='left', va='bottom',
                                            bbox=dict(facecolor=color_sat_V, edgecolor='none', alpha=0.7, pad=0.2))
        # Redraw the canvas
        self.canvas.draw()

    
    def remove_interactive_lines_for_manual_fit(self):
        """Remove interactive lines for manual fit."""
        # Remove existing lines if they exist
        attr_to_remove = [
                    'low_fit_start_line', 'low_fit_stop_line', 'low_fit_start_label', 'low_fit_stop_label',
                    'high_fit_start_line', 'high_fit_stop_line', 'high_fit_start_label', 'high_fit_stop_label',
                    'sat_V_line', 'sat_V_label', 'sat_V_point',
                    'low_fit_line', 'high_fit_line', 
                    'low_fit_points', 'high_fit_points',
                    'end_inv_cap_2_assumption_line', 'end_inv_cap_2_assumption_label',
                    'end_inv_cap_2_assumption_fill', 'plateau_error_bound_fill',
                    'sat_V_error_bound_fill', 'sat_V_error_error_bound_fill',
                ]
        
        for attr in attr_to_remove:
            if hasattr(self, attr):
                getattr(self, attr).remove()
                delattr(self, attr)
    
    
    def activate_interactive_lines_for_manual_fit(self):
        """Activate interactive lines for manual fit."""

        self.remove_interactive_lines_for_manual_fit()
        
        self.end_inv_cap_2_assumption = END_INV_CAPACITANCE_2_ASSUMPTION[str(self.single_sensor_thickness)]

        # Color of the lines 
        if self.saturation_voltage_fit_status in ["Manual_Analysed", "Manual_Analysed_EndCap", "Manual_Analysed_UpperLine"]:
            # Gray colors to display that they are inactive
            color_low_fit_start = COLOR_SAT_V_FIT_RESULTS_ANALYSED["low_fit_start"]
            color_low_fit_stop = COLOR_SAT_V_FIT_RESULTS_ANALYSED["low_fit_stop"]
            color_high_fit_start = COLOR_SAT_V_FIT_RESULTS_ANALYSED["high_fit_start"]
            color_high_fit_stop = COLOR_SAT_V_FIT_RESULTS_ANALYSED["high_fit_stop"]
            color_high_fit_line = COLOR_SAT_V_FIT_RESULTS_ANALYSED["high_fit_line"]
        else:
            # Colorful lines to display that they are active
            color_low_fit_start = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["low_fit_start"]
            color_low_fit_stop = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["low_fit_stop"]
            color_high_fit_start = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_start"]
            color_high_fit_stop = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_stop"]
            color_high_fit_line = COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_line"]

        # Set the default values for the fit start and stop values when there are no previous values
        if self.low_fit_start_value is None or self.low_fit_start_value == 0 or self.low_fit_start_value is np.nan:
            self.low_fit_start_value = 40 if self.previously_clicked_low_fit_start_value is None else self.previously_clicked_low_fit_start_value
        if self.low_fit_stop_value is None or self.low_fit_stop_value == 0 or self.low_fit_stop_value is np.nan:
            self.low_fit_stop_value = 115 if self.previously_clicked_low_fit_stop_value is None else self.previously_clicked_low_fit_stop_value
        if self.high_fit_start_value is None or self.high_fit_start_value == 0 or self.high_fit_start_value is np.nan:
            self.high_fit_start_value = 0 if self.endcap_assumption_activated or self.manual_upper_fit_activated else 490 if self.previously_clicked_high_fit_start_value is None else self.previously_clicked_high_fit_start_value
        if self.high_fit_stop_value is None or self.high_fit_stop_value == 0 or self.high_fit_stop_value is np.nan:
            self.high_fit_stop_value = 0 if self.endcap_assumption_activated or self.manual_upper_fit_activated else 710 if self.previously_clicked_high_fit_stop_value is None else self.previously_clicked_high_fit_stop_value


        if self.manual_upper_fit_activated:
            if self.upper_line_point_x is None:
                self.upper_line_point_x = 500 if self.previously_clicked_manual_upper_line_x_value is None else self.previously_clicked_manual_upper_line_x_value
            if self.upper_line_point_y is None:
                self.upper_line_point_y = max(self.y_data) 
            if self.upper_line_rotation_angle is None:
                self.upper_line_rotation_angle = 0 if self.previously_clicked_manual_upper_line_rotation_angle is None else self.previously_clicked_manual_upper_line_rotation_angle

        # low fit start lines and labels
        self.low_fit_start_line = self.ax.axvline(x=self.low_fit_start_value, 
                                                color=color_low_fit_start, 
                                                linestyle='--', 
                                                linewidth=0.8)
        
        self.low_fit_start_label = self.ax.text(self.low_fit_start_value, self.line_label_y_pos, " Fit Start ", 
                                                color='white', fontsize=5, ha='left', va='bottom',
                                                bbox=dict(facecolor=color_low_fit_start, edgecolor='none', alpha=0.7, pad=0.2))
        
        # low fit stop lines and labels
        self.low_fit_stop_line = self.ax.axvline(x=self.low_fit_stop_value, 
                                                color=color_low_fit_stop,  
                                                linestyle='--', 
                                                linewidth=0.8)
        
        self.low_fit_stop_label = self.ax.text(self.low_fit_stop_value, self.line_label_y_pos, " Fit Stop ", 
                                        color='white', fontsize=5, ha='left', va='bottom',
                                        bbox=dict(facecolor=color_low_fit_stop, edgecolor='none', alpha=0.7, pad=0.2))

        # Reset y-limits to original values without endcap assumption
        self.ax.set_ylim(self.y_min, self.y_max)

        # Only show high fit start and stop lines and labels if not Manual_Analysed_EndCap
        if not self.endcap_assumption_activated and not self.manual_upper_fit_activated:
            # high fit start lines and labels
            self.high_fit_start_line = self.ax.axvline(x=self.high_fit_start_value, 
                                                    color=color_high_fit_start,
                                                    linestyle='--', 
                                                    linewidth=0.8)
            self.high_fit_start_label = self.ax.text(self.high_fit_start_value, self.line_label_y_pos, " Fit Start ", 
                                color='white', fontsize=5, ha='left', va='bottom',
                                bbox=dict(facecolor=color_high_fit_start, edgecolor='none', alpha=0.7, pad=0.2))
            
            # high fit stop lines and labels
            self.high_fit_stop_line = self.ax.axvline(x=self.high_fit_stop_value, 
                                                    color=color_high_fit_stop, 
                                                    linestyle='--', 
                                                    linewidth=0.8)
            self.high_fit_stop_label = self.ax.text(self.high_fit_stop_value, self.line_label_y_pos, " Fit Stop ", 
                                            color='white', fontsize=5, ha='left', va='bottom',
                                            bbox=dict(facecolor=color_high_fit_stop, edgecolor='none', alpha=0.7, pad=0.2))
            
        elif self.endcap_assumption_activated:
            # Calculate error bounds
            self.end_cap_lower = self.end_inv_cap_2_assumption * (1 - END_CAP_ERROR_DOWN)
            self.end_cap_upper = self.end_inv_cap_2_assumption * (1 + END_CAP_ERROR_UP)
            
            # Keep the center line
            self.end_inv_cap_2_assumption_line = self.ax.axhline(
                y=self.end_inv_cap_2_assumption, 
                color="black", 
                linestyle='--', 
                linewidth=0.8
            )
            
            # --- Expand y-limits to include some margin around the upper error bound ---
            y_range = self.end_cap_upper - self.y_min
            margin_factor = 0.03  # 5% padding on both sides

            self.y_max_endcap_assumption = self.end_cap_upper + y_range * margin_factor
            self.ax.set_ylim(self.y_min, self.y_max_endcap_assumption)
            
            # Get axis limits to place text near the left edge
            x_min = self.ax.get_xlim()[0]
            x_max = self.ax.get_xlim()[1]
            x_offset = (x_max - x_min) * 0.02

            # Small vertical offset so the text appears exactly "on" the line visually
            y_offset = (self.ax.get_ylim()[1] - self.ax.get_ylim()[0]) * 0.0025  # ~0.25% offset

            # Place label right on the line at its left end
            self.end_inv_cap_2_assumption_label = self.ax.text(
                x_min + x_offset, self.end_inv_cap_2_assumption + y_offset,
                f" End Cap. = {self.end_inv_cap_2_assumption:.2e}",
                color='white', fontsize=5, ha='left', va='bottom',
                bbox=dict(facecolor="black", edgecolor='none', alpha=0.7, pad=0.2)
            )
        elif self.manual_upper_fit_activated:
            self.high_fit_coeffs = self.activate_manual_upper_fit_line(self.upper_line_point_x, self.upper_line_point_y, self.upper_line_rotation_angle)
            x_extended = np.linspace(self.x_min, self.x_max, 100)
            self.high_fit_line, = self.ax.plot(x_extended, np.poly1d(self.high_fit_coeffs)(x_extended), color=color_high_fit_line, linestyle='--', linewidth=0.8)

        if self.saturation_voltage_fit_status == "Manual_Fit":
            self.canvas.draw()
            self.canvas.flush_events()


    def activate_manual_upper_fit_line(self, x: float, y: float, rotation_angle: float):
        """Create a manual upper line from x, y, and rotation angle.
        Parameters
        ----------
        x : float
            X coordinate of the pivot point
        y : float
            Y coordinate of the pivot point
        rotation_angle : float
            Rotation angle in degrees (0 = horizontal)
        
        Returns
        -------
        list[float, float]
            Coefficients [slope, intercept] compatible with np.poly1d format
        """
        # Convert angle to radians
        angle_rad = np.deg2rad(rotation_angle)
        
        # Calculate aspect ratio to scale slope based on plot dimensions
        x_range = self.x_max - self.x_min
        y_range = self.y_max - self.y_min
        
        # Avoid division by zero
        if x_range == 0:
            aspect_ratio = 1.0
        else:
            aspect_ratio = y_range / x_range
        
        # Calculate slope from angle, scaled by aspect ratio
        slope = np.tan(angle_rad) * aspect_ratio
        
        # Calculate intercept: from point-slope form y = slope * (x_pivot - x) + y_pivot
        # At x=0: intercept = y - slope * x
        intercept = y - slope * x

        # Return coefficients in the same format as [slope, intercept] compatible with np.poly1d format
        return [slope, intercept]


    def rotate_manual_upper_line_button(self, rotation_direction: str):
        """Rotate the manual upper line button."""
        if rotation_direction == "anti_clockwise":
            self.upper_line_rotation_angle += 2
        elif rotation_direction == "clockwise":
            self.upper_line_rotation_angle -= 2

        # Store the new angle
        self.previously_clicked_manual_upper_line_rotation_angle = self.upper_line_rotation_angle

        # Remove high fit line and replace with a new one
        if hasattr(self, 'high_fit_line') and self.high_fit_line is not None:
            self.high_fit_line.remove()
        
        # Plot new manual upper fit line
        self.high_fit_coeffs = self.activate_manual_upper_fit_line(self.upper_line_point_x, self.upper_line_point_y, self.upper_line_rotation_angle)
        x_extended = np.linspace(self.x_min, self.x_max, 100)
        self.high_fit_line, = self.ax.plot(x_extended, np.poly1d(self.high_fit_coeffs)(x_extended), color=COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_line"], linestyle='--', linewidth=0.8)
            
        self.canvas.draw()
        self.canvas.flush_events()


    def ask_user_for_fit_response(self):
        # Activate the user response buttons depending on the sensor analysis status
        if self.saturation_voltage_fit_status in ["Manual_Analysed", "Auto", "Not_Analysed", "Manual_Fit", "Manual_Analysed_EndCap", "Manual_Analysed_UpperLine"]:
            self.fit_ok_button.setEnabled(True)
            self.manual_fit_button.setEnabled(True)
            self.fit_button.setEnabled(False)
            self.skip_button.setEnabled(True)
            self.endcap_assumption_button.setEnabled(False)
            self.manual_upper_line_button.setEnabled(False)
            self.rotate_anti_clockwise_button.setEnabled(False)
            self.rotate_clockwise_button.setEnabled(False)
            self.retry_automatic_fit_button.setEnabled(True)
        elif self.saturation_voltage_fit_status == "Skipped":
            self.fit_ok_button.setEnabled(False)
            self.manual_fit_button.setEnabled(True)
            self.fit_button.setEnabled(False)
            self.skip_button.setEnabled(True)
            self.endcap_assumption_button.setEnabled(False)
            self.manual_upper_line_button.setEnabled(False)
            self.rotate_anti_clockwise_button.setEnabled(False)
            self.rotate_clockwise_button.setEnabled(False)
            self.retry_automatic_fit_button.setEnabled(True)
    
    
    def release_canvas_focus(self, event):
        """Release focus from the canvas when the mouse leaves the figure."""
        self.canvas.setFocusPolicy(Qt.NoFocus)


    def grab_canvas_focus(self, event):
        """Grab focus to the canvas when the mouse enters the figure."""
        self.canvas.setFocusPolicy(Qt.StrongFocus)
        self.canvas.setFocus()
        
        
    def on_key_press(self, event):
        """Handle key presses."""
        if event.key == "shift":
            self.shift_pressed = True
        elif event.key == " " and self.fit_ok_button.isEnabled():
            self.fit_ok_button.click()
        elif event.key == "f" and self.interactive_sat_volt_button.isEnabled():
            self.interactive_sat_volt_button.click()
        elif event.key == "n" and self.next_sensor_button.isEnabled():
            self.next_sensor_button.click()
        elif event.key == "p" and self.previous_sensor_button.isEnabled():
            self.previous_sensor_button.click()
        elif event.key == "1" and self.manual_fit_button.isEnabled():
            self.manual_fit_button.click()
        elif event.key == "2" and self.fit_button.isEnabled():
            self.fit_button.click()
        elif event.key == "3" and self.skip_button.isEnabled():
            self.skip_button.click()
        elif event.key == "r" and self.retry_automatic_fit_button.isEnabled():
            self.retry_automatic_fit_button.click()
        elif event.key == "e" and self.endcap_assumption_button.isEnabled():
            self.endcap_assumption_button.click()
        elif event.key == "s" and self.manual_upper_line_button.isEnabled():
            self.manual_upper_line_button.click()
        elif event.key == "a" and self.rotate_anti_clockwise_button.isEnabled():
            self.rotate_anti_clockwise_button.click()
        elif event.key == "d" and self.rotate_clockwise_button.isEnabled():
            self.rotate_clockwise_button.click()


    def on_key_release(self, event):
        """Handle key releases."""
        if event.key == "shift":
            self.shift_pressed = False


    def on_click(self, event):
        """Move the vertical lines and update labels."""
        # Can't click when automatic fit is active or when previous analysis already has been done without manual fit activation
        if self.saturation_voltage_fit_status in ["Not_Analysed", "Auto", "Manual_Analysed", "Skipped", "Manual_Analysed_EndCap", "Manual_Analysed_UpperLine"]:
            return
        
        if event.inaxes != self.ax:
            return  # Ignore clicks outside the plot

        x_click = event.xdata
        y_click = event.ydata
        if x_click is None or y_click is None:
            return  # Ignore invalid clicks

        # Left-click -> Move Low Fit Start
        # shift + Left-click -> Move High Fit Start
        if event.button == 1:   
            if self.shift_pressed and not self.endcap_assumption_activated and not self.manual_upper_fit_activated: 
                if x_click <= self.low_fit_start_value or x_click <= self.low_fit_stop_value or x_click >= self.high_fit_stop_value:
                    return
                self.high_fit_start_value = x_click
                self.previously_clicked_high_fit_start_value = x_click
                self.high_fit_start_line.set_xdata([x_click, x_click])
                self.high_fit_start_label.set_position((x_click, self.line_label_y_pos))
            elif self.shift_pressed and self.manual_upper_fit_activated:
                self.upper_line_point_x = x_click
                self.upper_line_point_y = y_click
                self.previously_clicked_manual_upper_line_x_value = x_click
                self.previously_clicked_manual_upper_line_y_value = y_click

                # Update the high fit line with new pivot point
                self.high_fit_coeffs = self.activate_manual_upper_fit_line(
                    self.upper_line_point_x,
                    self.upper_line_point_y,
                    self.upper_line_rotation_angle
                )

                # Remove old line and plot new one
                if hasattr(self, 'high_fit_line') and self.high_fit_line is not None:
                    self.high_fit_line.remove()
                
                x_extended = np.linspace(self.x_min, self.x_max, 100)
                self.high_fit_line, = self.ax.plot(x_extended, np.poly1d(self.high_fit_coeffs)(x_extended), color=COLOR_SAT_V_FIT_RESULTS_NOT_ANALYSED["high_fit_line"], linestyle='--', linewidth=0.8)


            else:
                if self.endcap_assumption_activated or self.manual_upper_fit_activated:
                    if x_click >= self.low_fit_stop_value:
                        return
                else:
                    if (x_click >= self.low_fit_stop_value or x_click >= self.high_fit_start_value or x_click >= self.high_fit_stop_value):
                        return
                self.low_fit_start_value = x_click
                self.previously_clicked_low_fit_start_value = x_click
                self.low_fit_start_line.set_xdata([x_click, x_click])
                self.low_fit_start_label.set_position((x_click, self.line_label_y_pos)) 

        # Right-click -> Move Low Fit Stop
        # shift + Right-click -> Move High Fit Stop
        elif event.button == 3:  # Right-click -> Move Fit High (green)
            if self.shift_pressed and not self.endcap_assumption_activated and not self.manual_upper_fit_activated:
                if x_click <= self.low_fit_start_value or x_click <= self.low_fit_stop_value or x_click <= self.high_fit_start_value:
                    return
                self.high_fit_stop_value = x_click
                self.previously_clicked_high_fit_stop_value = x_click
                self.high_fit_stop_line.set_xdata([x_click, x_click])
                self.high_fit_stop_label.set_position((x_click, self.line_label_y_pos))  
            else:
                if self.endcap_assumption_activated or self.manual_upper_fit_activated:
                    if x_click <= self.low_fit_start_value:
                        return
                else:
                    if x_click <= self.low_fit_start_value or x_click >= self.high_fit_start_value or x_click >= self.high_fit_stop_value:
                        return
                self.low_fit_stop_value = x_click
                self.previously_clicked_low_fit_stop_value = x_click
                self.low_fit_stop_line.set_xdata([x_click, x_click])
                self.low_fit_stop_label.set_position((x_click, self.line_label_y_pos))  

        self.canvas.draw()  
        self.canvas.flush_events()
        

    def update_unique_annealing_temp(self):
        previous_annealing_temp = self.annealing_temp_input.get_selected_items()
        campaign = self.campaign_input.currentText()
        measurement_type = self.measurement_type_input.currentText()
        
        if self.database is not None:
            unique_annealing_temps = self.database[(self.database.index.get_level_values("campaign") == campaign) & (self.database["type"] == measurement_type)]["annealing_temp"].unique().tolist()
            if self.annealing_temp_input is not None:
                self.annealing_temp_input.clear()
            unique_annealing_temps = sorted(unique_annealing_temps, key=float)
            self.annealing_temp_input.addItems([str(temp) for temp in unique_annealing_temps])
            self.annealing_temp_input.select_from_list(previous_annealing_temp)
            self.update_unique_sensor_id()
        else:
            self.annealing_temp_input.addItems([])
        
        
    def update_unique_sensor_id(self):
        previous_sensor_id = self.sensor_id_input.get_selected_items()
        campaign = self.campaign_input.currentText()
        measurement_type = self.measurement_type_input.currentText()
        annealing_temp = [float(temp) for temp in self.annealing_temp_input.get_selected_items()]

        if self.database is not None:
            mask = (
                (self.database.index.get_level_values("campaign") == campaign)
                & (self.database["type"] == measurement_type)
                & (self.database["annealing_temp"].isin(annealing_temp))
            )
            df_filtered = self.database[mask]
            unique_sensor_ids = df_filtered.index.get_level_values("sensor_id").unique().tolist()

            if self.sensor_id_input is not None:
                self.sensor_id_input.clear()

            for sid in unique_sensor_ids:
                subdf = df_filtered.xs(sid, level="sensor_id", drop_level=False)

                fluence = subdf.index.get_level_values("fluence").unique().tolist()
                thickness = subdf.index.get_level_values("thickness").unique().tolist()
                ann_temp = subdf["annealing_temp"].unique().tolist()

                info_parts = []
                if fluence:
                    info_parts.append(f"{fluence[0]:.1e}".replace("e+", "e"))
                if thickness:
                    info_parts.append(f"{thickness[0]}µm")
                if ann_temp:
                    info_parts.append(f"{ann_temp[0]}°C")

                self.sensor_id_input.addItem(
                    sid,
                    show_sensor_info_text=True,
                    sensor_info_text=info_parts,
                )

            self.sensor_id_input.select_from_list(previous_sensor_id)
            self.update_unique_annealing_time()
        else:
            self.sensor_id_input.addItems([])


    def update_unique_annealing_time(self):
        previous_annealing_time = self.annealing_time_input.get_selected_items()
        sensor_id = self.sensor_id_input.get_selected_items()
        fit_column = "sat_V_CV" if not self.fit_from_TCT_check.isChecked() else "sat_V_TCT"
        
        if self.database is not None:
            # Get unique annealing times for the given campaign and measurement type
            mask = ((self.database.index.get_level_values("campaign") == self.campaign_input.currentText()) & 
                    (self.database["type"] == self.measurement_type_input.currentText()) &
                    (self.database.index.get_level_values("sensor_id").isin(sensor_id)) &
                    (self.database["Blacklisted"] == False)
                    )
            
            unique_annealing_times = self.database[mask].index.get_level_values("annealing_time").unique().tolist()
            
            if self.annealing_time_input is not None:
                self.annealing_time_input.clear()
                
            # Loop through annealing times
            for atime in sort_annealing_time(unique_annealing_times):
                # Default: no fitted checkbox
                show_fitted_checkbox = False
                fitted = False

                
                # Narrow mask to this annealing time + sensors
                mask_atime = (
                    mask &
                    (self.database.index.get_level_values("annealing_time") == atime)
                )

                # If there is any data for this annealing time
                if not self.database.loc[mask_atime].empty:
                    # Check NaN in 'sat_V_CV'
                    if not self.database.loc[mask_atime, fit_column].isna().any():
                        fitted = True  # means it’s already fitted
                    show_fitted_checkbox = True

                # Add item with optional right checkbox
                self.annealing_time_input.addItem(
                    atime,
                    checked=False,
                    show_fitted_checkbox=show_fitted_checkbox,
                    fitted=fitted
                )

            # Restore previous selection
            self.annealing_time_input.select_from_list(previous_annealing_time)
        else:
            self.annealing_time_input.addItems([])


    def save_plot(self):
        save_path = self.save_path_input.text()
        if save_path != "":
            # Create a new directory if it doesn't exist
            os.makedirs(save_path, exist_ok=True)

            if self.fig_size_save_input.currentText() != "Original":
                original_fig_size = self.fig.get_size_inches()
                base_width = 4.2
                ratio_w = float(self.fig_size_save_input.currentText().split(":")[0])
                ratio_h = float(self.fig_size_save_input.currentText().split(":")[1])
                self.fig.set_size_inches(base_width, base_width * (ratio_h / ratio_w))

            # Save plot as pdf to save path
            self.fig.savefig(
                os.path.join(save_path, "saturation_voltage_fit.pdf"), 
                bbox_inches='tight',
                dpi=600
            )
            
            if self.fig_size_save_input.currentText() != "Original":
                self.fig.set_size_inches(original_fig_size)


    def select_save_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.save_path_input.setText(directory)


    def display_plot(self):
        """Display the generated plot in the canvas while ensuring it fits within the layout."""
        if self.endcap_assumption_activated:
            # --- Expand y-limits to include some margin around the line ---
            self.ax.set_ylim(self.y_min, self.y_max_endcap_assumption)
        
        # --- Title ---
        if self.plot_settings_tab.title_check.isChecked():
            if self.plot_settings_tab.title_input.text() != "":
                self.ax.set_title(self.plot_settings_tab.title_input.text(), fontsize=self.plot_settings_tab.fontsize_slider.value())
            else:
                self.ax.set_title(self.ax.get_title(), fontsize=self.plot_settings_tab.fontsize_slider.value())
        else:
            self.ax.set_title("")
                
        # --- Labels ---
        if self.plot_settings_tab.xlabel_input.text() != "":
            self.ax.set_xlabel(self.plot_settings_tab.xlabel_input.text(),
                        fontsize=self.plot_settings_tab.fontsize_slider.value())
        else:
            self.ax.set_xlabel(self.ax.get_xlabel(),
                        fontsize=self.plot_settings_tab.fontsize_slider.value())

        if self.plot_settings_tab.ylabel_input.text() != "":
            self.ax.set_ylabel(self.plot_settings_tab.ylabel_input.text(),
                        fontsize=self.plot_settings_tab.fontsize_slider.value())
        else:
            self.ax.set_ylabel(self.ax.get_ylabel(),
                        fontsize=self.plot_settings_tab.fontsize_slider.value())
            
        # --- Log scales ---
        self.ax.set_xscale("log" if self.plot_settings_tab.logx_input.isChecked() else "linear")
        self.ax.set_yscale("log" if self.plot_settings_tab.logy_input.isChecked() else "linear")
        
        # --- Tick parameters ---
        self.ax.tick_params(axis='x', which='major',
                        size=self.plot_settings_tab.tick_size_major_slider.value(),
                        width=self.plot_settings_tab.tick_width_major_slider.value())
        self.ax.tick_params(axis='x', which='minor',
                    size=self.plot_settings_tab.tick_size_minor_slider.value(),
                    width=self.plot_settings_tab.tick_width_minor_slider.value())
        self.ax.tick_params(axis='y', which='major',
                    size=self.plot_settings_tab.tick_size_major_slider.value(),
                    width=self.plot_settings_tab.tick_width_major_slider.value())
        self.ax.tick_params(axis='y', which='minor',
                    size=self.plot_settings_tab.tick_size_minor_slider.value(),
                    width=self.plot_settings_tab.tick_width_minor_slider.value())
        
        # Tick label sizes
        self.ax.tick_params(axis='x', which='major',
                    labelsize=self.plot_settings_tab.tick_label_size_slider.value())
        self.ax.tick_params(axis='y', which='major',
                    labelsize=self.plot_settings_tab.tick_label_size_slider.value())
        self.ax.xaxis.get_offset_text().set_fontsize(self.plot_settings_tab.tick_label_size_slider.value())
        self.ax.yaxis.get_offset_text().set_fontsize(self.plot_settings_tab.tick_label_size_slider.value())
        
        # --- Custom text box ---
        if self.plot_settings_tab.custom_text_check.isChecked():
            self.text_box =self.ax.text(
                0.94, 0.1, self.plot_settings_tab.custom_text_input.text(),
                transform=self.ax.transAxes, ha="right", va="bottom",
                fontsize=self.plot_settings_tab.text_box_slider.value(),
                bbox=dict(facecolor="white", alpha=1, edgecolor="none", pad=3)
            )
        else:
            if hasattr(self, "text_box") and self.text_box is not None:
                self.text_box.remove()
                self.text_box = None
        
        self.ax.grid(True, linestyle=":", linewidth=0.3)

        # Adjust line and marker properties
        for line in self.ax.get_lines():
            # Check if this is one of the fit lines that should be preserved
            if hasattr(self, 'low_fit_line') and line == self.low_fit_line:
                continue  # Skip size adjustment for the first fit line
            if hasattr(self, 'high_fit_line') and line == self.high_fit_line:
                continue  # Skip size adjustment for the second fit line
            if hasattr(self, 'low_fit_start_line') and line == self.low_fit_start_line:
                continue  # Skip size adjustment for the low_fit_start_line
            if hasattr(self, 'low_fit_stop_line') and line == self.low_fit_stop_line:
                continue  # Skip size adjustment for the low_fit_stop_line
            if hasattr(self, 'high_fit_start_line') and line == self.high_fit_start_line:
                continue  # Skip size adjustment for the high_fit_start_line
            if hasattr(self, 'high_fit_stop_line') and line == self.high_fit_stop_line:
                continue  # Skip size adjustment for the high_fit_stop_line
            if hasattr(self, 'sat_V_line') and line == self.sat_V_line:
                continue  # Skip size adjustment for the sat_V_line
            if hasattr(self, 'end_inv_cap_2_assumption_line') and line == self.end_inv_cap_2_assumption_line:
                continue  # Skip size adjustment for the end_inv_cap_2_assumption_line

            line.set_markersize(self.plot_settings_tab.marker_size_slider.value())
            line.set_linewidth(self.plot_settings_tab.line_width_slider.value())
                
        # Adjust spine properties
        for spine in self.ax.spines.values():
            spine.set_linewidth(self.plot_settings_tab.border_width_slider.value())

        # Adjust text properties
        for text in self.ax.texts:
            text.set_fontsize(5)
            
        # Fitted line
        for collection in self.ax.collections:
            if isinstance(collection, LineCollection): 
                collection.set_linewidth(self.plot_settings_tab.line_width_slider.value())
            
        # Adjust legend properties
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

            legend = self.ax.legend(
                fontsize=fontsize, markerscale=markerscale, 
                loc=self.plot_settings_tab.legend_placement_input.currentText(), shadow=False,
                frameon=True, borderaxespad=1.2, 
                fancybox=True, framealpha=0.7,
                handlelength=2.4
            )
               
            legend.get_frame().set_linewidth(0.3)
            legend.get_frame().set_edgecolor("black")
        else:
            leg = self.ax.get_legend()
            if leg is not None:
                leg.remove()
        
        self.ax.yaxis.set_minor_formatter(NullFormatter())
        
        # --- Face color ---
        # self.ax.set_facecolor('#FAFAFA')
        # --- Store original limits for zoom reset ---
        self._original_xlim = [self.ax.get_xlim()]
        self._original_ylim = [self.ax.get_ylim()]

        # Remove old canvas and add new one
        self.saturation_voltage_fit_tab_layout.removeWidget(self.canvas)
        self.canvas.deleteLater()

        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.saturation_voltage_fit_tab_layout.insertWidget(0, self.canvas)
        self.saturation_voltage_fit_tab_layout.setStretch(0, 7)
        self.saturation_voltage_fit_tab_layout.setStretch(1, 1)
        
        self.fig.set_constrained_layout(True)

        self.canvas.draw()
        self.canvas.flush_events()

        # Re-attach the rectangle selector to the new canvas
        self._setup_rectangle_selector()

    def refresh_unique_lists_saturation_voltage_fit_tab(self):
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
            # Get unique values from index levels and columns
            self.CAMPAIGNS = sorted(self.database.index.get_level_values('campaign').unique().tolist())
            self.ANNEALING_TEMP = sorted([str(temp) for temp in self.database["annealing_temp"].unique().tolist()])
            self.ANNEALING_TIME = sort_annealing_time(self.database.index.get_level_values('annealing_time').unique().tolist())
            self.MEASUREMENT_TYPE = sorted(self.database['type'].unique().tolist())
        else:
            # Fallback to empty lists if database doesn't exist
            self.database = None
            self.CAMPAIGNS = []
            self.ANNEALING_TEMP = []
            self.ANNEALING_TIME = []
            self.MEASUREMENT_TYPE = []

        self.campaign_input.clear()
        self.campaign_input.addItems(self.CAMPAIGNS)
        self.measurement_type_input.clear()
        self.measurement_type_input.addItems(self.MEASUREMENT_TYPE)
        self.annealing_temp_input.clear()
        self.annealing_temp_input.addItems(self.ANNEALING_TEMP, select_all=True)
        self.annealing_time_input.clear()
        self.annealing_time_input.addItems(self.ANNEALING_TIME)


    def _on_rectangle_select(self, eclick, erelease):
        """Callback fired when the user finishes drawing a zoom rectangle."""
        x1, y1 = eclick.xdata, eclick.ydata
        x2, y2 = erelease.xdata, erelease.ydata

        if x1 is None or x2 is None or y1 is None or y2 is None:
            return

        xmin, xmax = sorted([x1, x2])
        ymin, ymax = sorted([y1, y2])

        self.ax.set_xlim(xmin, xmax)
        self.ax.set_ylim(ymin, ymax)
        self.canvas.draw_idle()

    def _setup_rectangle_selector(self):
        """Create (or recreate) the RectangleSelector on the current axis."""
        self._rect_selector = RectangleSelector(
            self.ax,
            self._on_rectangle_select,
            useblit=True,
            button=[1],
            interactive=False,
            minspanx=5,
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

        self.ax.set_xlim(self._original_xlim[0])
        self.ax.set_ylim(self._original_ylim[0])
        self.canvas.draw_idle()