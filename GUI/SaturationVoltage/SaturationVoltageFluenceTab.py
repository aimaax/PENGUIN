from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
import pandas as pd
from config import DEFAULT_DATABASE_PATH
from Utils.plot_electrical_characteristic_vs_fluence import get_measurement_vs_fluence_plot
from GUI.TabTemplate import TabTemplate
from tab_config import SATURATION_VOLTAGE_FLUENCE_TAB


class SaturationVoltageFluenceTab(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create widget with TabTemplate
        self.tab_template = TabTemplate(
            parent_tab=self, tab_config=SATURATION_VOLTAGE_FLUENCE_TAB, 
            plot_function=self.plot_saturation_voltage_fluence
            )
        
        # Create main layout and add TabTemplate
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_template)
        self.setLayout(main_layout)

                
    def plot_saturation_voltage_fluence(self):
        # Load the DataFrame from the pickle file
        db_path = DEFAULT_DATABASE_PATH
        database = pd.read_pickle(db_path)
        
        campaigns = self.tab_template.campaign_input.get_selected_items()
        plot_from_TCT = self.tab_template.plot_saturation_voltage_from_tct_input.isChecked()
        measurement_type = self.tab_template.measurement_type_input.get_selected_items()
        thickness = self.tab_template.thickness_input.get_selected_items()
        annealing_temp = [float(temp) for temp in self.tab_template.annealing_temp_input.get_selected_items()]
        sensor_id = self.tab_template.sensor_id_input.get_selected_items()
        annealing_time = self.tab_template.annealing_time_input.get_selected_items()

        self.tab_template.fig, self.tab_template.ax = get_measurement_vs_fluence_plot(
            database=database, 
            campaigns=campaigns, 
            measurement_type=measurement_type, 
            thickness=thickness, 
            annealing_time=annealing_time, 
            annealing_temp=annealing_temp, 
            sensor_id=sensor_id, 
            plot_type="saturation_voltage", 
            plot_from_TCT=plot_from_TCT
        )

        self.tab_template.display_plot()
        