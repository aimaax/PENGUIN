from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, 
    QCheckBox, QGridLayout
)
from PySide6.QtCore import Qt
from config import PLOT_STYLE, MATPLOTLIB_COLORS
from Utils.DoubleSlider import DoubleSlider
 
    
class SettingsPlot(QWidget):
    def __init__(self, plot_function):
        super().__init__() # initialize the QWidget
        
        self.setMinimumWidth(300)
        # Plot Settings
        self.plot_settings_layout = QVBoxLayout(self)

        # Zoom toggle butto
        self.zoom_button = QPushButton("Zoom")
        self.zoom_button.setCheckable(True)
        self.zoom_button.setChecked(False)
        self.zoom_button.setFixedWidth(50)

        # Reset zoom button
        self.reset_zoom_button = QPushButton("Reset")
        self.reset_zoom_button.setFixedWidth(50)
        
        # Log Y-axis Checkbox
        self.logy_input = QCheckBox("Log Y-axis")
        
        # Log X-axis Checkbox
        self.logx_input = QCheckBox("Log X-axis")
        
        # Horizontal layout with Log X-axis and Log Y-axis checkboxes
        log_box_layout = QHBoxLayout()
        log_box_layout.addWidget(self.logx_input)
        log_box_layout.addSpacing(10)
        log_box_layout.addWidget(self.logy_input)
        log_box_layout.addStretch(1)
        log_box_layout.addWidget(self.zoom_button)
        log_box_layout.addWidget(self.reset_zoom_button)
        log_box_layout.addStretch(1)
        self.plot_settings_layout.addLayout(log_box_layout)

        # Y-axis Limits
        lim_layout = QVBoxLayout()
        self.ylim_min_input = QLineEdit()
        self.ylim_min_input.setPlaceholderText("")
        self.ylim_max_input = QLineEdit()
        self.ylim_max_input.setPlaceholderText("")
        
        # Horizontal layout with Y-axis Limits
        ylim_box_layout = QHBoxLayout()
        ylim_box_layout.addWidget(self.ylim_min_input)
        ylim_box_layout.addWidget(QLabel("to"))
        ylim_box_layout.addWidget(self.ylim_max_input)
        
        # X-axis Limits
        self.xlim_min_input = QLineEdit()
        self.xlim_min_input.setPlaceholderText("")
        self.xlim_max_input = QLineEdit()
        self.xlim_max_input.setPlaceholderText("")
        
        # Horizontal layout with X-axis Limits
        xlim_box_layout = QHBoxLayout()
        xlim_box_layout.addWidget(self.xlim_min_input)
        xlim_box_layout.addWidget(QLabel("to"))
        xlim_box_layout.addWidget(self.xlim_max_input)
        
        lim_box_layout = QGridLayout()

        lim_box_layout.addWidget(QLabel("Y-axis Limits:"), 0, 0)
        lim_box_layout.addLayout(ylim_box_layout, 1, 0)
        lim_box_layout.addWidget(QLabel("X-axis Limits:"), 0, 1)
        lim_box_layout.addLayout(xlim_box_layout, 1, 1)
        
        self.plot_settings_layout.addLayout(lim_box_layout)
        
        # X-axis and Y-axis custom labels
        label_layout = QHBoxLayout()
        self.xlabel_input = QLineEdit()
        self.xlabel_input.setPlaceholderText("Custom x-axis label")
        self.ylabel_input = QLineEdit()
        self.ylabel_input.setPlaceholderText("Custom y-axis label")
        label_layout.addWidget(self.ylabel_input)
        label_layout.addWidget(self.xlabel_input)
        self.plot_settings_layout.addLayout(label_layout)
        
        
        # # Text on Axis Slider
        # self.text_on_axis_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        # self.text_on_axis_slider.setMinimum(0.5)
        # self.text_on_axis_slider.setMaximum(20)
        # self.text_on_axis_slider.setSingleStep(0.5)
        # self.text_on_axis_slider.setValue(PLOT_STYLE["axes.textonaxis.size"])
        # self.text_on_axis_slider.setTickPosition(DoubleSlider.TicksBelow)
        # self.text_on_axis_slider.setTickInterval(0.5)
        
        # # Update the label whenever the slider moves
        # self.text_on_axis_slider.doubleValueChanged.connect(
        #     lambda value: self.text_on_axis_value_label.setText(f"Text on Axis: {value}")
        # )
        
        # self.text_on_axis_value_label = QLabel(f"Text on Axis: {PLOT_STYLE['axes.textonaxis.size']}")
        # self.plot_settings_layout.addWidget(self.text_on_axis_value_label)
        # self.plot_settings_layout.addWidget(self.text_on_axis_slider)
        
        # Text box Slider
        self.text_box_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.text_box_slider.setMinimum(0.5)
        self.text_box_slider.setMaximum(20)
        self.text_box_slider.setSingleStep(0.5)
        self.text_box_slider.setValue(PLOT_STYLE["axes.textbox.size"])
        self.text_box_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.text_box_slider.setTickInterval(0.5)
        self.text_box_value_label = QLabel(f"Text Box: {PLOT_STYLE['axes.textbox.size']}")
        text_box_layout = QVBoxLayout()
        text_box_layout.addWidget(self.text_box_value_label)
        text_box_layout.addSpacing(-6)
        text_box_layout.addWidget(self.text_box_slider)
        self.plot_settings_layout.addLayout(text_box_layout)
        
        # Update the label whenever the slider moves
        self.text_box_slider.doubleValueChanged.connect(
            lambda value: self.text_box_value_label.setText(f"Text Box: {value}")
        )

        # Enable custom textbox 
        self.custom_text_check = QCheckBox("Enable Custom Box")
        self.custom_text_check.setChecked(False)
        self.custom_text_input = QLineEdit()
        self.custom_text_input.setPlaceholderText("Write custom text here")

        # Horizontal layout with Enable/Disable title checkbox and label
        custom_text_box_layout = QHBoxLayout()
        custom_text_box_layout.addWidget(self.custom_text_check)
        custom_text_box_layout.addWidget(self.custom_text_input)
        self.plot_settings_layout.addLayout(custom_text_box_layout)
        
        # Border Width slider
        self.border_width_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.border_width_slider.setMinimum(0.5)
        self.border_width_slider.setMaximum(10)
        self.border_width_slider.setSingleStep(0.5)
        self.border_width_slider.setValue(PLOT_STYLE["axes.border.width"])         # default value
        self.border_width_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.border_width_slider.setTickInterval(0.5)
        self.border_width_value_label = QLabel(f"Border Width: {PLOT_STYLE['axes.border.width']}")
        border_width_layout = QVBoxLayout()
        border_width_layout.addWidget(self.border_width_value_label)
        border_width_layout.addSpacing(-6)
        border_width_layout.addWidget(self.border_width_slider)
        self.plot_settings_layout.addLayout(border_width_layout)
        
        # Update the label whenever the slider moves
        self.border_width_slider.doubleValueChanged.connect(
            lambda value: self.border_width_value_label.setText(f"Border Width: {value}")
        )
        
        # Tick Label Size slider
        self.tick_label_size_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.tick_label_size_slider.setMinimum(0.5)
        self.tick_label_size_slider.setMaximum(20)  
        self.tick_label_size_slider.setSingleStep(0.5)
        self.tick_label_size_slider.setValue(PLOT_STYLE["axes.tick.major.label.size"])         # default value
        self.tick_label_size_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.tick_label_size_slider.setTickInterval(0.5)
        self.tick_label_size_value_label = QLabel(f"Tick Label Size: {PLOT_STYLE['axes.tick.major.label.size']}")
        tick_label_size_layout = QVBoxLayout()
        tick_label_size_layout.addWidget(self.tick_label_size_value_label)
        tick_label_size_layout.addSpacing(-6)
        tick_label_size_layout.addWidget(self.tick_label_size_slider)
        self.plot_settings_layout.addLayout(tick_label_size_layout)
        
        # Update the label whenever the slider moves
        self.tick_label_size_slider.doubleValueChanged.connect(
            lambda value: self.tick_label_size_value_label.setText(f"Tick Label Size: {value}")
        )
        
        # Major Tick Size slider
        self.tick_size_major_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.tick_size_major_slider.setMinimum(0.5)
        self.tick_size_major_slider.setMaximum(10)      
        self.tick_size_major_slider.setSingleStep(0.5)
        self.tick_size_major_slider.setValue(PLOT_STYLE["axes.tick.major.size"])       
        self.tick_size_major_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.tick_size_major_slider.setTickInterval(0.5)
        self.tick_size_major_value_label = QLabel(f"Major Tick Size: {PLOT_STYLE['axes.tick.major.size']}")
        tick_size_major_layout = QVBoxLayout()
        tick_size_major_layout.addWidget(self.tick_size_major_value_label)
        tick_size_major_layout.addSpacing(-6)
        tick_size_major_layout.addWidget(self.tick_size_major_slider)
        self.plot_settings_layout.addLayout(tick_size_major_layout)
        
        # Update the label whenever the slider moves
        self.tick_size_major_slider.doubleValueChanged.connect(
            lambda value: self.tick_size_major_value_label.setText(f"Major Tick Size: {value}")
        )
        
        # Major Tick Width slider
        self.tick_width_major_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.tick_width_major_slider.setMinimum(0.5)
        self.tick_width_major_slider.setMaximum(10)      
        self.tick_width_major_slider.setSingleStep(0.5)
        self.tick_width_major_slider.setValue(PLOT_STYLE["axes.tick.major.width"])       
        self.tick_width_major_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.tick_width_major_slider.setTickInterval(0.5)
        self.tick_width_major_value_label = QLabel(f"Major Tick Width: {PLOT_STYLE['axes.tick.major.width']}")
        tick_width_major_layout = QVBoxLayout()
        tick_width_major_layout.addWidget(self.tick_width_major_value_label)
        tick_width_major_layout.addSpacing(-6)
        tick_width_major_layout.addWidget(self.tick_width_major_slider)
        self.plot_settings_layout.addLayout(tick_width_major_layout)
        
        # Update the label whenever the slider moves
        self.tick_width_major_slider.doubleValueChanged.connect(
            lambda value: self.tick_width_major_value_label.setText(f"Major Tick Width: {value}")
        )
        
        # Minor Tick Size slider
        self.tick_size_minor_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.tick_size_minor_slider.setMinimum(0.5)
        self.tick_size_minor_slider.setMaximum(10)      
        self.tick_size_minor_slider.setSingleStep(0.5)
        self.tick_size_minor_slider.setValue(PLOT_STYLE["axes.tick.minor.size"])       
        self.tick_size_minor_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.tick_size_minor_slider.setTickInterval(0.5)
        self.tick_size_minor_value_label = QLabel(f"Minor Tick Size: {PLOT_STYLE['axes.tick.minor.size']}")
        tick_size_minor_layout = QVBoxLayout()
        tick_size_minor_layout.addWidget(self.tick_size_minor_value_label)
        tick_size_minor_layout.addSpacing(-6)
        tick_size_minor_layout.addWidget(self.tick_size_minor_slider)
        self.plot_settings_layout.addLayout(tick_size_minor_layout)
        
        # Update the label whenever the slider moves
        self.tick_size_minor_slider.doubleValueChanged.connect(
            lambda value: self.tick_size_minor_value_label.setText(f"Minor Tick Size: {value}")
        )
        
        # Minor Tick Width slider
        self.tick_width_minor_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.tick_width_minor_slider.setMinimum(0.5)
        self.tick_width_minor_slider.setMaximum(10)      
        self.tick_width_minor_slider.setSingleStep(0.5)
        self.tick_width_minor_slider.setValue(PLOT_STYLE["axes.tick.minor.width"])       
        self.tick_width_minor_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.tick_width_minor_slider.setTickInterval(0.5)
        self.tick_width_minor_value_label = QLabel(f"Minor Tick Width: {PLOT_STYLE['axes.tick.minor.width']}")
        tick_width_minor_layout = QVBoxLayout()
        tick_width_minor_layout.addWidget(self.tick_width_minor_value_label)
        tick_width_minor_layout.addSpacing(-6)
        tick_width_minor_layout.addWidget(self.tick_width_minor_slider)
        self.plot_settings_layout.addLayout(tick_width_minor_layout)
        
        # Update the label whenever the slider moves
        self.tick_width_minor_slider.doubleValueChanged.connect(
            lambda value: self.tick_width_minor_value_label.setText(f"Minor Tick Width: {value}")
        )

        self.fontsize_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.fontsize_slider.setMinimum(0.5)
        self.fontsize_slider.setMaximum(40)
        self.fontsize_slider.setSingleStep(0.5)
        self.fontsize_slider.setValue(PLOT_STYLE["axes.font.size"])
        self.fontsize_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.fontsize_slider.setTickInterval(0.5)

        self.fontsize_value_label = QLabel(f"Axis Font Size: {PLOT_STYLE['axes.font.size']}")
        fontsize_layout = QVBoxLayout()
        fontsize_layout.addWidget(self.fontsize_value_label)
        fontsize_layout.addSpacing(-6)
        fontsize_layout.addWidget(self.fontsize_slider)
        self.plot_settings_layout.addLayout(fontsize_layout)

        # Update the label whenever the slider moves
        self.fontsize_slider.doubleValueChanged.connect(
            lambda value: self.fontsize_value_label.setText(f"Axis Font Size: {value}")
        )
        
        # Marker Size slider
        self.marker_size_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.marker_size_slider.setMinimum(0.5)
        self.marker_size_slider.setMaximum(20)      
        self.marker_size_slider.setSingleStep(0.5)
        self.marker_size_slider.setValue(PLOT_STYLE["marker.size"])       
        self.marker_size_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.marker_size_slider.setTickInterval(0.5)
        self.marker_size_value_label = QLabel(f"Marker Size: {PLOT_STYLE['marker.size']}")
        marker_size_layout = QVBoxLayout()
        marker_size_layout.addWidget(self.marker_size_value_label)
        marker_size_layout.addSpacing(-6)
        marker_size_layout.addWidget(self.marker_size_slider)
        self.plot_settings_layout.addLayout(marker_size_layout)
        
        # Update the label whenever the slider moves
        self.marker_size_slider.doubleValueChanged.connect(
            lambda value: self.marker_size_value_label.setText(f"Marker Size: {value}")
        )
        
        # Line Width slider
        self.line_width_slider = DoubleSlider(Qt.Horizontal, decimals=1)
        self.line_width_slider.setMinimum(0.5)
        self.line_width_slider.setMaximum(4)      
        self.line_width_slider.setSingleStep(0.25)
        self.line_width_slider.setValue(PLOT_STYLE["line.width"])       
        self.line_width_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.line_width_slider.setTickInterval(0.25)
        self.line_width_value_label = QLabel(f"Line Width: {PLOT_STYLE['line.width']}")
        line_width_layout = QVBoxLayout()
        line_width_layout.addWidget(self.line_width_value_label)
        line_width_layout.addSpacing(-6)
        line_width_layout.addWidget(self.line_width_slider)
        self.plot_settings_layout.addLayout(line_width_layout)
        
        # Update the label whenever the slider moves
        self.line_width_slider.doubleValueChanged.connect(
            lambda value: self.line_width_value_label.setText(f"Line Width: {value}")
        )
        
        # Legend size
        self.legend_size_slider = DoubleSlider(Qt.Horizontal, decimals=0)
        self.legend_size_slider.setMinimum(1)
        self.legend_size_slider.setMaximum(7)      
        self.legend_size_slider.setSingleStep(1)
        self.legend_size_slider.setValue(PLOT_STYLE["legend.size"])       
        self.legend_size_slider.setTickPosition(DoubleSlider.TicksBelow)
        self.legend_size_slider.setTickInterval(1)
        self.legend_size_value_label = QLabel(f"Legend Size: {PLOT_STYLE['legend.size']}")
        legend_size_layout = QVBoxLayout()
        legend_size_layout.addWidget(self.legend_size_value_label)
        legend_size_layout.addSpacing(-6)
        legend_size_layout.addWidget(self.legend_size_slider)
        self.plot_settings_layout.addLayout(legend_size_layout)
        
        # Update the label whenever the slider moves
        self.legend_size_slider.doubleValueChanged.connect(
            lambda value: self.legend_size_value_label.setText(f"Legend Size: {value}")
        )
        
        # Specify color of the plot and skip colors
        combined_color_list = ["Custom Colors (config.py)", "Custom Colors (one per sensor)"] + list(MATPLOTLIB_COLORS.keys())
        self.color_input = QComboBox()
        self.color_input.addItems(combined_color_list)
        self.color_input.setPlaceholderText("Specify color palette of the plot")

        # Skip colors/markers input
        self.skip_x_colors_markers_input = QComboBox()
        self.skip_x_colors_markers_input.addItems([str(i) for i in range(8)])  # 0-7 skip options
        self.skip_x_colors_markers_input.setCurrentIndex(0)  # Default to 0 (no skip)
        self.skip_x_colors_markers_input.setPlaceholderText("Skip colors/markers")
        
        # Horizontal layout for color selection and skip colors
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_input, stretch=3)  # Give color input more space
        color_layout.addWidget(QLabel("Skip:"))
        color_layout.addWidget(self.skip_x_colors_markers_input, stretch=1)
        
        self.plot_settings_layout.addLayout(color_layout)

        # Enable/Disable enable_different_color_check 
        self.color_input.currentTextChanged.connect(
            lambda text: (
                self.enable_different_color_check.setChecked(False) if text == "Custom Colors (config.py)" else None,
                self.enable_different_color_check.setEnabled(text != "Custom Colors (config.py)")
            )
        )
        
        # Enable different color for single sensor with different annealing time
        self.enable_different_color_check = QCheckBox("Enable Different Color for 1 Sensor with Different Ann. Time")
        self.enable_different_color_check.setChecked(False)
        self.enable_different_color_check.setEnabled(False)
        self.plot_settings_layout.addWidget(self.enable_different_color_check)
                
        # Horizontal layout with Enable/Disable title checkbox and label
        self.title_check = QCheckBox("Enable Title")
        self.title_check.setChecked(False)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Write custom title here")
        
        title_box_layout = QHBoxLayout()
        title_box_layout.addWidget(self.title_check)
        title_box_layout.addWidget(self.title_input)
        self.plot_settings_layout.addLayout(title_box_layout)
        
        # Horizontal layout for enable, disable, and legend placement QComboBox
        legend_layout = QHBoxLayout()
        # Enable/Disable legend checkbox
        self.legend_check = QCheckBox("Enable Legend")
        self.legend_check.setChecked(False)
        legend_layout.addWidget(self.legend_check)
        self.legend_placement_input = QComboBox()
        self.legend_placement_input.addItems(["best", "upper right", "upper left", "lower left", "lower right", "right", "center left", "center right", "lower center", "upper center", "center"])
        self.legend_placement_input.setCurrentIndex(0)
        legend_layout.addWidget(self.legend_placement_input)

        self.plot_settings_layout.addLayout(legend_layout)
        
        
        # Add Display Plot Button
        self.display_plot_button = QPushButton("Display Plot")
        self.display_plot_button.clicked.connect(plot_function)
        self.plot_settings_layout.addWidget(self.display_plot_button)
        
        self.plot_settings_layout.addStretch(1)
        