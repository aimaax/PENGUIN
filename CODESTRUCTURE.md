# Architecture

This document describes the code structure, module responsibilities, data flow, and design patterns used for this project.

---

## Table of Contents

- [Directory Structure](#directory-structure)
- [High-Level Architecture](#high-level-architecture)
- [Entry Point](#entry-point)
- [GUI Layer](#gui-layer)
  - [MainWindow](#mainwindow)
  - [TabTemplate (Reusable Tab Base)](#tabtemplate-reusable-tab-base)
  - [SettingsPlot](#settingsplot)
  - [Plotting Tabs](#plotting-tabs)
  - [Custom Widgets](#custom-widgets)
- [Configuration Layer](#configuration-layer)
- [Data Layer](#data-layer)
  - [Database Schema](#database-schema)
  - [Data Files](#data-files)
- [Key Design Patterns](#key-design-patterns)
- [Data Flow Diagrams](#data-flow-diagrams)

---

## Directory Structure

```
particulars-analysis/
│
├── start_GUI.py                    # Application entry point
├── config.py                       # Global configuration and constants
├── tab_config.py                   # Per-tab filter/widget configuration
├── requirements.txt                # Python dependencies
├── Blacklisted_measurements.csv    # Sensor blacklist file
├── README.md                       # User documentation
├── CODESTRUCTURE.md                # This file
│
├── GUI/                            # All GUI modules
│   ├── MainWindow.py               # Main application window with tab container
│   ├── TabTemplate.py              # Reusable base widget for plotting tabs
│   ├── SettingsPlot.py             # Shared plot settings widget
│   ├── PlotTab.py                  # IV/CV/TCT vs Voltage tab
│   ├── DatabaseTab.py              # Database management parent tab
│   ├── AnnealingTab.py             # Annealing temperature profile tab
│   ├── DIHFComparisonTab.py        # DI vs HF comparison tab
│   │
│   ├── CurrentVolumeNorm/          # Current volume normalization tabs
│   │   ├── IVolNormFluenceTab.py   #   vs Fluence
│   │   └── IVolNormAnnealingTab.py #   vs Annealing Time
│   │
│   ├── SaturationVoltage/          # Saturation voltage tabs
│   │   ├── SaturationVoltageFitTab.py       # Interactive fit tool
│   │   ├── SaturationVoltageFluenceTab.py   # vs Fluence
│   │   └── SaturationVoltageAnnealingTab.py # vs Annealing Time
│   │
│   ├── ChargeCollection/           # Charge collection tabs
│   │   ├── CCFluenceTab.py         #   vs Fluence
│   │   └── CCAnnealingTab.py       #   vs Annealing Time
│   │
│   ├── ChargeCollectionEfficiency/  # Charge collection efficiency tabs
│   │   ├── CCEFluenceTab.py        #   vs Fluence
│   │   └── CCEAnnealingTab.py      #   vs Annealing Time
│   │
│   └── ManageDatabase/             # Database management sub-tabs
│       ├── CreateDatabaseTab.py    # Database creation from data files
│       ├── DisplayDatabaseTab.py   # Interactive database table viewer
│       └── ExportImportSaturationVoltageTab.py  # Export/import sat. voltage
│
├── Utils/                          # This is where all helper functions are located
│   ├── plot_helper.py              # IV/CV/TCT plotting functions
│   ├── plot_electrical_characteristic_vs_fluence.py   # vs Fluence plots
│   ├── plot_electrical_characteristic_vs_annealing.py # vs Annealing plots
│   ├── di_comparison_plot.py       # DI vs HF comparison plotting
│   ├── dataframe_helper.py         # DataFrame construction from raw files
│   ├── create_database_helper.py   # Database creation and update logic
│   ├── saturation_voltage_fit_helper.py  # Curvature-based fit algorithms
│   ├── annealing_helper.py         # Arrhenius-based annealing calculations
│   ├── conversion_helper.py        # Unit conversions and calculations
│   ├── constants.py                # Physical constants
│   ├── CheckableComboBox.py        # Multi-select combo box widget
│   └── DoubleSlider.py             # Float-valued slider widget
│
├── Data/                           # Raw measurement data (per campaign)
│   ├── HighFluenceIrrNeutron2023/
│   ├── ProtonIrr2024/
│   ├── LowFluenceIrrNeutron2025/
│   ├── DoubleIrrNeutron2025/
│   ├── Annealing_Files/
│   ├── TemperatureFiles/
│   └── 300um_UIRAD/
│
├── Database/                       # Generated database files
│   ├── Diodes_Database.pkl         # Main pickle database (GUI is using this database)
│   └── SaturationVoltageData/      # Exported saturation voltage CSVs
│
└── SavedPlots/                     # Saved plot output directories
    └── ...

```

---

## High-Level Architecture

The project follows the below structure:

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                        Entry Point                              │
  │                       start_GUI.py                              │
  ├─────────────────────────────────────────────────────────────────┤
  │                         GUI Layer                               │
  │  ┌────────────────────────────────────────────────────────────┐ │
  │  │                    MainWindow                              │ │
  │  │  ┌───────────────────────────────────────────┬──────────┐  │ │
  │  │  │   Plot/CurrVolNorm/SatVolt/CC/CCE/DIvsHF  │  DB Tab  │  │ │
  │  │  │                                           │ Annealing│  │ │
  │  │  └────┬──────────┬──────────┬──────────┬─────┴──────────┘  │ │
  │  │       │          │          │          │                   │ │
  │  │  ┌────▼──────────▼──────────▼──────────▼──────┐            │ │
  │  │  │         TabTemplate + SettingsPlot         │            │ │
  │  │  │   (Shared filter UI + plot display logic)  │            │ │
  │  │  └────────────────────────────────────────────┘            │ │
  │  └────────────────────────────────────────────────────────────┘ │
  ├─────────────────────────────────────────────────────────────────┤
  │                    Configuration Layer                          │
  │config.py (all constant paths etc.) + tab_config.py (TabTemplate)│
  ├─────────────────────────────────────────────────────────────────┤
  │                      Helper Layers                              │
  │  ┌───────────┐  ┌─────────────────┐  ┌─────────────────┐   ...  │
  │  │  Plotting │  │ Data Processing │  │  Database       │   ...  │
  │  │  Helpers  │  │ Helpers         │  │  Helpers        │   ...  │
  │  └───────────┘  └─────────────────┘  └─────────────────┘        │
  ├─────────────────────────────────────────────────────────────────┤
  │                        Data Layer                               │
  │        Pickle Database  ←→  Raw CSV/IV/CV/TCT Files             │
  │                         ←→  Google Sheets                       │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Entry Point

```bash
start_GUI.py
```

Starting point of the GUI:

- Creates the `QApplication` instance
- Instantiates `MainWindow`
- Enters the Qt event loop

---

## GUI Layer

### MainWindow

**File**: `GUI/MainWindow.py`  
**Class**: `MainWindow(QMainWindow)`

The root window that organizes all tabs into a `QTabWidget`. Responsible for:

- Instantiating all tab widgets
- For nested tab structures
- Providing `refresh_unique_lists_all_tabs()` to cascade database updates to every tab after database creation/modification

**Tab hierarchy from MainWindow:**

```
QTabWidget (main)
├── "Plot IV|CV|TCT vs Voltage"          → PlotTab
├── "Current Volume Normalization"       → QTabWidget
│   ├── "vs Fluence"                         → IVolNormFluenceTab
│   └── "vs Annealing Time"                  → IVolNormAnnealingTab
├── "Saturation Voltage"                 → QTabWidget
│   ├── "Fit"                                → SaturationVoltageFitTab
│   ├── "vs Fluence"                         → SaturationVoltageFluenceTab
│   └── "vs Annealing Time"                  → SaturationVoltageAnnealingTab
├── "Charge Collection"                  → QTabWidget
│   ├── "vs Fluence"                         → CCFluenceTab
│   └── "vs Annealing Time"                  → CCAnnealingTab
├── "Charge Collection Efficiency"       → QTabWidget
│   ├── "vs Fluence"                         → CCEFluenceTab
│   └── "vs Annealing Time"                  → CCEAnnealingTab
├── "DI vs HF Comparison"               → DIHFComparisonTab
├── "Manage Database"                    → DatabaseTab
└── "Annealing"                          → AnnealingTab
```

---

### TabTemplate (Reusable Tab Base)

**File**: `GUI/TabTemplate.py`  
**Class**: `TabTemplate(QWidget)`

The core reusable component used by most plotting tabs. It provides:

1. **Layout management**: Horizontal split with canvas (left) and input panel (right)
2. **Dynamic widget generation**: Reads a `tab_config` dictionary to decide which filter widgets to create (campaign, sensor ID, thickness, voltage, etc.)
3. **Database loading**: Reads `Diodes_Database.pkl` and extracts unique values for filter dropdowns
4. **Cascading filters**: When a filter changes (e.g., campaign), downstream filters (annealing temp → sensor ID → annealing time) are automatically updated
5. **Plot display**: Applies all visual settings from `SettingsPlot` and redraws the canvas
6. **Plot saving**: Exports to PDF at 600 DPI with configurable aspect ratios

**Key methods:**

| Method                            | Description                                                  |
| --------------------------------- | ------------------------------------------------------------ |
| `load_database()`                 | Loads the pickle database and extracts unique filter values  |
| `get_fiter_mask()`                | Creates a pandas boolean mask from current filter selections |
| `display_plot()`                  | Applies all SettingsPlot parameters and redraws the canvas   |
| `save_plot()`                     | Saves the current figure as PDF with optional aspect ratio   |
| `update_unique_*()`               | Cascade methods that update dependent filter dropdowns       |
| `refresh_unique_lists_plot_tab()` | Reloads database and refreshes all filter dropdowns          |

**Filter cascade chain:**

```
Campaign → Measurement Type → Annealing Temp → Sensor ID → Annealing Time
```

When a parent filter changes, all downstream filters are re-populated with valid values.

---

### SettingsPlot

**File**: `GUI/SettingsPlot.py`  
**Class**: `SettingsPlot(QWidget)`

Widget used as a sub-tab within every plotting `TabTemplate`. Provides interactive sliders and controls for visual plot customization.

Default values are loaded from `PLOT_STYLE` in `config.py`.

---

### Plotting Tabs

Each plotting tab follows the same pattern:

1. Creates a `TabTemplate` instance with a specific `tab_config` dictionary defined in `tab_config.py` and a `plot_function` callback
2. Implements the `plot_function` that:
   - Reads filter selections from `self.tab_template`
   - Loads/filters the database
   - Calls the appropriate plotting utility function
   - Calls `self.tab_template.display_plot()` to plot data

#### SaturationVoltageFitTab (Special Case)

**File**: `GUI/SaturationVoltage/SaturationVoltageFitTab.py`  
**Class**: `SaturationVoltageFitTab(QWidget)`

Does **not** use `TabTemplate`. Instead, it implements its own layout with:

**Key methods:**

| Method                                    | Description                                             |
| ----------------------------------------- | ------------------------------------------------------- |
| `interactive_saturation_voltage_fit()`    | Main entry: loads data and starts the fit workflow      |
| `automatic_fit_saturation_voltage()`      | Runs curvature-based automatic fit                      |
| `manual_fit_mode()`                       | Activates interactive line placement for manual fitting |
| `endcap_assumption_fit_mode()`            | Uses theoretical 1/C² endpoint for upper region         |
| `manual_upper_fit_mode()`                 | Allows manual rotation of the upper fit line            |
| `save_and_go_to_next_sensor()`            | Persists fit results to the database and advances       |
| `next_previous_sensor()`                  | Navigates through the sensor list                       |
| `plot_saturation_voltage_single_sensor()` | Renders a single sensor's curve with fit overlays       |

---

### Custom Widgets

#### CheckableComboBox

**File**: `Utils/CheckableComboBox.py`  
**Class**: `CheckableComboBox(QComboBox)`

A multi-select dropdown with checkboxes. Used extensively for filter selections (campaigns, sensors, annealing times, etc.).


#### DoubleSlider

**File**: `Utils/DoubleSlider.py`  
**Class**: `DoubleSlider(QSlider)`

A `QSlider` subclass that supports floating-point values. Used by `SettingsPlot` for all numeric sliders.


---

## Configuration Layer

### `config.py`

The central configuration file. Defines:

**Plot styling:**

- `RC_PLOT_STYLE` -- matplotlib rcParams for consistent styling
- `PLOT_STYLE` -- Custom style dict used by `SettingsPlot` for default slider values
- `CUSTOM_COLORS` -- Colors used for the plots
- `MATPLOTLIB_COLORS` -- Available matplotlib colormaps (viridis, plasma, inferno, magma, cividis)
- `MARKERS`, `LINESTYLES`, `FILLSTYLE`, `MARKERSIZE`, `LEGEND_SIZE`

**Paths:**

- `ROOT_PATH_REPO` -- Auto-detected repository root
- `DEFAULT_DIR_*` -- Default directories for data, database, saved plots
- `DEFAULT_DATABASE_PATH` -- Path to the main pickle database (Diodes_Database.pkl)

**Database schema:**

- `DATABASE_COLUMNS` -- Ordered list of all database column names
- `DATABASE_INDEX_LEVEL` -- Multi-index levels (sensor_id, campaign, thickness, fluence, temperature, CVF, annealing_time)
- `COLUMN_DTYPES` -- Type mapping for each column

**Campaign configuration:**

- `CAMPAIGNS` -- List of available campaign IDs
- `CAMPAIGN_TO_SENSOR_OVERVIEW_GOOGLE_ID_GID` -- Google Sheets IDs for sensor overview data
- `CAMPAIGN_TO_MEAS_LOG_ONPCB_GOOGLE_ID_GID` -- Google Sheets IDs for measurement logs
- `CORRECTED_ANNEALING_TIMES_GOOGLE_ID_GID` -- Google Sheets IDs for corrected annealing times
- `CAMPAIGN_TO_DISPLAY_NAME` -- Short display names for campaigns
- `CAMPAIGN_TO_PARTICLE_DICT` -- Particle type per campaign

**Physics constants and thresholds:**

- `FULLCHARGE_CC_DICT` -- Full charge values per thickness (fC)
- `END_INV_CAPACITANCE_2_ASSUMPTION` -- 1/C² endpoint values per thickness
- Error constants for various fit methods (endcap, plateau, manual upper line, TCT)
- `N_HIGHEST_CURVATURE_POINTS` -- Points used for curvature-based fitting

**Helper function:**

- `get_thickness_color(thickness)` -- Returns a color for a given thickness value

### `tab_config.py`

Defines dictionaries for each tab specifying which filter widgets to show. Each dictionary maps widget names to booleans.

## Data Layer

### Database Schema

The main database is stored as a pickled pandas DataFrame at `Database/Diodes_Database.pkl`.

**Multi-Index levels**:

| Level            | Type    | Example                          |
| ---------------- | ------- | -------------------------------- |
| `sensor_id`      | str     | `"100123_UL_2e15"`             |
| `campaign`       | str     | `"HighFluenceIrrNeutron2023"`    |
| `thickness`      | int64   | `120`, `200`, `300`              |
| `fluence`        | float64 | `1.5e15`                         |
| `temperature`    | int64   | `-20`                            |
| `CVF`            | int64   | `2000`                           |
| `annealing_time` | str     | `"noadd"`, `"10min"`, `"10days"` |

**Data columns:**

| Column                     | Type    | Description                          |
| -------------------------- | ------- | ------------------------------------ |
| `annealing_temp`           | float64 | Oven temperature (°C)                |
| `type`                     | str     | `"onPCB"` or `"bare"`                |
| `file_IV`                  | str     | Path to IV measurement file          |
| `file_CV`                  | str     | Path to CV measurement file          |
| `open_corr`                | float64 | Open CV correction factor            |
| `file_TCT`                 | str     | Path to TCT measurement file         |
| `TCT_corr`                 | float64 | TCT correction factor                |
| `sat_V_CV`                 | float64 | Saturation voltage from CV fit       |
| `sat_V_err_down_CV`        | float64 | CV saturation voltage lower error    |
| `sat_V_err_up_CV`          | float64 | CV saturation voltage upper error    |
| `low_fit_start_CV`         | float64 | CV low region fit start voltage      |
| `low_fit_stop_CV`          | float64 | CV low region fit stop voltage       |
| `high_fit_start_CV`        | float64 | CV high region fit start voltage     |
| `high_fit_stop_CV`         | float64 | CV high region fit stop voltage      |
| `upper_fit_params_CV`      | object  | CV upper fit line parameters         |
| `sat_V_TCT`                | float64 | Saturation voltage from TCT fit      |
| `sat_V_err_down_TCT`       | float64 | TCT saturation voltage lower error   |
| `sat_V_err_up_TCT`         | float64 | TCT saturation voltage upper error   |
| `low_fit_start_TCT`        | float64 | TCT low region fit start voltage     |
| `low_fit_stop_TCT`         | float64 | TCT low region fit stop voltage      |
| `high_fit_start_TCT`       | float64 | TCT high region fit start voltage    |
| `high_fit_stop_TCT`        | float64 | TCT high region fit stop voltage     |
| `upper_fit_params_TCT`     | object  | TCT upper fit line parameters        |
| `corrected_annealing_time` | str     | Correct annealing time |
| `corr_ann_time_err_up`     | str     | Corrected annealing time upper error |
| `corr_ann_time_err_down`   | str     | Corrected annealing time lower error |
| `Blacklisted`              | bool    | Whether the entry is blacklisted     |

### Data Files

Raw measurement data is organized under `Data/` by campaign:

```
Data/{CampaignName}/
├── IV_onPCB/          # On-PCB IV measurement CSVs
├── CV_onPCB/          # On-PCB CV measurement CSVs
├── TCT/               # TCT measurement CSVs
└── IVCV_bare/         # Bare IV/CV measurement files
```
---

---

## Key Design Patterns

### 1. Configuration-Driven Widget Generation

`TabTemplate` reads `tab_config` dictionaries to decide which widgets to create at runtime. This avoids duplicating widget setup code across 10+ tabs. Adding a new filter to a tab requires only adding a key to its config dictionary.

### 2. Callback Chain for Cascading Filters

`CheckableComboBox` supports external callbacks via `add_external_callback()`. When a selection changes, it triggers registered callbacks that update downstream filters:

```
Campaign changed
  → update_unique_annealing_temp()
    → update_unique_sensor_id()
      → update_unique_annealing_time()
```

### 3. Separation of Plot Logic from UI

All heavy plotting logic resides in `Utils/` modules. GUI tab classes only handle:

- Reading filter values from widgets
- Calling the appropriate utility function
- Assigning the returned figure/axes to the template
- Triggering `display_plot()`

### 4. Centralized Plot Styling

`SettingsPlot` applies styling uniformly to all plots through `TabTemplate.display_plot()`. This ensures consistent visual appearance across all tabs while allowing per-plot customization.

### 5. Database as Single Source of Truth

All tabs read from the same pickle database. Database modifications (creation, saturation voltage updates) trigger `refresh_unique_lists_all_tabs()` which cascades to every tab, ensuring data consistency.

---

## Data Flow Diagrams


### Plotting Flow (Standard Tabs)

```
User selects filters → Clicks "Display Plot"
         │
         ▼
Tab.plot_function()
  ├── Read filter values from TabTemplate widgets
  ├── Load and filter database (pandas)
  ├── Call Utils plotting function
  │     └── Returns (fig, ax)
  ├── Assign fig/ax to TabTemplate
  └── TabTemplate.display_plot()
        ├── Apply SettingsPlot parameters
        ├── Refresh canvas widget
        └── Draw
```

