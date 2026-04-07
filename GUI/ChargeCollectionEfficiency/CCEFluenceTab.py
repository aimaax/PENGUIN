from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
import pandas as pd
from config import DEFAULT_DATABASE_PATH
from Utils.plot_electrical_characteristic_vs_fluence import get_measurement_vs_fluence_plot

from GUI.TabTemplate import TabTemplate
from tab_config import CHARGE_COLLECTION_EFFICIENCY_FLUENCE_TAB

class CCEFluenceTab(QWidget):
    def __init__(self):
        super().__init__()
        
     # Create widget with TabTemplate
        self.tab_template = TabTemplate(
            parent_tab=self, tab_config=CHARGE_COLLECTION_EFFICIENCY_FLUENCE_TAB, 
            plot_function=self.plot_CCE_fluence
            )
        
        # Create main layout and add TabTemplate
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_template)
        self.setLayout(main_layout)
                
    def plot_CCE_fluence(self):
        # Load the DataFrame from the pickle file
        db_path = DEFAULT_DATABASE_PATH
        database = pd.read_pickle(db_path)
        
        campaigns = self.tab_template.campaign_input.get_selected_items()
        measurement_type = self.tab_template.measurement_type_input.get_selected_items()
        thickness = self.tab_template.thickness_input.get_selected_items()
        logx = self.tab_template.plot_settings_tab.logx_input.isChecked()
        voltage = float(self.tab_template.voltage_input.currentText()) if self.tab_template.voltage_input.currentText() != "Saturation Voltage" else "Saturation Voltage"
        sat_volt_cv_tct = self.tab_template.sat_volt_cv_tct.currentText()
        annealing_temp = [float(temp) for temp in self.tab_template.annealing_temp_input.get_selected_items()]
        sensor_id = self.tab_template.sensor_id_input.get_selected_items()
        annealing_time = self.tab_template.annealing_time_input.get_selected_items()
        
        self.tab_template.fig, self.tab_template.ax = get_measurement_vs_fluence_plot(
            database=database, 
            campaigns=campaigns, 
            measurement_type=measurement_type, 
            thickness=thickness, 
            voltage=voltage, 
            annealing_time=annealing_time, 
            annealing_temp=annealing_temp, 
            sensor_id=sensor_id, 
            plot_type="CCE", 
            logx=logx,
            sat_volt_cv_tct=sat_volt_cv_tct
        )

        self.tab_template.display_plot()

        