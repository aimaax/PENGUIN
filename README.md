# PENGUIN :penguin:  

> **NOTE!!** Google ID and GitLab repo for CERN organization is hidden and the create database function won't work properly in this version. Plotting is still possible with the saved database and data stored in this repo.  

A Python-based environment for GUI-driven analysis for IV, CV, and TCT measurements obtained with [Particulars Setup]() at CERN for CMS HGCAL silicon diodes. Used to plot data for individual diodes, but also to analyse Current Volume Normalization, Saturation Voltage, Charge Collection, and Charge Collection Efficiency.

---

## Table of Contents

- [Installation](#installation)
- [Using saved database from another computer](#using-saved-database-from-another-computer)
- [Running the GUI](#running-the-gui)
- [Creating the Database](#creating-the-database)
- [GUI Overview](#gui-overview)
  - [Plot Electrical Characteristics vs Voltage (Plot IV|CV|TCT vs Voltage)](#plot-electrical-characteristics-vs-voltage-plot-ivcvtct-vs-voltage)
  - [Plot Electrical Characteristics vs Fluence and Annealing Time](#plot-electrical-characteristics-vs-fluence-and-annealing-time)
  - [Extract Saturation Voltage from CV and TCT data](#extract-saturation-voltage-from-cv-and-tct-data)
  - [Plot Double Irradiation (DI & DI SR) vs High Fluence (HF) as function of annealing time](#plot-double-irradiation-di--di-sr-vs-high-fluence-hf-as-function-of-annealing-time)
  - [Manage Database Tab](#manage-database-tab)
  - [Annealing Tab](#annealing-tab)
- [Plot Settings](#plot-settings)
- [Blacklisting Measurements](#blacklisting-measurements)
- [Supported Irradiation Campaigns](#supported-irradiation-campaigns)
- [Code Structure](#code-structure)


---

## Installation

### Prerequisites 

Install `uv`:

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux/Git Bash:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone repo

```
git clonehttps://<username>@github.com/aimaax/penguin.git
cd penguin
```

---

## Using saved database from another computer

GUI only searches for Database/Diodes_Database.pkl so either create new database or copy a previous backup database:

```bash
cp Database/SavedDatabases/DB_DI_DISR_HF_20260216.pkl Database/Diodes_Database.pkl
```

> **Important!** If database was previously created on another system (Windows vs Linux), after you copied the file, then go to "Manage Database" --> "Create Database" then select one campaign at the time and under "Columns to Overwrite" select **file_iv**, **file_cv**, and **file_tct** then press Create Database. (This has to be done once, have patience :>)

---

## Running the GUI

From the **project root** directory (where `start_GUI.py` is located), run:

```bash
uv run start_GUI.py
```

---

## Creating the Database

Before you can plot any data, you must create the sensor database:

1. Navigate to the **Manage Database** tab.
2. Click the **Manage Database** sub-tab.
3. Select the **campaign** you want to import from the campaign dropdown.
4. Choose which **measurement directories** under Data/ to scan (IV_onPCB, CV_onPCB, TCT, IVCV_bare).
5. Press **"Create Database"**.

It scans the selected directories in `Data/` and matches the sensor id and annealing time from the filename to fetch metadata from the corresponding Google Sheets. Saves the database to `Database/Diodes_Database.pkl`.

---

## GUI Overview

Divided into **8 main tabs** containing:

1. Plot IV|CV|TCT vs Voltage
2. Current Volume Noramlization
3. Saturation Voltage
4. Charge Collection
5. Charge Collection Efficiency
6. DI vs HF Comparison
7. Manage Database
8. Annealing

Plots can be saved with Save Plot:

- **Original** = saves exactly as you see it in the GUI
- **16:9** = 16 to 9 ratio with the base_width of 5.12 (full width of 15' laptop screen)

<!-- - **Left side**: Matplotlib plot canvas (resizable)
- **Right side**: A narrow panel (max 300px) with two sub-tabs:
  - **Filter tab**: Campaign, measurement type, sensor ID, annealing time, and other filters specific to the tab
  - **Plot Settings tab**: Visual customization (axis scales, labels, fonts, markers, legend, colors, etc.)

### Typical Workflow

1. Select your desired filters in the right-side panel (campaign, sensors, annealing times, etc.)
2. Click **"Display Plot"** to generate the plot
3. Adjust visual settings in the **"Plot Settings"** sub-tab
4. Click **"Display Plot"** again to apply visual changes
5. Optionally **save** the plot as PDF -->

---

### Plot Electrical Characteristics vs Voltage (Plot IV|CV|TCT vs Voltage)

Displays electrical characteristics as a function of applied voltage. Typically used to check if current measurement cycle at X annealing time matches the expectation of the previous measurement at Y annealing time. Typically procedure:

1. Update database --> Follow [Creating the Database](#creating-the-database) `Note: TCT factor will be default 1 if not filled out in the corresponding Google Sheet. If creating either way, make sure to overwrite this later when filled in by using 'Columns to Overwrite' = TCT corr`
2. Plot data for each temperature. Can use zoom function under `Plot Settings` --> left click `Zoom` --> click and drag on Canvas

Plot data, make sure that you have path columns are created under your system [Windows vs Linux](#using-saved-database-from-another-computer):

- **Campaign**
- **Measurement**: IV, CV or TCT
- **Measurement Type** (onPCB = measured at [Particulars Setup](https://gitlab.cern.ch/CLICdp/HGCAL/particulars_setup), bare = measured at IVCV probe station),
- **Annealing Temperature**
- **Sensor ID**
- **Annealing Time**
- **Include uncertainty** = plot with uncertainty bars, e.g. 5% for Charge Collection

---

### Plot Electrical Characteristics vs Fluence and Annealing Time

Tabs: `Current Volume Normalization`, `Saturation Voltage`, `Charge Collection`, and `Charge Collection Efficiency` contains two sub-tabs:

#### vs Fluence

Plots electrical characteristic as a function of 1MeV neutron equivalent fluence.

#### vs Annealing Time

Plots electrical characteristic as a function of annealing time for the selected sensors.

**Additional filters:**

- **Thickness**: Select sensor thicknesses (120, 200, 300 µm)
- **Voltage**: Voltage to extract the values from 0-900V, including saturation voltage extracted from both CV and TCT data.

---

### Extract Saturation Voltage from CV and TCT data

Extraction of saturation voltage from CV and TCT data can be done under `Saturation Voltage` --> `Fit`,

**How to use the fit tab:**

1. Select a **campaign**, **measurement type**, **annealing temperature**, **sensor ID**, and **annealing time**
2. Default fit from `CV`. To fit from `TCT` data, click in the checkbox `Fit from TCT | CC vs V`
3. **Annealing Time** displays green checkbox if all diodes for the specific sensor id, campaign and annealing temperature are done, otherwise a red X. To skip looking through already fit diodes, check `Only iterate through non analysed annealing times`
4. Click **Interactive Fit Saturation Voltage** to load first diode
5. First tries an **automatic fit** using a curvature-based algorithm (@GUI.SaturationVoltage.SaturationVoltageFitTab.py -> automatic_fit_saturation_voltage -> @Utils.saturation_voltage_fit_helper.py -> find_saturation_voltage_from_curvature_fit):
6. If the automatic fit is unsatisfactory, use the **manual fit modes** by pressing `1`:
   - **Manual Fit Mode**: Click on the plot to define the lower and upper fit regions by placing interactive vertical lines. Move lower lines by `left click` and `right click`. Move upper lines by `SHIFT` + `left click` and `right click`.
   - **Endcap Assumption**: Remove lines for upper fit and uses end capacitance assumption for the upper fit (values extracted from mean value of all diodes with equal thicknesses for 120um, 200um, and 300um)
   - **Manual Upper Fit Mode**: Manually align upper fit line by moving it with the left click and rotating it with keyboard controls `A` & `D`
7. When satisfied with the selected region, press `2` to fit.
8. If saturation voltage is not possible to extract, press `3` to skip (stores 0 in the database).
9. If you are happy with the **automatic fit** or **manual fit**, press `SPACE` to save the saturation voltage, uncertainties, and fit regions to the database.

**Fit result colors:**

- Orange lines/points: Not yet saved to database = current analysis
- Green lines/points: Stored in database = already analysed

---

### Plot Double Irradiation (DI & DI SR) vs High Fluence (HF) as function of annealing time

Compares **alpha, saturation voltage, CC, and CCE** as a function of annealing time between Double Irradiation (DI) and High Fluence (HF) irradiation campaigns. Also possible to include Low Fluence Campaign.

**Unique filters:**

- **Plot only second round of DI**: Restrict to the second irradiation round
- **DI FR: Sensor ID**: Select first-round DI sensors
- **DI SR: Sensor ID**: Select second-round DI sensors (auto-populated from FR selection)
- **HF: Sensor ID**: Select HF comparison sensors (auto-matched by fluence and thickness from DI SR)
- **LF: Sensor ID**: Select Low Fluence comparison sensors
- **HF points after last DI annealing step**: Number of HF annealing points to include after the last DI step
- **Type of Plot**: Choose between alpha, saturation voltage, CC, or CCE

**Special options:**

- **Split x-axis**: Breaks the x-axis to show DI campaign (1/4 of fluence) in the left plot and DI SR vs HF in the right plot. Annealing time axis reset. If unchecked, plot showed with one axis.
- **Plot ratio DI vs HF**: Plot DI SR / HF ratio at all possible annealing times. If HF point is not equal to exact annealing time point of DI SR, then interpolate with the two clostest points.
- **Plot average ratio DI vs HF**: Shows averaged compressed ratio plot with ratio in the y-axis and the unique thickness and fluence combination on the x-axis. Here choose all temperatures.
- **Add 1/4 ann time from DI FR to SR**: Add 1/4 of the maximum annealing time from the DI first round (1/4) to the DI SR.

---

### Manage Database Tab

#### Display Database

Shows the full database as an interactive table. You can:

- Select which columns to display
- Edit individual cell values directly in the table **delete individual row** by setting `thickness value to 0`
- Filter database from Campaigns, Measurement Type, Thickness, Annealing Temperatures, Annealing Time.

#### Create Database

The primary database creation interface (see [Creating the Database](#creating-the-database)).

#### Export/Import Saturation Voltage

Default exporting all related saturation voltage fit columns of the selected `Campaign`, `Sensor ID`, and `Annealing Time` combination. 

- **Export**: Save saturation voltage fit results to a CSV file in `Database/SaturationVoltageData/`
- **Import**: Load previously exported saturation voltage data back into the database

**Options**:
- **Export CV values only**: only saturation voltage, fit regions, uncertainties regarding the `CV` fit. 
- **Export TCT values only**: only saturation voltage, fit regions, uncertainties regarding the `TCT` fit.
---

### Annealing Tab

Using Arrhenius scaling to calculated equivalent annealing time from logged temperature (1 data recording per second). 

**How to use:**

1. Click **"Browse"** to select an annealing temperature log file (from `Data/Annealing_Files/` or any other place)
2. The tool automatically detects the oven temperature from the filename
3. Click **"Plot Annealing Temperature vs Time"** to display the temperature profile
4. The equivalent annealing time at target temperature is displayed for EPI and FZ diodes. 

---

## Plot Settings

Every plotting tab includes a **"Plot Settings"** sub-tab on the right panel with the following controls:

| Setting                    | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| **Log X/Y axis**           | Toggle logarithmic scaling                                               |
| **X/Y axis limits**        | Set custom min/max axis bounds                                           |
| **Custom X/Y labels**      | Override default axis labels                                             |
| **Axis Font Size**         | Changes axis label font size                                          |
| **Text Box**               | Change font size for custom text box bottom right corner                                            |
| **Enable Custom Text**     | Add a custom text box annotation to the plot                             |
| **Border Width**           | Change axes border thickness                                         |
| **Tick Label Size**        | Change tick number font size                                         |
| **Major/Minor Tick Size**  | Change tick mark lengths                                            |
| **Major/Minor Tick Width** | Change tick mark widths                                             |
| **Marker Size**            | Change marker size for data points                                      |
| **Line Width**             | Change line widths                                     |
| **Legend Size**            | Change legend font and marker scale                    |
| **Color Palette**          | Choose between custom colors, per-sensor colors, or matplotlib colormaps |
| **Skip Colors/Markers**    | Skip N colors/markers from the beginning of the palette                  |
| **Enable Title**           | Toggle plot title with optional custom text                              |
| **Enable Legend**          | Toggle legend with placement options (best, upper right, etc.)           |

After changing any setting, click **"Display Plot"** to apply the changes. The methods `display_plot` reads all of these settings and plot them accordingly. 

---

## Blacklisting Measurements

To exclude specific measurements from all plots and filtering, edit `Blacklisted_measurements.csv` in the project root:

```
Sensor,Type,Annealing_Time
HPK_SENSOR_NAME,bare,noadd
HPK_SENSOR_NAME,onPCB,10min
HPK_SENSOR_NAME,all,
```

| Field            | Values                                                                       |
| ---------------- | ---------------------------------------------------------------------------- |
| `Sensor`         | Any valid sensor name from the database                                      |
| `Type`           | `bare`, `onPCB`, or `all` (blacklists all measurement types for that sensor) |
| `Annealing_Time` | `noadd`, `10min`, `10days`, etc. (leave empty when using `all`)              |

---

## Supported Irradiation Campaigns

| Campaign ID                 | Display Name | Irradiation Particle |
| --------------------------- | ------------ | -------- |
| `HighFluenceIrrNeutron2023` | HF           | Neutrons |
| `ProtonIrr2024`             | Proton       | Protons  |
| `LowFluenceIrrNeutron2025`  | LF           | Neutrons |
| `DoubleIrrNeutron2025`      | DI           | Neutrons |
| `DoubleIrrSRNeutron2025`    | DI SR        | Neutrons |

Each campaign has linked Google Sheets for diode metadata and TCT factor from measuring reference diode at the end of the day and are fetched during database creation.

---

## Code Structure

For a detailed description of the code structure and data flow, see [CODESTRUCTURE.md](CODESTRUCTURE.md).
