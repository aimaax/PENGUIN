from PySide6.QtWidgets import (
    QWidget, QVBoxLayout
)
from matplotlib.colors import ListedColormap
import pandas as pd

from config import CUSTOM_COLORS, MARKERS, MATPLOTLIB_COLORS
from config import DEFAULT_DATABASE_PATH
from Utils.plot_helper import plot_iv_cv_tct, grade_colors
from Utils.create_database_helper import sort_annealing_time
from GUI.TabTemplate import TabTemplate
from Utils.conversion_helper import convert_annealing_time

from tab_config import PLOT_TAB

class PlotTab(QWidget):
    def __init__(self):
        super().__init__()

        self.tab_template = TabTemplate(parent_tab=self, tab_config=PLOT_TAB, plot_function=self.plot_diodes)
        
        # Create main layout and add TabTemplate
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.tab_template)
        self.setLayout(main_layout)
        

    def plot_diodes(self):
        # Define plotting parameters
        mode = 'fluence, thickness, annealing_time'
        CV_mode = '1/Cs2'

        # Get input values
        chosen_campaign = self.tab_template.campaign_input.get_selected_items()
        chosen_measurement = self.tab_template.measurement_input.currentText()
        chosen_measurement_type = self.tab_template.measurement_type_input.currentText()
        chosen_annealing_temp = [float(temp) for temp in self.tab_template.annealing_temp_input.get_selected_items()]
        chosen_annealing_time = self.tab_template.annealing_time_input.get_selected_items()
        chosen_sensor_id = self.tab_template.sensor_id_input.get_selected_items()
        i_tot = self.tab_template.i_tot_check.isChecked()
        include_uncertainty = self.tab_template.include_uncertainty_check.isChecked()

        # Load the DataFrame from the pickle file
        db_path = DEFAULT_DATABASE_PATH
        database = pd.read_pickle(db_path).reset_index()

        database = database[
            (database["campaign"].isin(chosen_campaign)) &
            (database["annealing_time"].isin(chosen_annealing_time)) &
            (database["sensor_id"].isin(chosen_sensor_id)) &
            (database["type"].isin([chosen_measurement_type])) &
            (database['annealing_temp'].isin(chosen_annealing_temp)) &
            (database['Blacklisted']==False)
        ].copy()

        database["corrected_annealing_time"] = database["corrected_annealing_time"].apply(convert_annealing_time)
        database = database.sort_values(by=["fluence", "thickness", "corrected_annealing_time"], ascending=[True, False, True])
        
        # Group diodes by thickness and fluence
        if self.tab_template.plot_settings_tab.color_input.currentText() == "Custom Colors (one per sensor)":
            # Group by sensor_id only for one color per sensor
            grouped = database.groupby('sensor_id')
        elif chosen_sensor_id != [''] and len(chosen_sensor_id) <= 1:
            grouped = database.groupby(['sensor_id', 'thickness', 'fluence'])
        else:
            grouped = database.groupby(['thickness', 'fluence'])

        # Create a ListedColormap using custom colors from CMS_Style file
        if self.tab_template.plot_settings_tab.color_input.currentText() == "Custom Colors (config.py)":
            colors = ListedColormap(CUSTOM_COLORS)
            # Create a dictionary to map each group to a color and marker
            group_style = {}
            for i, (name, group) in enumerate(grouped):
                group_style[name] = {'color': colors(i), 'marker': MARKERS[i % len(MARKERS)]}
        elif self.tab_template.plot_settings_tab.color_input.currentText() == "Custom Colors (one per sensor)":
            mode = 'fluence, thickness, name'
            # Assign one color per sensor from CUSTOM_COLORS list
            group_style = {}
            for i, (name, group) in enumerate(grouped):
                # name is just sensor_id in this case since we grouped by sensor_id only
                group_style[name] = {'color': CUSTOM_COLORS[i % len(CUSTOM_COLORS)], 'marker': MARKERS[0]}
        else:
            colors = MATPLOTLIB_COLORS[self.tab_template.plot_settings_tab.color_input.currentText()].reversed()
            group_style = {}
            num_groups = len(grouped)
            for i, (name, group) in enumerate(grouped):
                # Normalize the index to [0, 1] range to use full colormap spectrum
                min_val, max_val = 0.4, 1.0
                normalized_index = min_val + (max_val - min_val) * i / max(1, num_groups - 1)
                group_style[name] = {'color': colors(normalized_index), 'marker': MARKERS[i % len(MARKERS)]}

        
        # Sort annealing time
        sorted_anntime = sort_annealing_time(chosen_annealing_time)
        
        # Dictionary: group -> {anntime: graded_color}
        group_color_by_anntime = {}

        if self.tab_template.plot_settings_tab.enable_different_color_check.isChecked() and len(grouped) == 1 and self.tab_template.plot_settings_tab.color_input.currentText() != "Custom Colors (config.py)":
            # Custom color palette case for one sensor only, assign distinct colors from chosen palette
            n = len(sorted_anntime)

            cmap = MATPLOTLIB_COLORS[self.tab_template.plot_settings_tab.color_input.currentText()].reversed()

            group_name = list(group_style.keys())[0]
            group_color_by_anntime[group_name] = {
                at: cmap(i / max(1, n-1)) for i, at in enumerate(sorted_anntime)
            }
        else:
            # One color with different grading depending on annealing time
            for group_name, style in group_style.items():
                base_color = style["color"]
                n = len(sorted_anntime)
                graded = grade_colors(base_color, n)  # list of light→dark shades
                group_color_by_anntime[group_name] = {
                    at: graded[i] for i, at in enumerate(sorted_anntime)
                }

        # Prepare data for plotting
        list_sensor_id = database["sensor_id"].tolist()
        list_thickness = database["thickness"].tolist()
        list_fluence = database["fluence"].tolist()
        list_annealing_time = database["annealing_time"].tolist()
        
        if self.tab_template.plot_settings_tab.color_input.currentText() == "Custom Colors (one per sensor)":
            # For one color per sensor mode, use sensor_id only for color/style lookup
            list_color = [group_color_by_anntime[sensor_id][anntime]
                        for sensor_id, anntime 
                        in zip(list_sensor_id, list_annealing_time)]
            list_style = [group_style[sensor_id]['marker']
                        for sensor_id in list_sensor_id]
        elif chosen_sensor_id != [''] and len(chosen_sensor_id) <= 1:
            list_color = [group_color_by_anntime[(sensor_id, thickness, fluence)][anntime]
                        for sensor_id, thickness, fluence, anntime 
                        in zip(list_sensor_id, list_thickness, list_fluence, list_annealing_time)]
            list_style = [group_style[(sensor_id, thickness, fluence)]['marker']
                        for sensor_id, thickness, fluence 
                        in zip(list_sensor_id, list_thickness, list_fluence)]
        else:
            list_color = [group_color_by_anntime[(thickness, fluence)][anntime]
                        for thickness, fluence, anntime
                        in zip(list_thickness, list_fluence, list_annealing_time)]
            list_style = [group_style[(thickness, fluence)]['marker']
                        for thickness, fluence
                        in zip(list_thickness, list_fluence)]
            

        self.tab_template.fig, self.tab_template.ax = plot_iv_cv_tct(
            df = database, 
            measurement_type = chosen_measurement_type, 
            measurement = chosen_measurement, 
            mode = mode, 
            color = list_color, 
            list_style = list_style, 
            CV_mode = CV_mode,
            i_tot = i_tot, 
            include_uncertainty = include_uncertainty
        )
    

        # Display the generated plot in the GUI
        self.tab_template.display_plot()


        