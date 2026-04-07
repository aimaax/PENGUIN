from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout
from GUI.PlotTab import PlotTab
from GUI.DatabaseTab import DatabaseTab
# from GUI.CurrentVolumeNormTab import CurrentVolumeNormTab
from GUI.CurrentVolumeNorm.IVolNormFluenceTab import IVolNormFluenceTab
from GUI.CurrentVolumeNorm.IVolNormAnnealingTab import IVolNormAnnealingTab
from GUI.SaturationVoltage.SaturationVoltageFitTab import SaturationVoltageFitTab
from GUI.SaturationVoltage.SaturationVoltageFluenceTab import SaturationVoltageFluenceTab
from GUI.ChargeCollection.CCFluenceTab import CCFluenceTab
from GUI.ChargeCollectionEfficiency.CCEFluenceTab import CCEFluenceTab
from GUI.ChargeCollectionEfficiency.CCEAnnealingTab import CCEAnnealingTab
from GUI.ChargeCollection.CCAnnealingTab import CCAnnealingTab
from GUI.SaturationVoltage.SaturationVoltageAnnealingTab import SaturationVoltageAnnealingTab
from GUI.AnnealingTab import AnnealingTab
from GUI.DIHFComparisonTab import DIHFComparisonTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plotting and Database Manager GUI")

        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        main_layout = QVBoxLayout(main_widget)

        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Add Plotting Tab
        self.plot_tab = PlotTab()
        self.tabs.addTab(self.plot_tab, "Plot IV|CV|TCT vs Voltage")
        
        # Add Volume Normalization Tab vs Fluence
        self.curr_vol_norm_fluence_tab = IVolNormFluenceTab()
        
        # Add Volume Normalization Tab vs Annealing Time
        self.curr_vol_norm_annealing_tab = IVolNormAnnealingTab()
        
        # Parent Tab for Volume Normalization
        self.curr_vol_norm_tab = QTabWidget()
        self.curr_vol_norm_tab.addTab(self.curr_vol_norm_fluence_tab, "vs Fluence")
        self.curr_vol_norm_tab.addTab(self.curr_vol_norm_annealing_tab, "vs Annealing Time")
        self.tabs.addTab(self.curr_vol_norm_tab, "Current Volume Normalization")
        
        # Add Saturation Voltage Tab
        self.saturation_voltage_fit_tab = SaturationVoltageFitTab()

        # Add Saturation Voltage vs Fluence Tab
        self.sat_volt_fluence_tab = SaturationVoltageFluenceTab()

        # Add Saturation Voltage vs Annealing Time Tab
        self.sat_volt_annealing_tab = SaturationVoltageAnnealingTab()

        # Parent Tab for Saturration Voltage
        self.saturation_voltage_tab = QTabWidget()
        self.saturation_voltage_tab.addTab(self.saturation_voltage_fit_tab, "Fit")
        self.saturation_voltage_tab.addTab(self.sat_volt_fluence_tab, "vs Fluence")
        self.saturation_voltage_tab.addTab(self.sat_volt_annealing_tab, "vs Annealing Time")
        self.tabs.addTab(self.saturation_voltage_tab, "Saturation Voltage")
        

        # Add CC (Charge Collection) vs Fluence Tab
        self.CC_fluence_tab = CCFluenceTab()

        # Add CC (Charge Collection) vs Annealing Time Tab
        self.CC_annealing_tab = CCAnnealingTab()

        # Parent Tab for Charge Collection
        self.charge_collection_tab = QTabWidget()
        self.charge_collection_tab.addTab(self.CC_fluence_tab, "vs Fluence")
        self.charge_collection_tab.addTab(self.CC_annealing_tab, "vs Annealing Time")
        self.tabs.addTab(self.charge_collection_tab, "Charge Collection")

        # Add CCE (Charge Collection Efficiency) vs Fluence Tab
        self.CCE_fluence_tab = CCEFluenceTab()

        # Add CCE (Charge Collection) vs Annealing Time Tab
        self.CCE_annealing_tab = CCEAnnealingTab()

        # Parent Tab for Charge Collection Efficiency
        self.charge_collection_efficiency_tab = QTabWidget()
        self.charge_collection_efficiency_tab.addTab(self.CCE_fluence_tab, "vs Fluence")
        self.charge_collection_efficiency_tab.addTab(self.CCE_annealing_tab, "vs Annealing Time")
        self.tabs.addTab(self.charge_collection_efficiency_tab, "Charge Collection Efficiency")
        
        # Add DI vs HF Comparison Tab
        self.di_hf_comparison_tab = DIHFComparisonTab()
        self.tabs.addTab(self.di_hf_comparison_tab, "DI vs HF Comparison")

        # Add Database Tab
        self.database_tab = DatabaseTab(refresh_unique_lists_all_tabs=self.refresh_unique_lists_all_tabs)
        self.tabs.addTab(self.database_tab, "Manage Database")
        
        # Add Annealing Tab
        self.annealing_tab = AnnealingTab()
        self.tabs.addTab(self.annealing_tab, "Annealing")

    def refresh_unique_lists_all_tabs(self):
        self.plot_tab.tab_template.refresh_unique_lists_plot_tab()
        self.curr_vol_norm_fluence_tab.tab_template.refresh_unique_lists_plot_tab()
        self.curr_vol_norm_annealing_tab.tab_template.refresh_unique_lists_plot_tab()
        self.saturation_voltage_fit_tab.refresh_unique_lists_saturation_voltage_fit_tab()
        self.sat_volt_fluence_tab.tab_template.refresh_unique_lists_plot_tab()
        self.CC_fluence_tab.tab_template.refresh_unique_lists_plot_tab()
        self.CCE_fluence_tab.tab_template.refresh_unique_lists_plot_tab()
        self.CC_annealing_tab.tab_template.refresh_unique_lists_plot_tab()
        self.CCE_annealing_tab.tab_template.refresh_unique_lists_plot_tab()
        self.sat_volt_annealing_tab.tab_template.refresh_unique_lists_plot_tab()
        self.database_tab.refresh_unique_lists_database_tab()