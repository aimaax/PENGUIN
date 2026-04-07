from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QFileDialog, QDialog, QMessageBox
)
from PySide6.QtCore import Qt

from Utils.CheckableComboBox import CheckableComboBox

from config import (
    DEFAULT_DIR_SATURATION_VOLTAGE_DATA, DEFAULT_DATABASE_PATH
)

import os
import pandas as pd
from datetime import datetime
from Utils.create_database_helper import sort_annealing_time, extract_unique_values_from_database

class ExportImportSaturationVoltageTab(QWidget):
    def __init__(self, retrieve_database, update_database, tab_display_database):
        super().__init__()
        
        self.retrieve_database = retrieve_database
        self.update_database = update_database
        self.tab_display_database = tab_display_database
        
        # Load database and extract unique values
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
        
            campaigns, _, _, _, _, _ = extract_unique_values_from_database(self.database)
        else:
            self.database = None
            campaigns = []
            
        
        export_import_saturation_voltage_layout = QVBoxLayout(self)
        export_import_saturation_voltage_layout.setAlignment(Qt.AlignTop)
        export_import_saturation_voltage_layout.addSpacing(20)

        # Save directory
        save_dir_layout = QVBoxLayout()
        save_dir_layout.setSpacing(5)
        self.save_dir_input = QLineEdit()
        self.save_dir_input.setText(DEFAULT_DIR_SATURATION_VOLTAGE_DATA)
        self.save_dir_button = QPushButton("Browse")
        self.save_dir_button.clicked.connect(self.select_save_dir)
        save_dir_layout.addWidget(QLabel("Path to export Saturation Voltage:"))
        save_dir_layout.addWidget(self.save_dir_input)
        save_dir_layout.addWidget(self.save_dir_button)
        export_import_saturation_voltage_layout.addLayout(save_dir_layout)
        export_import_saturation_voltage_layout.addSpacing(20)
        
        # CheckableComboBox for DATABASE_CAMPAIGNS
        campaigns_database_layout = QVBoxLayout()
        campaigns_database_layout.setSpacing(5)
        self.campaigns_database_input = CheckableComboBox()
        self.campaigns_database_input.addItems(campaigns)
        self.campaigns_database_input.select_first_index()
        self.campaigns_database_input.add_external_callback(self.update_unique_sensor_id)
        campaigns_database_layout.addWidget(QLabel("Database Campaign:"))
        campaigns_database_layout.addWidget(self.campaigns_database_input)
        export_import_saturation_voltage_layout.addLayout(campaigns_database_layout)
        export_import_saturation_voltage_layout.addSpacing(20)

        # CheckableComboBox for SENSOR_ID
        sensor_id_layout = QHBoxLayout()
        sensor_id_layout.addWidget(QLabel("Sensor ID:"))
        self.sensor_id_input = CheckableComboBox()
        self.sensor_id_input.add_external_callback(self.update_unique_annealing_time)
        sensor_id_layout.addWidget(QPushButton("Select All", clicked=self.sensor_id_input.select_all))
        sensor_id_layout.addWidget(QPushButton("Deselect All", clicked=self.sensor_id_input.deselect_all))
        export_import_saturation_voltage_layout.addLayout(sensor_id_layout)
        export_import_saturation_voltage_layout.addWidget(self.sensor_id_input)
        export_import_saturation_voltage_layout.addSpacing(20)
        
        # CheckableComboBox for ANNEALING_TIME
        annealing_time_layout = QHBoxLayout()
        annealing_time_layout.addWidget(QLabel("Annealing time:"))
        self.annealing_time_input = CheckableComboBox()
        annealing_time_layout.addWidget(QPushButton("Select All", clicked=self.annealing_time_input.select_all))
        annealing_time_layout.addWidget(QPushButton("Deselect All", clicked=self.annealing_time_input.deselect_all))
        annealing_time_layout.addWidget(self.annealing_time_input)
        
        export_import_saturation_voltage_layout.addLayout(annealing_time_layout)
        export_import_saturation_voltage_layout.addWidget(self.annealing_time_input)
        export_import_saturation_voltage_layout.addSpacing(20)
        
        # Checkbox to export CV or TCT values only in horizontal layout
        export_cv_tct_layout = QHBoxLayout()
        export_cv_tct_layout.setSpacing(5)
        self.export_cv_input = QCheckBox("Export CV values only")
        self.export_tct_input = QCheckBox("Export TCT values only")
        self.export_cv_input.stateChanged.connect(lambda: self.export_cv_tct_input_changed(cv_only=self.export_cv_input.isChecked()))
        self.export_tct_input.stateChanged.connect(lambda: self.export_cv_tct_input_changed(tct_only=self.export_tct_input.isChecked()))
        export_cv_tct_layout.addStretch()
        export_cv_tct_layout.addWidget(self.export_cv_input)
        export_cv_tct_layout.addStretch()
        export_cv_tct_layout.addWidget(self.export_tct_input)
        export_cv_tct_layout.addStretch()
        export_import_saturation_voltage_layout.addLayout(export_cv_tct_layout)
        export_import_saturation_voltage_layout.addSpacing(20)

        # Export/Import Saturation Voltage Button
        self.export_saturation_voltage_button = QPushButton("Export Saturation Voltage")
        self.export_saturation_voltage_button.clicked.connect(self.export_saturation_voltage)
        self.export_saturation_voltage_button.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border: 1px solid #999999; 
                border-radius: 4px; 
                height: 30px;
            }
            QPushButton:hover {
                background-color: #999999;  /* Slightly lighter grey on hover */
            }
            QPushButton:pressed {
                background-color: #666666;  /* Slightly darker grey when pressed */
            }
        """)
        export_import_saturation_voltage_layout.addWidget(self.export_saturation_voltage_button)
        export_import_saturation_voltage_layout.addWidget(QLabel("================================================="))
        export_import_saturation_voltage_layout.addSpacing(20)
        
        # Checkbox to import CV or TCT values only in horizontal layout
        import_cv_tct_layout = QHBoxLayout()
        import_cv_tct_layout.setSpacing(5)
        self.import_cv_input = QCheckBox("Import CV values only")
        self.import_tct_input = QCheckBox("Import TCT values only")
        self.import_cv_input.stateChanged.connect(lambda: self.import_cv_tct_input_changed(cv_only=self.import_cv_input.isChecked()))
        self.import_tct_input.stateChanged.connect(lambda: self.import_cv_tct_input_changed(tct_only=self.import_tct_input.isChecked()))
        import_cv_tct_layout.addStretch()
        import_cv_tct_layout.addWidget(self.import_cv_input)
        import_cv_tct_layout.addStretch()
        import_cv_tct_layout.addWidget(self.import_tct_input)
        import_cv_tct_layout.addStretch()
        export_import_saturation_voltage_layout.addLayout(import_cv_tct_layout)
        export_import_saturation_voltage_layout.addSpacing(20)
        
        # Import Saturation Voltage Button
        self.import_saturation_voltage_button = QPushButton("Import Saturation Voltage")
        self.import_saturation_voltage_button.clicked.connect(self.import_saturation_voltage)
        self.import_saturation_voltage_button.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border: 1px solid #999999; 
                border-radius: 4px; 
                height: 30px;
            }
            QPushButton:hover {
                background-color: #999999;  /* Slightly lighter grey on hover */
            }
            QPushButton:pressed {
                background-color: #666666;  /* Slightly darker grey when pressed */
            }
        """)
        export_import_saturation_voltage_layout.addWidget(self.import_saturation_voltage_button)
        
        self.update_unique_sensor_id(select_all=True)
        self.update_unique_annealing_time(select_all=True)
        
        
    def select_save_dir(self):
        save_dir = QFileDialog.getExistingDirectory(self, "Select Save Directory", DEFAULT_DIR_SATURATION_VOLTAGE_DATA)
        if save_dir:
            self.save_dir_input.setText(save_dir)
            
            
    def export_cv_tct_input_changed(self, cv_only=False, tct_only=False):
        if cv_only:
            self.export_tct_input.setChecked(False)
        elif tct_only:
            self.export_cv_input.setChecked(False)
            
            
    def import_cv_tct_input_changed(self, cv_only=False, tct_only=False):
        if cv_only:
            self.import_tct_input.setChecked(False)
        elif tct_only:
            self.import_cv_input.setChecked(False)
            
            
    def export_saturation_voltage(self):
        # Load database 
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
        
        save_dir = self.save_dir_input.text() 
        if not os.path.exists(save_dir):
            os.makedirs(save_dir, exist_ok=True)
        
        # Generate filename
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"saturation_voltage_data_{date_str}.csv"
        save_path = os.path.join(save_dir, filename)
        
        # If file exists, append _2, _3, ...
        counter = 2
        while os.path.exists(save_path):
            filename = f"saturation_voltage_data_{date_str}_{counter}.csv"
            save_path = os.path.join(save_dir, filename)
            counter += 1
        
        # Get selected items
        chosen_campaigns = self.campaigns_database_input.get_selected_items()
        chosen_sensor_id = self.sensor_id_input.get_selected_items()
        chosen_annealing_time = self.annealing_time_input.get_selected_items()
        
        # Filter database
        mask = (
            self.database.index.get_level_values("campaign").isin(chosen_campaigns) &
            self.database.index.get_level_values("sensor_id").isin(chosen_sensor_id) &
            self.database.index.get_level_values("annealing_time").isin(chosen_annealing_time)
        )
        
        filtered_database = self.database[mask]
        
        # Reset index
        df = filtered_database.reset_index()
        
        # Ensure all columns exist
        index_cols = [
            "campaign", "sensor_id", "annealing_time",
            "sat_V_CV", "sat_V_err_down_CV", "sat_V_err_up_CV",
            "low_fit_start_CV", "low_fit_stop_CV", "high_fit_start_CV", "high_fit_stop_CV",
            "sat_V_TCT", "sat_V_err_down_TCT", "sat_V_err_up_TCT",
            "low_fit_start_TCT", "low_fit_stop_TCT", "high_fit_start_TCT", "high_fit_stop_TCT"
        ]
        for col in index_cols:
            if col not in df.columns:
                df[col] = float('nan')
        
        # Replace missing values (NaN) with string 'nan'
        df = df[index_cols].fillna("nan")
        
        # Sort campaigns and sensor_ids normally, annealing_time using your custom function
        df["annealing_time"] = pd.Categorical(df["annealing_time"], categories=sort_annealing_time(df["annealing_time"].unique()), ordered=True)
        
        df = df.sort_values(by=["campaign", "sensor_id", "annealing_time"])
        
        # Able to only export CV or TCT values
        export_cv = self.export_cv_input.isChecked()
        export_tct = self.export_tct_input.isChecked()
        
        cv_cols = [col for col in df.columns if col.endswith("_CV")]
        tct_cols = [col for col in df.columns if col.endswith("_TCT")]
        
        if export_cv and not export_tct:
            df[tct_cols] = "nan"   # wipe out TCT columns
        elif export_tct and not export_cv:
            df[cv_cols] = "nan"    # wipe out CV columns
        
        # Export to CSV
        df.to_csv(save_path, index=False)
        
        
    def import_saturation_voltage(self):
        # Load database 
        if os.path.exists(DEFAULT_DATABASE_PATH):
            self.database = pd.read_pickle(DEFAULT_DATABASE_PATH)
        
        # Step 1: Ask user to select a CSV file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV file to import",
            "",
            "CSV Files (*.csv)"
        )
        if not file_path:
            return  # User cancelled
        
        # Step 2: Create dialog with overwrite checkbox
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Options")
        
        layout = QVBoxLayout(dialog)
        overwrite_checkbox = QCheckBox("Overwrite existing values in database", dialog)
        layout.addWidget(overwrite_checkbox)
        
        import_button = QPushButton("Import", dialog)
        cancel_button = QPushButton("Cancel", dialog)
        layout.addWidget(import_button)
        layout.addWidget(cancel_button)
        
        import_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        if dialog.exec_() != QDialog.Accepted:
            return  # Cancelled
        
        overwrite = overwrite_checkbox.isChecked()
        
        # Step 3: Read CSV
        try:
            df_import = pd.read_csv(file_path, dtype=str)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV file:\n{e}")
            return
        
        # Step 4: Replace 'nan' strings with real NaN
        df_import = df_import.replace("nan", pd.NA)
        
        # Able to only import CV or TCT values
        import_cv = self.import_cv_input.isChecked()
        import_tct = self.import_tct_input.isChecked()

        cv_cols = [col for col in df_import.columns if col.endswith("_CV")]
        tct_cols = [col for col in df_import.columns if col.endswith("_TCT")]

        if import_cv and not import_tct:
            df_import[tct_cols] = pd.NA  # wipe out TCT values
        elif import_tct and not import_cv:
            df_import[cv_cols] = pd.NA
        
        # Ensure required columns exist
        required_cols = ["campaign", "sensor_id", "annealing_time", "sat_V_CV", "sat_V_TCT"]
        for col in required_cols:
            if col not in df_import.columns:
                QMessageBox.critical(self, "Error", f"Missing required column: {col}")
                return
        
        # Step 5: Drop rows where both sat_V_CV and sat_V_TCT are NaN
        df_import = df_import.dropna(subset=["sat_V_CV", "sat_V_TCT"], how="all")
        
        # Step 6: Convert numeric cols to correct dtype
        numeric_cols = [
            "sat_V_CV", "sat_V_err_down_CV", "sat_V_err_up_CV",
            "low_fit_start_CV", "low_fit_stop_CV", "high_fit_start_CV", "high_fit_stop_CV",
            "sat_V_TCT", "sat_V_err_down_TCT", "sat_V_err_up_TCT",
            "low_fit_start_TCT", "low_fit_stop_TCT", "high_fit_start_TCT", "high_fit_stop_TCT"
        ]
        for col in numeric_cols:
            if col in df_import.columns:
                df_import[col] = pd.to_numeric(df_import[col], errors="coerce")
        
        # Step 7: Set index for matching
        df_import = df_import.set_index(["sensor_id", "campaign", "annealing_time"])
        
        # Step 8: Iterate through import rows and update database
        updated_rows = 0
        for (sensor_id, campaign, annealing_time), row in df_import.iterrows():
            # Find matching rows in database (multi-index has more levels)
            mask = (
                (self.database.index.get_level_values("sensor_id") == sensor_id) &
                (self.database.index.get_level_values("campaign") == campaign) &
                (self.database.index.get_level_values("annealing_time") == annealing_time)
            )
            
            if not mask.any():
                continue  # no match in DB → skip
            
            for col, val in row.items():
                if pd.isna(val):
                    continue  # skip empty values
                
                if overwrite:
                    # Overwrite only if the import value is not NaN
                    if not pd.isna(val):
                        self.database.loc[mask, col] = val
                        updated_rows += mask.sum()
                else:
                    # Only fill missing values in database
                    to_assign = mask & self.database[col].isna()
                    if to_assign.any():
                        self.database.loc[to_assign, col] = val
                        updated_rows += int(to_assign.sum())
        
        QMessageBox.information(
            self,
            "Import Successful",
            f"Imported {updated_rows} values from {os.path.basename(file_path)}"
        )
        
        # update and save database
        self.update_database(self.database)
        self.database.to_pickle(DEFAULT_DATABASE_PATH)
        
        # refresh database tab
        self.tab_display_database()
        
    
    def update_unique_sensor_id(self, select_all=False):
        # Save previous selected sensor ID to select it again after filtering
        previous_sensor_id = self.sensor_id_input.get_selected_items()
        
        campaigns = self.campaigns_database_input.get_selected_items()
        
        if self.database is not None:
            mask = (
                self.database.index.get_level_values("campaign").isin(campaigns)
            )

            unique_sensor_id = self.database[mask].index.get_level_values("sensor_id").unique().tolist()
            if self.sensor_id_input is not None:
                self.sensor_id_input.clear()
                self.sensor_id_input.addItems(unique_sensor_id)
                if select_all:
                    self.sensor_id_input.select_all()
                else:
                    self.sensor_id_input.select_from_list(previous_sensor_id)
        else:
            if self.sensor_id_input is not None:
                self.sensor_id_input.clear()


    def update_unique_annealing_time(self, select_all=False):
        # Save previous selected sensor ID to select it again after filtering
        previous_annealing_time = self.annealing_time_input.get_selected_items()
        
        sensor_id = self.sensor_id_input.get_selected_items()
        if self.database is not None:
            mask = (
                self.database.index.get_level_values("sensor_id").isin(sensor_id)
            )

            unique_annealing_time = self.database[mask].index.get_level_values("annealing_time").unique().tolist()
            if self.annealing_time_input is not None:
                self.annealing_time_input.clear()
                self.annealing_time_input.addItems(sort_annealing_time(unique_annealing_time))
                if select_all:
                    self.annealing_time_input.select_all()
                else:
                    self.annealing_time_input.select_from_list(previous_annealing_time)
        else:
            if self.annealing_time_input is not None:
                self.annealing_time_input.clear()