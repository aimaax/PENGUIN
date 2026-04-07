from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, QTextEdit, QFileDialog, QApplication
)
from PySide6.QtCore import Qt
from git import Repo

from config import DEFAULT_DATABASE_PATH, CAMPAIGNS, DEFAULT_MEASUREMENT_DIR_CHECKED, DEFAULT_OVERWRITE_COLUMNS_DATABASE, ANNEALING_TIME_BARE
from Utils.CheckableComboBox import CheckableComboBox
from Utils.create_database_helper import update_sensor_database
from config import ROOT_PATH_REPO, DEFAULT_DIR_DATA
import os


class CreateDatabaseTab(QWidget):
    def __init__(self, refresh_unique_lists_all_tabs, update_database, display_database):
        super().__init__()
        
        self.refresh_unique_lists_all_tabs = refresh_unique_lists_all_tabs
        self.update_database = update_database
        self.display_database = display_database
        
        
        create_database_layout = QVBoxLayout(self)
        create_database_layout.setAlignment(Qt.AlignTop)
        create_database_layout.setSpacing(10)

        # Save path
        save_path_layout = QVBoxLayout()
        save_path_layout.setSpacing(5)
        self.save_path_input = QLineEdit()
        self.save_path_input.setText(DEFAULT_DATABASE_PATH)
        self.save_path_button = QPushButton("Browse")
        self.save_path_button.clicked.connect(self.select_database_save_path)
        save_path_layout.addWidget(QLabel("Database Save Path:"))
        save_path_layout.addWidget(self.save_path_input)
        save_path_layout.addWidget(self.save_path_button)
        create_database_layout.addLayout(save_path_layout)

        # Set line to enhance design
        database_line_widget = QLabel("=================================================")
        create_database_layout.addWidget(database_line_widget)
        
        # ComboBox for CAMPAIGN
        campaign_layout = QVBoxLayout()
        campaign_layout.setSpacing(5)
        self.campaign_input = QComboBox()
        self.campaign_input.addItems(CAMPAIGNS)
        # self.campaign_input.currentTextChanged.connect(self.change_Google_Sheet_Paths)
        campaign_layout.addWidget(QLabel("Campaign | Name of folder under /Data/ :"))
        campaign_layout.addWidget(self.campaign_input)
        create_database_layout.addLayout(campaign_layout)

        # Set line to enhance design
        projects_database_line_widget = QLabel("=================================================")
        create_database_layout.addWidget(projects_database_line_widget)

        # ComboBox for MEASUREMENT_DIR
        measurement_dir_layout = QVBoxLayout()
        measurement_dir_layout.setSpacing(5)
        self.measurement_dir_input = CheckableComboBox()
        for column, checked in DEFAULT_MEASUREMENT_DIR_CHECKED.items():
            self.measurement_dir_input.addItem(column, checked=checked)
            self.measurement_dir_input.update_selected_items()
        self.measurement_dir_input.currentTextChanged.connect(self.enable_disable_annealing_time_dropdown)
        measurement_dir_layout.addWidget(QLabel("Measurement Directory under /Data/Campaign/:"))
        measurement_dir_layout.addWidget(self.measurement_dir_input)
        create_database_layout.addLayout(measurement_dir_layout)

        # ComboBox for ANNEALING_TIME_BARE
        annealing_time_layout = QVBoxLayout()
        annealing_time_layout.setSpacing(5)
        self.annealing_time_input = QComboBox()
        self.annealing_time_input.addItems(ANNEALING_TIME_BARE)
        annealing_time_layout.addWidget(QLabel("Annealing time bare (auto extracted with IVCV_onPCB and TCT):"))
        annealing_time_layout.addWidget(self.annealing_time_input)
        create_database_layout.addLayout(annealing_time_layout)
        
        # CheckableComboBox for overwriting columns 
        overwrite_columns_layout = QVBoxLayout()
        overwrite_columns_layout.setSpacing(5)
        self.overwrite_columns_input = CheckableComboBox()
        # Add all columns from the SELECTED_COLUMNS_TO_DISPLAY_DATABASE dictionary
        for column, checked in DEFAULT_OVERWRITE_COLUMNS_DATABASE.items():
            self.overwrite_columns_input.addItem(column, checked=checked)
            self.overwrite_columns_input.update_selected_items()
        overwrite_columns_layout.addWidget(QLabel("Columns to Overwrite:"))
        overwrite_columns_layout.addWidget(self.overwrite_columns_input)
        create_database_layout.addLayout(overwrite_columns_layout)

        # Create Database Button
        self.create_database_button = QPushButton("Create Database")
        self.create_database_button.setEnabled(False) # Disable create database when Google ID is hidden
        self.create_database_button.clicked.connect(self.create_database)
        self.create_database_button.setStyleSheet("""
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
        create_database_layout.addWidget(self.create_database_button)

        # Output Text
        self.output_text_database = QTextEdit()
        self.output_text_database.setReadOnly(True)
        create_database_layout.addWidget(QLabel("Output:"))
        create_database_layout.addWidget(self.output_text_database)
        
        self.enable_disable_annealing_time_dropdown()
        
        
    def select_database_save_path(self):
        file_save_path, _ = QFileDialog.getOpenFileName(self, "Select .pkl File", DEFAULT_DATABASE_PATH, "Pickle Files (*.pkl)")
        if file_save_path:
            self.save_path_input.setText(file_save_path)
            
    def enable_disable_annealing_time_dropdown(self):
        """
        Enable or disable dropdowns based on measurement directory selection
        """
        selected_items = self.measurement_dir_input.get_selected_items()
        # Enable only if IVCV_bare is selected
        enable_annealing_time_dropdown = "IVCV_bare" in selected_items
        self.annealing_time_input.setEnabled(enable_annealing_time_dropdown)
        
        
    def create_database(self):
        self.output_text_database.setPlainText("Creating database...")
        QApplication.processEvents()

        # Git pull the latest data from the repository
        repo = Repo(ROOT_PATH_REPO)
        origin = repo.remote(name='origin')
        origin.pull('master')
        print("Pulled latest data from the repository")

        self.output_text_database.setPlainText("Pulled latest data from the repository. Updating database... please wait...")
        QApplication.processEvents()

        db_path = self.save_path_input.text()
        campaign = self.campaign_input.currentText()
        annealing_time = self.annealing_time_input.currentText()
        measurement_dirs = self.measurement_dir_input.get_selected_items()
        if campaign == "DoubleIrrSRNeutron2025":
            root_path_data = os.path.join(DEFAULT_DIR_DATA, "DoubleIrrNeutron2025", "")
        else:
            root_path_data = os.path.join(DEFAULT_DIR_DATA, campaign, "")

        overwrite_columns = self.overwrite_columns_input.get_selected_items()
        if overwrite_columns == []:
            overwrite_columns = None

        output_text = ""

        if overwrite_columns == ["Blacklisted"]:
            database = update_sensor_database(
                db_path,
                overwrite_columns=["Blacklisted"]
            )
            self.output_text_database.setPlainText("Blacklisted measurements updated!")

        else:   
            if "IV_onPCB" in measurement_dirs and "CV_onPCB" in measurement_dirs:
                overwrite_CV_file = True
            else:
                overwrite_CV_file = False

            for measurement_dir in measurement_dirs:
                print(measurement_dir)
                if measurement_dir == "IVCV_bare":
                    type = "bare"
                elif measurement_dir == "IV_onPCB" or measurement_dir == "CV_onPCB" or measurement_dir == "TCT":
                    type = "onPCB"

                open_corr = None

                if measurement_dir == "TCT" and len(measurement_dirs) > 1:
                    # For TCT processing after other measurements, we want to update existing records
                    database = update_sensor_database(
                        db_path,  # Use the already updated database
                        campaign,
                        root_path_data,
                        measurement_dir,
                        annealing_time,
                        type,
                        open_corr,
                        overwrite_columns=["file_TCT", "TCT_corr"]  # Only overwrite TCT-related columns
                    )
                elif measurement_dir == "CV_onPCB" and overwrite_CV_file:
                    database = update_sensor_database(
                        db_path,
                        campaign,
                        root_path_data,
                        measurement_dir,
                        annealing_time,
                        type,
                        open_corr,
                        overwrite_columns=["file_CV"]
                    )
                else:
                    # For the first measurement or non-TCT measurements
                    database = update_sensor_database(
                        db_path,
                        campaign,
                        root_path_data,
                        measurement_dir,
                        annealing_time,
                        type,
                        open_corr,
                        overwrite_columns=overwrite_columns
                    )
                
                output_text += f"Added {measurement_dir} measurements to database.\n"
            
            output_text = (
                f"{campaign} Database created! \n"
            )

            self.output_text_database.setPlainText(output_text)

        # pd.set_option('display.max.rows', None)
        # pd.set_option('display.max.columns', None)
        # pd.set_option('display.width', None)
        # pd.set_option('display.max_colwidth', None)
        # print(database)
        
        self.update_database(database)

        self.display_database(database)

        # Refresh unique lists in all tabs
        self.refresh_unique_lists_all_tabs()