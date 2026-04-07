from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QComboBox, 
    QFileDialog, QSizePolicy, QTabWidget
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import re
import matplotlib.pyplot as plt

from Utils.annealing_helper import read_annealing_file, calculate_equivalent_annealing_time

from config import DEFAULT_DIR_ANNEALING_FILES, ANNEALING_TEMP_OVEN, RC_PLOT_STYLE, PLOT_STYLE

class AnnealingTab(QWidget):
    def __init__(self):
        super().__init__()

        self.annealing_tab()


    def annealing_tab(self):
        # Layout for the plotting tab
        self.annealing_tab_layout = QHBoxLayout(self)

        # Left side: Plot area inside a container
        self.fig = Figure(dpi=300)
        self.fig.set_constrained_layout(True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.annealing_tab_layout.addWidget(self.canvas)

        # Right side: Input area
        self.input_tabs = QTabWidget()
        self.annealing_tab_layout.addWidget(self.input_tabs)  

        # Tab Plot IV/CV/TCT
        self.annealing_tab = QWidget()
        self.annealing_layout = QVBoxLayout(self.annealing_tab)
        
        # Annealing file
        self.annealing_file= QLineEdit()
        self.annealing_file.setText(DEFAULT_DIR_ANNEALING_FILES)
        self.annealing_file_button = QPushButton("Choose Annealing File")
        self.annealing_file_button.clicked.connect(self.select_annealing_file)
        self.annealing_layout.addWidget(QLabel("Annealing File:"))
        self.annealing_layout.addWidget(self.annealing_file)
        self.annealing_layout.addWidget(self.annealing_file_button)
        
        # Add temperature dropdown
        self.annealing_temp_dropdown = QComboBox()
        self.annealing_temp_dropdown.addItems(ANNEALING_TEMP_OVEN)
        self.annealing_layout.addWidget(QLabel("Annealing Temperature:"))
        self.annealing_layout.addWidget(self.annealing_temp_dropdown)
        
        # Add plot button
        self.plot_annealing_temp_vs_time_button = QPushButton("Plot Annealing Temp vs Time")
        self.plot_annealing_temp_vs_time_button.clicked.connect(self.plot_annealing_temp_vs_time)
        self.annealing_layout.addWidget(self.plot_annealing_temp_vs_time_button)
        
        self.annealing_layout.addStretch(1)
        
        # Add the Plot Diodes tab to the QTabWidget
        self.input_tabs.addTab(self.annealing_tab, "Annealing")

        # Add input tabs to the plot tab
        self.annealing_tab_layout.addWidget(self.input_tabs)
        self.annealing_tab_layout.setStretch(0, 7)
        self.annealing_tab_layout.setStretch(1, 2)
        
        
    def select_annealing_file(self):
        # Get the current directory from the QLineEdit or use default
        current_dir = self.annealing_file.text()
        
        # If the current text is a file path, get its directory
        if os.path.isfile(current_dir):
            directory = os.path.dirname(current_dir)
        elif os.path.isdir(current_dir):
            directory = current_dir
        else:
            directory = DEFAULT_DIR_ANNEALING_FILES
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Annealing File",
            directory,  # Set the starting directory
            "All Files (*);;Text Files (*.txt)"  # Optional: filter file types
        )
        if file_path:
            self.annealing_file.setText(file_path)
            self.automatically_detect_annealing_temp()
            
    def automatically_detect_annealing_temp(self):
        """
        Automatically detect the annealing temperature from the filename
        and update the dropdown with the detected value.
        """
        filename = self.annealing_file.text()

        # Search for a pattern like "20C", "30C", etc.
        match = re.search(r'(\d+)C', filename)
        if match:
            annealing_temp = float(match.group(1))
            self.annealing_temp_dropdown.setCurrentText(f"{annealing_temp}")
            print(f"\nAnnealing temperature detected from filename: {annealing_temp}°C")
        else:
            # Fallback if no temperature found
            annealing_temp = None
            print("\nCould not detect annealing temperature in filename.")
        
                
    def plot_annealing_temp_vs_time(self):
        # Remove old canvas
        if hasattr(self, "canvas"):
            self.annealing_tab_layout.removeWidget(self.canvas)
            self.canvas.deleteLater()

        # Create new figure and axes without fixed size
        plt.rcParams.update(RC_PLOT_STYLE)
        self.fig = Figure(dpi=300)  # No fixed figsize
        self.fig.set_constrained_layout(True)  # Use constrained layout for automatic adjustment
        self.ax = self.fig.add_subplot(111)

        # Create new canvas with expanding size policy
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Remove these lines that restrict the layout:
        # self.fig.tight_layout(pad=3)
        # self.fig.subplots_adjust(left=0.1, right=0.95)

        self.annealing_tab_layout.insertWidget(0, self.canvas)
        # Remove alignment constraint to allow full expansion
        # self.annealing_tab_layout.setAlignment(self.canvas, Qt.AlignRight)
        self.annealing_tab_layout.setStretch(0, 7)
        self.annealing_tab_layout.setStretch(1, 2)
        
        filename = self.annealing_file.text()
        annealing_temp = float(self.annealing_temp_dropdown.currentText())
        time, temp = read_annealing_file(filename)
        equivalent_annealing_time_epi, equivalent_annealing_time_fz = calculate_equivalent_annealing_time(filename, annealing_temp)
        
        # Extract target time from filename
        target_time = None
        # Try to match minutes 
        min_match = re.search(r'(\d+)min', filename, re.IGNORECASE)
        if min_match:
            target_time = int(min_match.group(1))
        else:
            # Try to match days or day
            days_match = re.search(r'(\d+)day', filename, re.IGNORECASE)
            if days_match:
                days = int(days_match.group(1))
                target_time = days * 24 * 60  # Convert days to minutes
        
        # Plot the annealing temp vs time with solid line
        self.ax.plot(time, temp, label="Measured Temperature", 
                    linewidth=1.5, color="black")
        
        # Plot horizontal line at the annealing temp
        self.ax.axhline(annealing_temp, color="red", linestyle="--", 
                        label=f"Target Temperature: {annealing_temp}°C", 
                        linewidth=1.5)

        # Dummy handle for equivalent annealing time and target time
        equiv_label = f"Equivalent Annealing Time EPI: {equivalent_annealing_time_epi:.2f} min"
        equiv_label_fz = f"Equivalent Annealing Time FZ: {equivalent_annealing_time_fz:.2f} min"
        self.ax.plot([], [], ' ', label=equiv_label)
        self.ax.plot([], [], ' ', label=equiv_label_fz)
        if target_time:
            target_time_label = f"Target Time: {target_time} min"
            self.ax.plot([], [], ' ', label=target_time_label)
        
        # Legend
        legend = self.ax.legend(
            fontsize=7, 
            markerscale=1, 
            loc="best", 
            shadow=False,
            frameon=True, 
            borderaxespad=1.2, 
            fancybox=True, 
            framealpha=0.7,
            handlelength=2
        )

        legend.get_frame().set_linewidth(PLOT_STYLE["axes.border.width"])
        legend.get_frame().set_edgecolor("black")
        
        # self.ax.set_ylim(35, 65)
        self.ax.set_xlim(min(time) - 0.05 * max(time), max(time) + 0.05 * max(time))
        self.ax.set_xscale("linear")
        self.ax.set_yscale("linear")
        
        # Tick parameters
        self.ax.tick_params(
            axis='both', 
            which='major',
            labelsize=11,
            size=PLOT_STYLE["axes.tick.major.size"],
            width=PLOT_STYLE["axes.tick.major.width"]
        )
        self.ax.tick_params(
            axis='both',
            which='minor',
            size=PLOT_STYLE["axes.tick.minor.size"],
            width=PLOT_STYLE["axes.tick.minor.width"]
        )
        
        # Axis labels
        self.ax.set_xlabel("Time [s]", 
                        fontsize=13, 
                        fontweight='bold')
        self.ax.set_ylabel("Temperature [°C]", 
                        fontsize=13, 
                        fontweight='bold')
        
        # Set spine width
        for spine in self.ax.spines.values():
            spine.set_linewidth(PLOT_STYLE["axes.border.width"])
        
        # Grid
        self.ax.grid(True, alpha=0.5, linestyle=":", linewidth=0.3)
        
        # Canvas will automatically resize with constrained_layout
        self.canvas.draw()