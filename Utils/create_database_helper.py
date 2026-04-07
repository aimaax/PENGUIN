import pandas as pd
import os
import numpy as np
import math
from datetime import datetime
from config import (
    DATABASE_COLUMNS, 
    DATABASE_INDEX_LEVEL, 
    VALID_HALFMOONS, 
    COLUMN_DTYPES, 
    ROOT_PATH_REPO, 
    CAMPAIGN_TO_SENSOR_OVERVIEW_GOOGLE_ID_GID, 
    CAMPAIGN_TO_MEAS_LOG_ONPCB_GOOGLE_ID_GID, 
    CORRECTED_ANNEALING_TIMES_GOOGLE_ID_GID
)

def process_annealing_temp(value):
    if value == "RT":
        return 20.0
    elif pd.isna(value):  # Check if the value is NaN
        return None
    else:
        value_str = str(value)
        # Check if the value contains any letters
        if any(c.isalpha() for c in value_str):
            # Extract digits from the value (e.g., "40C" → "40")
            digits = ''.join(filter(str.isdigit, value_str))
            if digits == "0":
                digits = "5"
            return float(digits) if digits else None
        else:
            return float(value_str)
        
def sort_annealing_time(values, list = False):
    def sort_key(annealing_time):
        if annealing_time == "noadd":
            return (0, 0)  # top priority
        elif "min" in annealing_time:
            return (1, int(annealing_time.replace("min", "")))  # second, sort by minutes
        elif "h" in annealing_time:
            return (2, int(annealing_time.replace("h", "")))  # third, sort by hours
        elif "days" in annealing_time:
            return (3, int(annealing_time.replace("days", "")))  # fourth, sort by days
        else:
            return (4, annealing_time)  # unknowns last

    return sorted(values, key=sort_key)

def annealing_sort_key(annealing_time):
    """ Sort annealing time from database """
    if annealing_time == "noadd":
        return (0, 0)
    elif "min" in annealing_time:
        return (1, int(annealing_time.replace("min", "")))
    elif "h" in annealing_time:
        return (2, int(annealing_time.replace("h", "")))
    elif "days" in annealing_time:
        return (3, int(annealing_time.replace("days", "")))
    else:
        return (4, annealing_time)


def extract_correction_factor(text):
    # Split the text into words
    words = str(text).split()
    if "," in words[-1]:
        words = str(text).split(",")
    
    # Look for a float value between 0.5 and 1.5
    for word in words:
        try:
            value = float(word.strip('.,'))  # Remove potential trailing periods or commas
            if 0.5 <= value <= 1.5:
                return value
        except ValueError:
            continue
    return 1.0

def check_file_exist_in_database(df, sensor_id, measurement_dir, annealing_time, type):
    df_reset = df.reset_index()
    mask = (df_reset['sensor_id'] == sensor_id) & (df_reset['annealing_time'] == annealing_time) & (df_reset["type"] == type)
        # Check if any rows match the mask
    if not mask.any():
        if measurement_dir == "IVCV_bare":
            return None
        elif measurement_dir in ["IV_onPCB", "CV_onPCB", "TCT"]:
            return None, None
    if measurement_dir == "IVCV_bare":
        file_TCT = df_reset.loc[mask, 'file_TCT']
        return file_TCT
    elif measurement_dir == "IV_onPCB":
        file_CV = df_reset.loc[mask, 'file_CV']
        file_TCT = df_reset.loc[mask, 'file_TCT']
        return file_CV, file_TCT
    elif measurement_dir == "CV_onPCB":
        file_IV = df_reset.loc[mask, 'file_IV']
        file_TCT = df_reset.loc[mask, 'file_TCT']
        return file_IV, file_TCT
    elif measurement_dir == "TCT":
        file_IV = df_reset.loc[mask, 'file_IV']
        file_CV = df_reset.loc[mask, 'file_CV']
        return file_IV, file_CV
    
