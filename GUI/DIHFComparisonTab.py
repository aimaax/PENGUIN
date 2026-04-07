from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
import pandas as pd
import matplotlib.pyplot as plt
from GUI.TabTemplate import TabTemplate
from config import DEFAULT_DATABASE_PATH
from tab_config import DI_HF_COMPARISON_TAB
from Utils.di_comparison_plot import get_di_comparison_plot

class DIHFComparisonTab(QWidget):
    def __init__(self):
        super().__init__()
            
        self.tab_template = TabTemplate(
            parent_tab=self, 
            tab_config=DI_HF_COMPARISON_TAB, 
            plot_function=self.plot_di_hf_comparison)
        
        # Create main layout and add TabTemplate
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_template)
        self.setLayout(main_layout)

                
    def plot_di_hf_comparison(self):
        # Load the DataFrame from the pickle file
        db_path = DEFAULT_DATABASE_PATH
        database = pd.read_pickle(db_path)
        
        campaigns = self.tab_template.campaign_input.get_selected_items()
        measurement_type = self.tab_template.measurement_type_input.get_selected_items()
        thickness = [int(t) for t in self.tab_template.thickness_input.get_selected_items()]
        annealing_temp = [float(temp) for temp in self.tab_template.annealing_temp_input.get_selected_items()]
        sensor_id_fr = self.tab_template.sensor_id_fr_input.get_selected_items()
        sensor_id_sr = self.tab_template.sensor_id_sr_input.get_selected_items()
        sensor_id_hf = self.tab_template.sensor_id_hf_input.get_selected_items()
        sensor_id_lf = self.tab_template.sensor_id_lf_input.get_selected_items()
        type_of_plot = self.tab_template.type_of_plot_input.currentText() # alpha, saturation voltage, CC, CCE
        voltage = float(self.tab_template.voltage_input.currentText()) if self.tab_template.voltage_input.currentText() != "Saturation Voltage" else "Saturation Voltage"
        sat_volt_cv_tct = self.tab_template.sat_volt_cv_tct.currentText()
        logx = self.tab_template.plot_settings_tab.logx_input.isChecked()
        add_quarter_ann_time_from_di_first_round = self.tab_template.add_quarter_ann_time_from_di_first_round_input.isChecked()
        split_x_axis = self.tab_template.split_x_axis_input.isChecked()
        plot_ratio_DI_vs_HF = self.tab_template.plot_ratio_DI_vs_HF_input.isChecked()
        plot_average_ratio_DI_vs_HF = self.tab_template.plot_average_ratio_DI_vs_HF_input.isChecked()
        points_after_last_annealing_time = self.tab_template.points_after_last_annealing_step_input.value()
        plot_saturation_voltage_from_tct = self.tab_template.plot_saturation_voltage_from_tct_input.isChecked()
        skip_x_colors_markers = int(self.tab_template.plot_settings_tab.skip_x_colors_markers_input.currentText())
        # Close the old figure to free memory before creating a new one
        if hasattr(self.tab_template, "fig") and self.tab_template.fig is not None:
            plt.close(self.tab_template.fig)
        
        self.tab_template.fig, self.tab_template.ax = get_di_comparison_plot(
            database=database, 
            campaigns=campaigns, 
            measurement_type=measurement_type, 
            thickness=thickness, 
            annealing_temp=annealing_temp, 
            sensor_id_fr=sensor_id_fr, 
            sensor_id_sr=sensor_id_sr, 
            sensor_id_hf=sensor_id_hf, 
            sensor_id_lf=sensor_id_lf, 
            type_of_plot=type_of_plot, 
            voltage=voltage, 
            logx=logx, 
            add_quarter_ann_time_from_di_first_round=add_quarter_ann_time_from_di_first_round,
            split_x_axis=split_x_axis,
            points_after_last_annealing_time=points_after_last_annealing_time,
            plot_saturation_voltage_from_tct=plot_saturation_voltage_from_tct,
            plot_ratio_DI_vs_HF=plot_ratio_DI_vs_HF,
            plot_average_ratio_DI_vs_HF=plot_average_ratio_DI_vs_HF,
            skip_x_colors_markers=skip_x_colors_markers,
            sat_volt_cv_tct=sat_volt_cv_tct)
        
        self.tab_template.display_plot()
        