from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QTabWidget
)
from PySide6.QtCore import Qt
import pandas as pd
import os
import numpy as np

from config import DEFAULT_DATABASE_PATH, DEFAULT_COLUMNS_TO_DISPLAY_DATABASE, DATABASE_INDEX_LEVEL

from Utils.create_database_helper import sort_annealing_time, extract_unique_values_from_database

from GUI.ManageDatabase.DisplayDatabaseTab import DisplayDatabaseTab
from GUI.ManageDatabase.CreateDatabaseTab import CreateDatabaseTab
from GUI.ManageDatabase.ExportImportSaturationVoltageTab import ExportImportSaturationVoltageTab

class DatabaseTab(QWidget):
    def __init__(self, refresh_unique_lists_all_tabs):
        super().__init__()
        # self.columns_to_display_database = DEFAULT_COLUMNS_TO_DISPLAY_DATABASE
        # self.columns_to_overwrite_database = DEFAULT_OVERWRITE_COLUMNS_DATABASE

        # Load database and extract unique values
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
        else:
            # Fallback to empty lists if database doesn't exist
            self.database = None

        # Extract unique values from the database
        self.CAMPAIGNS, self.THICKNESS, self.ANNEALING_TIME, self.ANNEALING_TEMP, self.SENSOR_ID, self.MEASUREMENT_TYPE = extract_unique_values_from_database(self.database)
        
        self.refresh_unique_lists_all_tabs = refresh_unique_lists_all_tabs

        self.initialize_database_main_tab()
        
    
    def initialize_database_main_tab(self):
        # Layout for the database tab
        database_tab_layout = QHBoxLayout(self)

        # Left side: Database display
        self.database_table = QTableWidget()
        self.database_table.setColumnCount(len(DEFAULT_COLUMNS_TO_DISPLAY_DATABASE))
        self.database_table.setHorizontalHeaderLabels([
            "sensor_id", "campaign", "thickness", "fluence", "particle", 
            "halfmoon", "temperature", "CVF", "annealing_time", "annealing_temp", "type",
            "file_IV", "file_CV", "open_corr", "file_TCT", "TCT_corr"
        ])
        self.database_table.setSortingEnabled(True)
        self.database_table.setEditTriggers(QTableWidget.AllEditTriggers)
        self.database_table.cellChanged.connect(self.update_database_value)
        database_tab_layout.addWidget(self.database_table, 80)

        # Right side: Input area for database creation/settings
        input_layout = QVBoxLayout()
        input_layout.setAlignment(Qt.AlignTop)
        input_layout.setSpacing(20)

        # Create a QTabWidget for sub-tabs on the right side
        sub_tab_widget = QTabWidget()
  
        # Add display database tab
        self.display_tab = DisplayDatabaseTab(self.retrieve_database, self.update_database, self.tab_display_database)
        sub_tab_widget.addTab(self.display_tab, "Display Database")
        
        # Add create database tab
        self.create_database_tab = CreateDatabaseTab(self.refresh_unique_lists_all_tabs, self.update_database, self.display_database)
        sub_tab_widget.addTab(self.create_database_tab, "Create Database")

        # Add export/import saturation voltage tab
        self.export_import_saturation_voltage_tab = ExportImportSaturationVoltageTab(self.retrieve_database, self.update_database, self.tab_display_database)
        sub_tab_widget.addTab(self.export_import_saturation_voltage_tab, "Export/Import Saturation Voltage")

        # Add the sub-tab widget to the input layout
        input_layout.addWidget(sub_tab_widget)
        
        # Add input layout to the database tab
        database_tab_layout.addLayout(input_layout, 20)

        if os.path.exists(DEFAULT_DATABASE_PATH):
            database = pd.read_pickle(DEFAULT_DATABASE_PATH)
            self.display_database(database)

    
        
    def retrieve_database(self):
        return self.database
    
    
    def update_database(self, database):
        self.database = database

    
    def tab_display_database(self):
        db_path = self.display_tab.database_path_input.text()
        campaign = self.display_tab.campaigns_database_input.get_selected_items()
        thickness = [float(t) for t in self.display_tab.thickness_input.get_selected_items()]
        annealing_temp = [float(element) if element != "nan" else None for element in  self.display_tab.annealing_temp_input.get_selected_items()]
        filter_none = None in annealing_temp
        annealing_time = self.display_tab.annealing_time_input.get_selected_items()
        measurement_type = self.display_tab.measurement_type_input.get_selected_items()
        
        database = pd.read_pickle(db_path)
        
        database = database[
            (database.index.get_level_values("campaign").isin(campaign)) &
            (database.index.get_level_values("thickness").isin(thickness)) &
            (database.index.get_level_values("annealing_time").isin(annealing_time)) &
            ((database["annealing_temp"].isin(annealing_temp)) | (pd.isna(database["annealing_temp"]) if filter_none else False))  &
            (database["type"].isin(measurement_type))
        ]
        
        self.display_database(database)
        

    def display_database(self, db):
        # Temporarily disconnect the cellChanged signal
        self.database_table.cellChanged.disconnect(self.update_database_value)
    
        # Filter columns based on the self.columns_to_display_database dictionary
        selected_columns = self.display_tab.display_columns_input.get_selected_items()
        
        # Reset the index to convert multi-level index into columns
        db_reset = db.reset_index()
        db_reset = db_reset[selected_columns]

        # Clear the table
        # self.database_table.setRowCount(0)
        self.database_table.clear()
        self.database_table.setSortingEnabled(False)

        # Set the number of rows and columns
        self.database_table.setRowCount(db_reset.shape[0])
        self.database_table.setColumnCount(len(selected_columns))
        # self.database_table.setColumnCount(db_reset.shape[1])

        # Set headers
        # self.database_table.setHorizontalHeaderLabels(db_reset.columns)
        self.database_table.setHorizontalHeaderLabels(selected_columns)

        # Populate the table with data
        for i in range(db_reset.shape[0]):
            for j in range(db_reset.shape[1]):
                if db_reset.columns[j] == 'fluence':
                    # Format the fluence value in scientific notation
                    fluence_value = db_reset.iat[i, j]
                    formatted_value = f"{float(fluence_value):.1e}"  # Format as scientific notation
                    self.database_table.setItem(i, j, QTableWidgetItem(formatted_value))
                else:
                    # For all other columns, display the value as is
                    self.database_table.setItem(i, j, QTableWidgetItem(str(db_reset.iat[i, j])))

        # Resize columns to fit content
        self.database_table.resizeColumnsToContents()
        self.database_table.setSortingEnabled(True)
        
        # Reconnect the cellChanged signal
        self.database_table.cellChanged.connect(self.update_database_value)
        
        
    def update_database_value(self, row, column):
        """
        Update the database when a cell value is changed in the QTableWidget.
        """
        # Get the new value from the cell
        new_value = self.database_table.item(row, column).text()

        # Get the column name of the edited cell
        column_name = self.database_table.horizontalHeaderItem(column).text()

        # Get the values of the index levels 
        index_values = {}
        for col in range(self.database_table.columnCount()):
            header = self.database_table.horizontalHeaderItem(col).text()
            value = self.database_table.item(row, col).text()
            index_values[header] = value

        # Extract the required values for querying
        sensor_id = index_values.get("sensor_id")
        campaign = index_values.get("campaign")
        type_value = index_values.get("type")
        annealing_time = index_values.get("annealing_time")

        print(sensor_id, campaign, type_value, annealing_time)

        # Load the database
        db_path = self.display_tab.database_path_input.text()
        database = pd.read_pickle(db_path)

        # Reset MultiIndex to make it easier to update
        database = database.reset_index()

        # Find the corresponding row
        mask = (
            (database["sensor_id"] == sensor_id) &
            (database["campaign"] == campaign) &
            (database["type"] == type_value) &
            (database["annealing_time"] == annealing_time)
        )
        
        if mask.sum() > 0:
            if column_name == "thickness" and new_value == "0":
                print("Dropping row")
                database = database[~mask]
            else:
                # Update the value
                if column_name == "thickness":
                    new_value = int(new_value) if new_value != "" else 0
                elif column_name == "fluence":
                    new_value = float(new_value) if new_value != "" else 0
                elif column_name == "temperature":
                    new_value = int(new_value) if new_value != "" else 0
                elif column_name == "CVF":
                    new_value = int(new_value) if new_value != "" else 0
                elif column_name in ["annealing_temp"]:
                    new_value = float(new_value) if new_value != "" else None
                elif column_name in ["sat_V_CV", "sat_V_err_down_CV", "sat_V_err_up_CV", "low_fit_start_CV", "low_fit_stop_CV", "high_fit_start_CV", "high_fit_stop_CV"]:
                    new_value = float(new_value) if new_value != "" else np.nan
                elif column_name in ["sat_V_TCT", "sat_V_err_down_TCT", "sat_V_err_up_TCT", "low_fit_start_TCT", "low_fit_stop_TCT", "high_fit_start_TCT", "high_fit_stop_TCT"]:
                    new_value = float(new_value) if new_value != "" else np.nan
                elif column_name == "corrected_annealing_time":
                    new_value = str(new_value)
                elif column_name in ["corr_ann_time_err_up", "corr_ann_time_err_down"]:
                    new_value = str(new_value) if new_value != "" else ""
                elif column_name == "Blacklisted":
                    new_value = True if new_value in ["True", "true"] else False
                elif column_name == "TCT_corr":
                    new_value = float(new_value) if new_value != "" else np.nan
                else:
                    new_value = str(new_value)
                database.loc[mask, column_name] = new_value
            
                print(new_value)

            # Restore MultiIndex
            database = database.set_index(DATABASE_INDEX_LEVEL)
            
            # Save the updated DataFrame back to the database file
            database.to_pickle(db_path)
            
            # pd.set_option('display.max.rows', None)
            # pd.set_option('display.max.columns', None)
            # pd.set_option('display.width', None)
            # pd.set_option('display.max_colwidth', None)
            
            self.tab_display_database()
            self.refresh_unique_lists_all_tabs()
        else:
            print("Error: Could not find the corresponding row in the database.")
        

    def refresh_unique_lists_database_tab(self):
        # Load database and extract unique values
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
            # Get unique values from index levels and columns
            self.CAMPAIGNS = sorted(self.database.index.get_level_values('campaign').unique().tolist())
            self.THICKNESS = sorted([str(thickness) for thickness in self.database.index.get_level_values('thickness').unique().tolist()])
            self.ANNEALING_TEMP = sorted([str(temp) for temp in self.database["annealing_temp"].unique().tolist()])
            self.ANNEALING_TIME = sort_annealing_time(self.database.index.get_level_values('annealing_time').unique().tolist())
            self.MEASUREMENT_TYPE = sorted(self.database['type'].unique().tolist())
        else:
            # Fallback to empty lists if database doesn't exist
            self.database = None
            self.CAMPAIGNS = []
            self.THICKNESS = []
            self.ANNEALING_TEMP = []
            self.ANNEALING_TIME = []
            self.MEASUREMENT_TYPE = []

        self.display_tab.campaigns_database_input.clear()
        self.display_tab.campaigns_database_input.addItems(self.CAMPAIGNS)
        self.display_tab.measurement_type_input.clear()
        self.display_tab.measurement_type_input.addItems(self.MEASUREMENT_TYPE)
        self.display_tab.thickness_input.clear()
        self.display_tab.thickness_input.addItems(self.THICKNESS, select_all=True)
        self.display_tab.annealing_temp_input.clear()
        self.display_tab.annealing_temp_input.addItems(self.ANNEALING_TEMP, select_all=True)
        self.display_tab.annealing_time_input.clear()
        self.display_tab.annealing_time_input.addItems(sort_annealing_time(self.ANNEALING_TIME))
       