def extract_file_info(filename, measurement_dir):
    """
    Extract sensor ID, and halfmoon from filename.
    Returns tuple of (sensor_id, halfmoon) or (None, None) if invalid
    """
    try:
        filename = filename.split(".")[0]
        parts = filename.split('_')

        if measurement_dir == "TCT":
            annealing_time = parts[-1]
        elif measurement_dir in ["IV_onPCB", "CV_onPCB"]:
            annealing_time = parts[-2]
        
        # Work backwards through the parts to find the valid halfmoon
        for i in range(len(parts)-1, -1, -1):
            if parts[i] in VALID_HALFMOONS:
                halfmoon = parts[i]
                sensor_id = '_'.join(parts[:i+1])
                return sensor_id, halfmoon, annealing_time
        
        return None, None, None  # Return None for all values if no valid pattern found
    except:
        return None, None, None

def standardize_annealing_time(annealing_time):
    """
    Standardize annealing time format to end with min, h, or days
    """
    if annealing_time == "no add":
        return "noadd"
    elif annealing_time == "noadd":
        return "noadd"
    else:
        try:
            # Remove any trailing periods or spaces
            annealing_time = annealing_time.strip().strip('.')

            # Convert the input to string and lowercase for easier processing
            time_str = str(annealing_time).lower()
            
            # Extract numeric value from string
            numeric_time = float(''.join(filter(lambda x: x.isdigit() or x == '.', time_str)))
            
            # Round to nearest integer
            rounded_time = round(numeric_time)
            
            # Convert 'd' to 'days'
            if 'd' in annealing_time.lower():
                return f"{rounded_time}days"
            
            # Handle minutes (min)
            elif 'min' in annealing_time.lower():
                return f"{rounded_time}min"
            
            # Handle hours (h)
            elif 'h' in annealing_time.lower():
                return f"{rounded_time}h"
        except:
            return None


