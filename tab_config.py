""" 
This file contains the configuration for the tabs.
You need to follow the format below to add a new tab.
Tab specific settings should be added in the tab class. This is just default settings used over multiple tabs.
Example:
[Tab Name] = {
    "title": "Tab Title",
    "save_path": Boolean,
    "campaign": Boolean,
    "measurement": Boolean,
    "measurement_type": Boolean,
    "thickness": Boolean,
    "annealing_temp": Boolean,
    "sensor_id": Boolean,
    "annealing_time": Boolean,
    "fluence": Boolean,
    "voltage": Boolean
}

Possible to leave out False entries.
"""

PLOT_TAB = {
    "title": "Plot IV|CV|TCT vs Voltage",
    "save_path": True,
    "campaign": True,
    "measurement": True,
    "measurement_type": True,
    "annealing_temp": True,
    "sensor_id": True,
    "annealing_time": True,
    "incluce_i_tot": True,
    "include_uncertainty": True,
}

CURRENT_VOLUME_NORM_FLUENCE_TAB = {
    "title": "vs Fluence",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "annealing_time": True,
    "voltage": True,
}

CURRENT_VOLUME_NORM_ANNEALING_TAB = {
    "title": "vs Annealing Time",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "voltage": True,
}

SATURATION_VOLTAGE_FIT_TAB = {
    "title": "Saturation Voltage Fit",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "annealing_temp": True,
    "sensor_id": True,
    "annealing_time": True,
}

SATURATION_VOLTAGE_FLUENCE_TAB = {
    "title": "Saturation Voltage vs Fluence",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "annealing_time": True,
    "plot_saturation_voltage_from_tct": True,
    "plot_saturation_voltage_from_cv_and_tct": True,
}

SATURATION_VOLTAGE_ANNEALING_TAB = {
    "title": "Saturation Voltage vs Annealing Time",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "plot_saturation_voltage_from_tct": True,
    "plot_saturation_voltage_from_cv_and_tct": True,
}

CHARGE_COLLECTION_FLUENCE_TAB = {
    "title": "CC vs Fluence",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "annealing_time": True,
    "voltage": True
}

CHARGE_COLLECTION_ANNEALING_TAB = {
    "title": "CC vs Annealing Time",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "voltage": True,
}

CHARGE_COLLECTION_EFFICIENCY_FLUENCE_TAB = {
    "title": "CCE vs Fluence",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "annealing_time": True,
    "voltage": True
}

CHARGE_COLLECTION_EFFICIENCY_ANNEALING_TAB = {
    "title": "CCE vs Annealing Time",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "sensor_id": True,
    "voltage": True,
}

DI_HF_COMPARISON_TAB = {
    "title": "DI vs HF Comparison",
    "save_path": True,
    "campaign": True,
    "measurement_type": True,
    "thickness": True,
    "annealing_temp": True,
    "plot_only_second_round_of_DI": True,
    "sensor_id_fr": True, # first round of irradiation
    "sensor_id_sr": True, # second round of irradiation
    "sensor_id_hf": True, # high fluence irradiation
    "sensor_id_lf": True, # low fluence irradiation
    "HF_points_after_last_DI_annealing_step": True,
    "type_of_plot": True,
    "voltage": True,
    "add_quarter_ann_time_from_di_first_round": True,
    "split_x_axis": True,
    "plot_saturation_voltage_from_tct": True,
    "plot_saturation_voltage_from_cv_and_tct": True,
    "plot_ratio_DI_vs_HF": True
}