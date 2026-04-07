from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt
import numpy as np

from Utils.CheckableComboBox import CheckableComboBox
from config import DEFAULT_DATABASE_PATH, DEFAULT_COLUMNS_TO_DISPLAY_DATABASE
from Utils.create_database_helper import sort_annealing_time, extract_unique_values_from_database

class DisplayDatabaseTab(QWidget):
    def __init__(self, retrieve_database, update_database, tab_display_database):
        super().__init__()
        
        self.retrieve_database = retrieve_database
        self.update_database = update_database
        self.tab_display_database = tab_display_database
        
        self.database = self.retrieve_database()
        
        self.campaigns, self.thickness, self.annealing_time, self.annealing_temp, self.sensor_id, self.measurement_type = extract_unique_values_from_database(self.database)

        display_layout = QVBoxLayout(self)
        display_layout.setAlignment(Qt.AlignTop)
        display_layout.setSpacing(20)

        # Database path
        database_path_layout = QVBoxLayout()
        database_path_layout.setSpacing(5)
        self.database_path_input = QLineEdit()
        self.database_path_input.setText(DEFAULT_DATABASE_PATH)
        self.database_path_button = QPushButton("Browse")
        self.database_path_button.clicked.connect(self.select_database_save_path)
        database_path_layout.addWidget(QLabel("Database Path:"))
        database_path_layout.addWidget(self.database_path_input)
        database_path_layout.addWidget(self.database_path_button)
        display_layout.addLayout(database_path_layout)
        
        # CheckableComboBox for DATABASE_CAMPAIGNS
        campaigns_database_layout = QVBoxLayout()
        campaigns_database_layout.setSpacing(5)
        self.campaigns_database_input = CheckableComboBox()
        self.campaigns_database_input.add_external_callback(self.update_unique_annealing_time)
        self.campaigns_database_input.addItems(self.campaigns, select_all=True)
        campaigns_database_layout.addWidget(QLabel("Database Campaign:"))
        campaigns_database_layout.addWidget(self.campaigns_database_input)
        display_layout.addLayout(campaigns_database_layout)

        # CheckableComboBox for MEASUREMENT_TYPE
        measurement_type_layout = QVBoxLayout()
        measurement_type_layout.setSpacing(5)
        self.measurement_type_input = CheckableComboBox()
        self.measurement_type_input.add_external_callback(self.update_unique_annealing_time)
        self.measurement_type_input.addItems(self.measurement_type, select_all=True)
        measurement_type_layout.addWidget(QLabel("Measurement Type:"))
        measurement_type_layout.addWidget(self.measurement_type_input)
        display_layout.addLayout(measurement_type_layout)

        # CheckableComboBox for THICKNESS
        thickness_layout = QVBoxLayout()
        thickness_layout.setSpacing(5)
        self.thickness_input = CheckableComboBox()
        self.thickness_input.add_external_callback(self.update_unique_annealing_time)
        self.thickness_input.addItems(self.thickness, select_all=True)
        thickness_layout.addWidget(QLabel("Thickness:"))
        thickness_layout.addWidget(self.thickness_input)
        display_layout.addLayout(thickness_layout)

        # CheckableComboBox for ANNEALING_TEMP
        annealing_temp_layout = QVBoxLayout()
        annealing_temp_layout.setSpacing(5)
        self.annealing_temp_input = CheckableComboBox()
        self.annealing_temp_input.add_external_callback(self.update_unique_annealing_time)
        self.annealing_temp_input.addItems(self.annealing_temp, select_all=True)
        annealing_temp_layout.addWidget(QLabel("Annealing Temperature:"))
        annealing_temp_layout.addWidget(self.annealing_temp_input)
        display_layout.addLayout(annealing_temp_layout)

        # CheckableComboBox for ANNEALING_TIME
        annealing_time_layout = QVBoxLayout()
        annealing_time_layout.setSpacing(5)
        
        # Create horizontal layout for label and select/deselect buttons
        annealing_time_header_layout = QHBoxLayout()
        annealing_time_header_layout.setSpacing(5)
        annealing_time_header_layout.addWidget(QLabel("Annealing time:"))
        
        # Create buttons with compact size
        annealing_time_select_all = QPushButton("Select All")
        annealing_time_select_all.setFixedWidth(70)
        annealing_time_select_all.setStyleSheet("font-size: 10px;")
        
        annealing_time_deselect_all = QPushButton("Deselect All")
        annealing_time_deselect_all.setFixedWidth(70) 
        annealing_time_deselect_all.setStyleSheet("font-size: 10px;")
        
        # Add spacer to push buttons to the right
        annealing_time_header_layout.addStretch()
        annealing_time_header_layout.addWidget(annealing_time_select_all)
        annealing_time_header_layout.addWidget(annealing_time_deselect_all)
        
        # Add the header layout to the main layout
        annealing_time_layout.addLayout(annealing_time_header_layout)
        
        # Create the combo box
        self.annealing_time_input = CheckableComboBox()
        self.annealing_time_input.addItems(self.annealing_time, select_all=True)
        annealing_time_layout.addWidget(self.annealing_time_input)
        
        # Connect the buttons to the combo box methods
        annealing_time_select_all.clicked.connect(self.annealing_time_input.select_all)
        annealing_time_deselect_all.clicked.connect(self.annealing_time_input.deselect_all)
        
        display_layout.addLayout(annealing_time_layout)

        # Set line to enhance design
        display_line_widget = QLabel("=================================================\n" + "                                      Delete row by setting thickness to 0        " +   "\n=================================================")
        display_layout.addWidget(display_line_widget)
        
        # CheckableComboBox for selecting columns to display
        display_columns_layout = QVBoxLayout()
        display_columns_layout.setSpacing(5)
        self.display_columns_input = CheckableComboBox()
        # Add all columns from the SELECTED_COLUMNS_TO_DISPLAY_DATABASE dictionary
        for column, checked in DEFAULT_COLUMNS_TO_DISPLAY_DATABASE.items():
            self.display_columns_input.addItem(column, checked=checked)
            self.display_columns_input.update_selected_items()
        display_columns_layout.addWidget(QLabel("Columns to Display:"))
        display_columns_layout.addWidget(self.display_columns_input)
        display_layout.addLayout(display_columns_layout)
        
        # Display Database Button
        self.display_database_button = QPushButton("Display Database")
        self.display_database_button.clicked.connect(self.tab_display_database)
        self.display_database_button.setStyleSheet("""
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
        display_layout.addWidget(self.display_database_button)
        
    def select_database_save_path(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select .pkl File", DEFAULT_DATABASE_PATH, "Pickle Files (*.pkl)")
        if file_path:
            self.database_path_input.setText(file_path)
        
    def update_unique_annealing_time(self):
        self.database = self.retrieve_database()
        
        previous_annealing_time = self.annealing_time_input.get_selected_items()
        campaigns = self.campaigns_database_input.get_selected_items()
        measurement_type = self.measurement_type_input.get_selected_items()
        annealing_temp = [float(temp) for temp in self.annealing_temp_input.get_selected_items()]
        thickness = [float(t) for t in self.thickness_input.get_selected_items()]
        unique_annealing_times = []
        if self.database is not None:
            mask = (
                self.database.index.get_level_values("campaign").isin(campaigns) &
                self.database["type"].isin(measurement_type) &
                self.database["annealing_temp"].isin(annealing_temp) &
                self.database.index.get_level_values("thickness").isin(thickness)
            )
            unique_annealing_times = self.database[mask].index.get_level_values("annealing_time").unique().tolist()
        else:
            unique_annealing_times = []

        if self.annealing_time_input is not None:
            self.annealing_time_input.clear()
            self.annealing_time_input.addItems(sort_annealing_time(np.unique(unique_annealing_times)))
            self.annealing_time_input.select_from_list(previous_annealing_time)