def update_sensor_database(df_path, campaign=None, root_path_data=None, measurement_dir=None, 
                           annealing_time=None, type=None, open_corr=None, overwrite_columns=None):
    
    if overwrite_columns == ["Blacklisted"]:
        df = pd.read_pickle(df_path)

        # Reset all values to False 
        df['Blacklisted'] = False
        
        # Read in Blacklisted_measurements.csv (columns: sensor_id, type, annealing_time)
        df_blacklisted = pd.read_csv(os.path.join(ROOT_PATH_REPO, "Blacklisted_measurements.csv"))

        # Go through the blacklisted measurements and set the matching sensor_id,type,annealing_time mask to True
        for _, row in df_blacklisted.iterrows():
            if row["Annealing_Time"] == "all":
                mask = (
                    (df.index.get_level_values('sensor_id') == row['Sensor']) &
                    (df['type'] == row['Type'])
                )
            else:
                mask = (
                    (df.index.get_level_values('sensor_id') == row['Sensor']) &
                    (df['type'] == row['Type']) &
                    (df.index.get_level_values('annealing_time') == row['Annealing_Time'])
                )
            df.loc[mask, 'Blacklisted'] = True

        df.to_pickle(df_path)
        return df

    google_sheet_sensor_overview_id = CAMPAIGN_TO_SENSOR_OVERVIEW_GOOGLE_ID_GID[campaign][0]
    google_sheet_sensor_overview_gid = CAMPAIGN_TO_SENSOR_OVERVIEW_GOOGLE_ID_GID[campaign][1]
    
    corrected_annealing_times_id = CORRECTED_ANNEALING_TIMES_GOOGLE_ID_GID[campaign][0]
    corrected_annealing_times_gid = CORRECTED_ANNEALING_TIMES_GOOGLE_ID_GID[campaign][1]

    if campaign == "HighFluenceIrrNeutron2023":
        google_sheet_sensor_overview_df = pd.read_csv(f'https://docs.google.com/spreadsheets/d/{google_sheet_sensor_overview_id}/export?format=csv&gid={google_sheet_sensor_overview_gid}',
                            skiprows=1,
                            header=0)
    else:
        google_sheet_sensor_overview_df = pd.read_csv(f'https://docs.google.com/spreadsheets/d/{google_sheet_sensor_overview_id}/export?format=csv&gid={google_sheet_sensor_overview_gid}')
    
    google_sheet_meas_log_onPCB_id = CAMPAIGN_TO_MEAS_LOG_ONPCB_GOOGLE_ID_GID[campaign][0]
    google_sheet_meas_log_onPCB_gid = CAMPAIGN_TO_MEAS_LOG_ONPCB_GOOGLE_ID_GID[campaign][1]

    google_sheet_meas_log_onPCB_df = pd.read_csv(f'https://docs.google.com/spreadsheets/d/{google_sheet_meas_log_onPCB_id}/export?format=csv&gid={google_sheet_meas_log_onPCB_gid}')

    corrected_annealing_times_df = pd.read_csv(f'https://docs.google.com/spreadsheets/d/{corrected_annealing_times_id}/export?format=csv&gid={corrected_annealing_times_gid}')

    sensor_id_to_annealing_temp_dict = {}
    sensor_id_to_thickness_dict = {}
    sensor_id_to_fluence_dict = {}
    for _, row in google_sheet_sensor_overview_df.iterrows():
        row_sensor_id = row["Sensor"]
        row_annealing_temperature = process_annealing_temp(row["Annealing temperature"])
        sensor_id_to_annealing_temp_dict[row_sensor_id] = row_annealing_temperature
        sensor_id_to_thickness_dict[row_sensor_id] = row["Thickness"]
        raw_fluence = row.get('Fluence') or row.get('Fluence Step 1')
        if raw_fluence is None:
            raise ValueError("Neither 'Fluence' nor 'Fluence Step 1' is present in the data.")
        sensor_id_to_fluence_dict[row_sensor_id] = float(str(raw_fluence).replace(',', '.'))

    sensor_id_TCT_factor_dict = {}
    sensor_id_date_dict = {}

    for _, row in google_sheet_meas_log_onPCB_df.iterrows():
        # Skip if Sensor ID is NaN
        if pd.isna(row["Sensor ID"]):
            print(f"Warning: Skipping row with NaN Sensor ID")
            continue
        
        row_date = row["Date"]
        if pd.notna(row_date):  # Only convert if not NaN
            row_date = datetime.strptime(row_date, "%d.%m.%Y")
        else:
            continue # measurement not done
        
        raw_sensor_id = str(row["Sensor ID"])  # Convert to string to handle any numeric values
        row_sensor_id = "_".join(raw_sensor_id.strip().split())
        # Check if the last part after splitting by underscore is a valid halfmoon
        parts = row_sensor_id.split('_')
        if not parts or parts[-1] not in VALID_HALFMOONS:
            print(f"Warning: Invalid halfmoon in sensor ID: {row_sensor_id}")
            continue
        row_annealing_time = row["Annealing time"]

        row_annealing_time = standardize_annealing_time(row_annealing_time)

        row_TCT_factor = extract_correction_factor(row["Laser Power, correction"])
        sensor_id_TCT_factor_dict[(row_sensor_id, row_annealing_time)] = row_TCT_factor
        sensor_id_date_dict[(row_sensor_id, row_annealing_time)] = row_date
        
    sensor_id_label_to_corrected_annealing_time = {}

    # Group by sensor_name
    for sensor_name, group_df in corrected_annealing_times_df.groupby("sensor_name"):
        # Sort group by the order in the file (or by label order if numeric)
        group_df = group_df.reset_index(drop=True)

        cumulative_time = 0  # Track total annealing time per sensor
        # cumulative_time_err_up = 0  # Track total uncert
        # cumulative_time_err_down = 0  # Track total uncert
        list_time_err_up = []  # Store uncertainty to use Gaussian error propagation
        list_time_err_down = []  # Store uncertainty to use Gaussian error propagation
        
        for _, row in group_df.iterrows():
            label = row["label"]
            real_added_time = row["real_added_time"]
            uncertainty_class = row["uncertainty_class"]
            time_unit_real_added_time = row["unit"]
            
            # Convert time unit to standarised format [min, h, days]
            if time_unit_real_added_time == "hours":
                time_unit_real_added_time = "h"
                
            # Skip rows with no label
            if pd.isna(label):
                continue

            # Handle missing or invalid real_added_time
            if pd.isna(real_added_time) or real_added_time == "-" or str(real_added_time).strip() == "":
                # If first entry or missing, assume no additional time
                real_added_time = 0.0

            # Convert possible string like "120", "2,5" to float
            try:
                real_added_time = float(str(real_added_time).replace(",", "."))
            except ValueError:
                # If parsing fails, skip or set to 0
                real_added_time = 0.0
                
            corr_ann_time_err_up = 0.0
            corr_ann_time_err_down = 0.0

            # Explicit up/down values in minutes
            if "/" in uncertainty_class:
                try:
                    up_str, down_str = uncertainty_class.split("/")
                    corr_ann_time_err_up = float(up_str.strip())
                    corr_ann_time_err_down = float(down_str.strip())
                except ValueError:
                    print(f"Could not parse uncertainty '{uncertainty_class}'")

            # Relative classes: small/medium/big
            elif uncertainty_class in ["small", "medium", "big"]:
                factor = {"small": 0.05, "medium": 0.1, "big": 0.5}[uncertainty_class]
                corr_ann_time_err_up = real_added_time * factor
                corr_ann_time_err_down = real_added_time * factor

                # Convert to minutes if needed
                if time_unit_real_added_time == "h":
                    corr_ann_time_err_up *= 60
                    corr_ann_time_err_down *= 60
            
            # Accumulate the annealing time
            cumulative_time += real_added_time
            
            # Accumulate the uncertainty
            list_time_err_up.append(corr_ann_time_err_up)
            list_time_err_down.append(corr_ann_time_err_down)
            
            # Calculate Gaussian error propagation
            cumulative_time_err_up = math.sqrt(sum([err**2 for err in list_time_err_up]))
            cumulative_time_err_down = math.sqrt(sum([err**2 for err in list_time_err_down]))
            
            # cumulative_time_err_up += corr_ann_time_err_up
            # cumulative_time_err_down += corr_ann_time_err_down
            
            # Standardise label to standarised format [min, h, days]
            label = standardize_annealing_time(label)

            # Store results in the dictionary
            sensor_id_label_to_corrected_annealing_time[(sensor_name, label)] = {
                "corrected_annealing_time": f"{round(cumulative_time, 2)}{time_unit_real_added_time}",
                "corr_ann_time_err_up": f"{round(cumulative_time_err_up, 2)}min",     
                "corr_ann_time_err_down": f"{round(cumulative_time_err_down, 2)}min"     
            }
            
    # Load the existing DataFrame if it exists
    if os.path.exists(df_path):
        df = pd.read_pickle(df_path)
    else:
        if overwrite_columns is None:
            # If the file doesn't exist, create an empty DataFrame with the required columns
            df = pd.DataFrame(columns=DATABASE_COLUMNS)
            df = df.set_index(DATABASE_INDEX_LEVEL)
        else: 
            print("No database to overwrite values in")
    
    # Initialize an empty list to store the new diode data
    diodes_data = []
    
    if measurement_dir in ["IVCV_bare"]:
        # Process all directories in the measurement_dir
        sensor_dirs = [dir for dir in os.listdir(os.path.join(root_path_data, measurement_dir)) if os.path.isdir(os.path.join(root_path_data, measurement_dir, dir))]

        # Iterate through the directories in the root path
        for sensor_dir in sensor_dirs: # sensor_dir = e.g. 100264_UL_5e14 in path: IVCV_bare|IV_onPCB|CV_onPCB|TCT
            # Ignore SR measurements for DoubleIrrNeutron2025 as they are treated as DoubleIrrSRNeutron2025
            if "_SR_" in sensor_dir and campaign == "DoubleIrrNeutron2025":
                continue
            # Ignore non-SR measurements for DoubleIrrSRNeutron2025
            if "_SR_" not in sensor_dir and campaign == "DoubleIrrSRNeutron2025":
                continue
            
            sensor_dir_full_path = os.path.join(root_path_data, measurement_dir, sensor_dir)
           
            sensor_id = sensor_dir
            print(f"sensor_id: {sensor_id}")

            annealing_time_iv_files_dict = {}
            annealing_time_cv_files_dict = {}
            annealing_time_TCT_files_dict = {}

            # Find the IV, CV and TCT files
            for file in os.listdir(sensor_dir_full_path): # file = e.g. 100264_UL_2025-02-20.iv|cv with bare. ||| e.g. 100264_UL_5e14_noadd|30min_IV|CV.csv onPCB IV|CV. ||| 
                                                        # e.g. file = folder 100264_UL_5e15_253_250230_Laser2333_noadd|30min onPCB TCT
                
                tmp_campaign = 'DoubleIrrNeutron2025' if campaign == 'DoubleIrrSRNeutron2025' else campaign
                if file.endswith('.iv'):
                    file_IV = os.path.join(tmp_campaign, measurement_dir, sensor_id, file)
                    annealing_time_iv_files_dict[annealing_time] = file_IV
                elif file.endswith('.cv'):
                    file_CV = os.path.join(tmp_campaign, measurement_dir, sensor_id, file)
                    annealing_time_cv_files_dict[annealing_time] = file_CV
                                  
                    
            # Get the fluence, particle from the irradiation DataFrame
            fluence = sensor_id_to_fluence_dict.get(sensor_id)
            # Extract halfmoon from sensor_id
            halfmoon = sensor_id.split('_')[-1]
                
            # If we don't have a valid halfmoon = wrong directory to store in database
            if halfmoon not in VALID_HALFMOONS:
                continue 

            # Get the thickness from the detector DataFrame
            try:
                thickness = sensor_id_to_thickness_dict.get(sensor_id)
            except:
                print(f"sensor_id: {sensor_id} not found in sensor_overview_csv")
                continue            
                        
            annealing_temp = sensor_id_to_annealing_temp_dict.get(sensor_id)

            all_annealing_times = set(annealing_time_iv_files_dict.keys()) | \
                                set(annealing_time_cv_files_dict.keys()) | \
                                set(annealing_time_TCT_files_dict.keys())
        
            # Iterate through each annealing time
            for annealing_time in all_annealing_times:
                if overwrite_columns is None:
                    # Check if the sensor_id is already in the existing DataFrame
                    if sensor_id in df.index.get_level_values('sensor_id'):
                        df_sensor = df.xs(sensor_id, level='sensor_id')
                        # Skip if the combination (sensor_id, annealing_time, type) already exists 
                        if annealing_time in df_sensor.index.get_level_values('annealing_time'):
                            df_sensor_annealing_time = df_sensor.xs(annealing_time, level='annealing_time')
                            # Check if the "type" already exists
                            if type in df_sensor_annealing_time["type"].values:
                                print(f"Warning: Measurement '{annealing_time}' with type '{type}' already exists for sensor_id {sensor_id}. Skipping.")
                                continue
                                
                # Get corresponding files for this annealing time
                iv_file = annealing_time_iv_files_dict.get(annealing_time)
                cv_file = annealing_time_cv_files_dict.get(annealing_time)
                
                data_dict = {
                    "sensor_id": str(sensor_id),
                    "campaign": str(campaign),
                    "thickness": int(thickness),
                    "fluence": float(fluence),
                    "temperature": -20,
                    "CVF": 2000,
                    "annealing_time": str(annealing_time),
                    "annealing_temp": annealing_temp,
                    "type": str(type),
                    "file_IV": str(iv_file),
                    "file_CV": str(cv_file),
                    "open_corr": open_corr,
                    "file_TCT": str(None),
                    "TCT_corr": np.nan,
                    "sat_V_CV": np.nan,
                    "sat_V_err_down_CV": np.nan,
                    "sat_V_err_up_CV": np.nan,
                    "low_fit_start_CV": np.nan,
                    "low_fit_stop_CV": np.nan,
                    "high_fit_start_CV": np.nan,
                    "high_fit_stop_CV": np.nan,
                    "upper_fit_params_CV": None, # To become a tuple of 3 floats
                    "sat_V_TCT": np.nan,
                    "sat_V_err_down_TCT": np.nan,
                    "sat_V_err_up_TCT": np.nan,
                    "low_fit_start_TCT": np.nan,
                    "low_fit_stop_TCT": np.nan,
                    "high_fit_start_TCT": np.nan,
                    "high_fit_stop_TCT": np.nan,
                    "upper_fit_params_TCT": None, # To become a tuple of 3 floats
                    "corrected_annealing_time": "",
                    "corr_ann_time_err_up": "",
                    "corr_ann_time_err_down": "",
                    "Blacklisted": False
                }
                
                if overwrite_columns is None:
                    # Append the data to the list
                    diodes_data.append((tuple(data_dict[col] for col in DATABASE_COLUMNS)))
                    print(f"success: {sensor_id} {annealing_time} {type}")
                else: 
                    df_reset = df.reset_index()
                    mask = (
                        (df_reset['sensor_id'] == sensor_id) &
                        (df_reset['annealing_time'] == annealing_time) &
                        (df_reset['type'] == type)
                    )
                    if mask.any():
                        for col in overwrite_columns:
                            if col in df_reset.columns:
                                df_reset.loc[mask, col] = data_dict.get(col, df_reset.loc[mask, col])
                        df = df_reset.set_index(DATABASE_INDEX_LEVEL)

    elif measurement_dir in ["IV_onPCB", "CV_onPCB", "TCT"]:
        measurement_dir_full_path = os.path.join(root_path_data, measurement_dir)
        
        for file in os.listdir(measurement_dir_full_path):
            # Ignore SR measurements for DoubleIrrNeutron2025 as they are treated as DoubleIrrSRNeutron2025
            if "_SR_" in file and campaign == "DoubleIrrNeutron2025":
                continue
            # Ignore non-SR measurements for DoubleIrrSRNeutron2025
            if "_SR_" not in file and campaign == "DoubleIrrSRNeutron2025":
                continue
            
            if file.endswith('.csv'):
                tmp_campaign = 'DoubleIrrNeutron2025' if campaign == 'DoubleIrrSRNeutron2025' else campaign
                file_path = os.path.join(tmp_campaign, measurement_dir, file)
                sensor_id, halfmoon, annealing_time = extract_file_info(filename=file, measurement_dir=measurement_dir)
                if sensor_id is None:
                    continue
                annealing_time = standardize_annealing_time(annealing_time) # [min, h, days]
                print(f"sensor_id: {sensor_id}, halfmoon: {halfmoon}, annealing_time: {annealing_time}")
                corrected_annealing_time_entry = sensor_id_label_to_corrected_annealing_time.get(
                    (sensor_id, annealing_time)
                )
                # If the sensor never existed in the dictionary, use defaults
                if not corrected_annealing_time_entry or not isinstance(corrected_annealing_time_entry, dict):
                    corrected_annealing_time_entry = {
                        "corrected_annealing_time": "",
                        "corr_ann_time_err_up": "",
                        "corr_ann_time_err_down": ""
                    }
                corrected_annealing_time = corrected_annealing_time_entry["corrected_annealing_time"]
                corr_ann_time_err_up = corrected_annealing_time_entry["corr_ann_time_err_up"]
                corr_ann_time_err_down = corrected_annealing_time_entry["corr_ann_time_err_down"]
                if corrected_annealing_time is None:
                    corrected_annealing_time = ""
                if corr_ann_time_err_up is None:
                    corr_ann_time_err_up = ""
                if corr_ann_time_err_down is None:
                    corr_ann_time_err_down = ""
                if halfmoon not in VALID_HALFMOONS:
                    continue
                try:
                    thickness = sensor_id_to_thickness_dict.get(sensor_id)
                except:
                    print(f"sensor_id: {sensor_id} not found in sensor_overview_csv")
                    continue

                if thickness is None:
                    print(f"sensor_id: {sensor_id} not found in sensor_overview_csv")
                    continue
                
                annealing_temp = sensor_id_to_annealing_temp_dict.get(sensor_id)

                if overwrite_columns is None:
                    # Check if the sensor_id is already in the existing DataFrame
                    if sensor_id in df.index.get_level_values('sensor_id'):
                        df_sensor = df.xs(sensor_id, level='sensor_id')
                        # Skip if the combination (sensor_id, annealing_time, type) already exists 
                        if annealing_time in df_sensor.index.get_level_values('annealing_time'):
                            df_sensor_annealing_time = df_sensor.xs(annealing_time, level='annealing_time')
                            # Check if the "type" already exists
                            if type in df_sensor_annealing_time["type"].values:
                                print(f"Warning: Measurement '{annealing_time}' with type '{type}' already exists for sensor_id {sensor_id}. Skipping.")
                                continue

                # Get TCT correction factor for this sensor and annealing time
                TCT_corr = sensor_id_TCT_factor_dict.get((sensor_id, annealing_time))
                
                # Get date for this sensor and annealing time
                date = sensor_id_date_dict.get((sensor_id, annealing_time))
                open_cv_corr_value = extract_open_cv_corr_value(date, sensor_id, annealing_time)
                print(f"sensor_id: {sensor_id}, halfmoon: {halfmoon}, annealing_time: {annealing_time}, corrected_annealing_time: {corrected_annealing_time}, corr_ann_time_err_up: {corr_ann_time_err_up}, corr_ann_time_err_down: {corr_ann_time_err_down}, open_cv_corr: {open_cv_corr_value}")

                if TCT_corr is None or np.isnan(TCT_corr):
                    TCT_corr = 1

                if measurement_dir == "TCT":
                    file_TCT = file_path
                    file_IV, file_CV = check_file_exist_in_database(df, sensor_id, measurement_dir, annealing_time, type)
                elif measurement_dir == "IV_onPCB":
                    file_IV = file_path
                    file_CV, file_TCT = check_file_exist_in_database(df, sensor_id, measurement_dir, annealing_time, type)
                elif measurement_dir == "CV_onPCB":
                    file_CV = file_path
                    file_IV, file_TCT = check_file_exist_in_database(df, sensor_id, measurement_dir, annealing_time, type)

                fluence = sensor_id_to_fluence_dict.get(sensor_id)


                data_dict = {
                    "sensor_id": str(sensor_id),
                    "campaign": str(campaign),
                    "thickness": int(thickness),
                    "fluence": float(fluence),
                    "temperature": -20,
                    "CVF": 2000,
                    "annealing_time": str(annealing_time),
                    "annealing_temp": annealing_temp,
                    "type": str(type),
                    "file_IV": str(file_IV),
                    "file_CV": str(file_CV),
                    "open_corr": open_cv_corr_value,
                    "file_TCT": str(file_TCT),
                    "TCT_corr": float(TCT_corr),
                    "sat_V_CV": np.nan,
                    "sat_V_err_down_CV": np.nan,
                    "sat_V_err_up_CV": np.nan,
                    "low_fit_start_CV": np.nan,
                    "low_fit_stop_CV": np.nan,
                    "high_fit_start_CV": np.nan,
                    "high_fit_stop_CV": np.nan,
                    "upper_fit_params_CV": None, # To become a tuple of 3 floats
                    "sat_V_TCT": np.nan,
                    "sat_V_err_down_TCT": np.nan,
                    "sat_V_err_up_TCT": np.nan,
                    "low_fit_start_TCT": np.nan,
                    "low_fit_stop_TCT": np.nan,
                    "high_fit_start_TCT": np.nan,
                    "high_fit_stop_TCT": np.nan,
                    "upper_fit_params_TCT": None, # To become a tuple of 3 floats
                    "corrected_annealing_time": str(corrected_annealing_time),
                    "corr_ann_time_err_up": str(corr_ann_time_err_up),
                    "corr_ann_time_err_down": str(corr_ann_time_err_down),
                    "Blacklisted": False
                }
                
                if overwrite_columns is None:
                    # Append the data to the list
                    diodes_data.append((tuple(data_dict[col] for col in DATABASE_COLUMNS)))
                    print(f"success: {sensor_id} {annealing_time} {type}")
                else: 
                    df_reset = df.reset_index()
                    mask = (
                        (df_reset['sensor_id'] == sensor_id) &
                        (df_reset['annealing_time'] == annealing_time) &
                        (df_reset['type'] == type)
                    )
                    if mask.any():
                        for col in overwrite_columns:
                            if col in df_reset.columns:
                                df_reset.loc[mask, col] = data_dict.get(col, df_reset.loc[mask, col])
                        df = df_reset.set_index(DATABASE_INDEX_LEVEL)

        

    if overwrite_columns is None:
        # Create a DataFrame for the new data
        df_new = pd.DataFrame(diodes_data, columns=DATABASE_COLUMNS)

        # Unsure that columns are correct types
        for col, dtype in COLUMN_DTYPES.items():
            if col in df_new.columns:
                df_new[col] = df_new[col].astype(dtype, errors="ignore")
        
        # Set multi-index for the new DataFrame
        df_new = df_new.set_index(DATABASE_INDEX_LEVEL)

        # Append the new data to the existing DataFrame
        df_updated = pd.concat([df, df_new])

        # Sort the updated DataFrame
        df_updated = df_updated.sort_index(level=["campaign", "fluence", "annealing_time"])

        # Reset all values to False 
        df_updated['Blacklisted'] = False

        # Read in Blacklisted_measurements.csv (columns: sensor_id, type, annealing_time)
        df_blacklisted = pd.read_csv(os.path.join(ROOT_PATH_REPO, "Blacklisted_measurements.csv"))
        
        # Go through the blacklisted measurements and set the matching sensor_id,type,annealing_time mask to True
        for _, row in df_blacklisted.iterrows():
            if row["Annealing_Time"] == "all":
                mask = (
                    (df_updated.index.get_level_values('sensor_id') == row['Sensor']) &
                    (df_updated['type'] == row['Type'])
                )
            else:
                mask = (
                    (df_updated.index.get_level_values('sensor_id') == row['Sensor']) &
                    (df_updated['type'] == row['Type']) &
                    (df_updated.index.get_level_values('annealing_time') == row['Annealing_Time'])
                )
            df_updated.loc[mask, 'Blacklisted'] = True

        # Save the updated DataFrame to a pickle file
        df_updated.to_pickle(df_path)
        return df_updated
    else:
        df = df.sort_index(level=["campaign", "fluence", "annealing_time"])

        # Reset all values to False 
        df['Blacklisted'] = False

        # Read in Blacklisted_measurements.csv (columns: sensor_id, type, annealing_time)
        df_blacklisted = pd.read_csv(os.path.join(ROOT_PATH_REPO, "Blacklisted_measurements.csv"))
        
        # Go through the blacklisted measurements and set the matching sensor_id,type,annealing_time mask to True
        for _, row in df_blacklisted.iterrows():
            if row["Annealing_Time"] == "all":
                mask = (
                    (df.index.get_level_values('sensor_id') == row['Sensor']) &
                    (df['type'] == row['Type'])
                )
            else:
                mask = (
                    (df.index.get_level_values('sensor_id') == row['Sensor']) &
                    (df['type'] == row['Type']) &
                    (df.index.get_level_values('annealing_time') == row['Annealing_Time'])
                )
            df.loc[mask, 'Blacklisted'] = True

        df.to_pickle(df_path)
        return df
    
    
def extract_unique_values_from_database(database):
    # Get unique values from index levels and columns
    if database is not None:
        campaigns = sorted(database.index.get_level_values('campaign').unique().tolist())
        thickness = sorted([str(thickness) for thickness in database.index.get_level_values('thickness').unique().tolist()])
        annealing_time = sort_annealing_time(database.index.get_level_values('annealing_time').unique().tolist())
        annealing_temp = sorted([str(temp) for temp in database['annealing_temp'].unique().tolist()])
        sensor_id = sorted(database.index.get_level_values('sensor_id').unique().tolist())
        measurement_type = sorted(database['type'].unique().tolist())
    else:
        campaigns = []
        thickness = []
        annealing_time = []
        annealing_temp = []
        sensor_id = []
        measurement_type = []
        
    return campaigns, thickness, annealing_time, annealing_temp, sensor_id, measurement_type

def extract_open_cv_corr_value(date, sensor_id, annealing_time):
    open_cv_before_20231116 = 4.98418735e-11
    open_cv_after_20231116 = 5.0276597281666e-11
    if date is not None:
        if date <= datetime(2023, 11, 16):
            return open_cv_before_20231116
        else:
            return open_cv_after_20231116
    else:
        print(f"Warning: No date found for sensor_id: {sensor_id} and annealing_time: {annealing_time}")
        return 0

