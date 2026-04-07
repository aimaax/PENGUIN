import pandas as pd
import os
from math import pi
import numpy as np
from Utils.constants import ConvFactor
from config import DEFAULT_DIR_DATA, FULLCHARGE_CC_DICT
    
def get_files(measurements):
    measurement_files = []
    
    # if single measurement is used as agument, turn it into a list so the loop works
    if type(measurements) == str:
        measurements = [measurements]
    
    # loop over the arguments
    for measurement in measurements:
        # in case the argument is a direct path to a measurement
        if os.path.isfile(measurement):
            measurement_files.append(measurement)
        
    return measurement_files


##############################################################
##############        Bare Measurements       ################
##############################################################


def makeDataFrameBare_IV(iv_path):
    # Check if the file exists
    if not os.path.isfile(iv_path):
        print('Not a file!')
        return 0

    # Initialize variables
    headerSSD = 'BEGIN'
    footerSSD = 'END'
    sr = 0  # Number of header rows to skip
    sf = 0  # Number of footer rows to skip
    col = ['Volt_nom', 'I_tot', 'I_pad']  # Column names for the DataFrame

    try:
        with open(iv_path) as file:
            lines = [line.strip() for line in file.readlines()]

            # Find the start and end of the data block
            begin_index = -1
            end_index = -1
            for i, line in enumerate(lines):
                line = "".join(line.split())  # Remove all whitespace, including tabs
                if line == headerSSD:
                    begin_index = i
                elif line == footerSSD:
                    end_index = i
                    break

            # Check if the data block is valid
            if begin_index == -1 or end_index == -1:
                print('Measurement not recognized: ' + iv_path)
                return 0
            if begin_index >= end_index:
                print('Measurement empty or invalid: ' + iv_path)
                return 0

            # Set the number of rows to skip (header and footer)
            sr = begin_index + 1  # Skip rows up to and including BEGIN
            sf = len(lines) - end_index  # Skip rows from END to the end of the file

    except UnicodeDecodeError:
        print('Incompatible file format: ' + iv_path)
        return 0

    try:
        # Load the data into a DataFrame
        iv = pd.read_csv(iv_path, skiprows=sr, skipfooter=sf, sep='\t', header=None, names=col, engine='python')
        
        # Ensure all values are positive
        iv.Volt_nom = abs(iv.Volt_nom)
        iv.I_pad = abs(iv.I_pad)
        iv.I_tot = abs(iv.I_tot)

        return iv

    except Exception as e:
        print(f'Loading error of IV measurement: {iv_path}')
        print(f'Error: {e}')
        return 0
    


def makeDataFrameBare_CV(cv_path):
    # Check if the file exists
    if not os.path.isfile(cv_path):
        print('Not a file!')
        return 0

    # Initialize variables
    headerSSD = 'BEGIN'
    footerSSD = 'END'
    sr = 0  # Number of header rows to skip
    sf = 0  # Number of footer rows to skip
    sensorID = 'test'
    lab = 'none'
    col = ['v_nom', 'cp', 'cond', 'v_meas', 'i_tot']  # Column names for the DataFrame

    try:
        with open(cv_path) as file:
            lines = ["".join(line.split()) for line in file.readlines()]  # Remove all whitespace, including tabs

            # Find the start and end of the data block
            begin_index = -1
            end_index = -1
            for i, line in enumerate(lines):
                if line == headerSSD:
                    begin_index = i
                elif line == footerSSD:
                    end_index = i
                    break

            # Check if the data block is valid
            if begin_index == -1 or end_index == -1:
                print('Measurement not recognized: ' + cv_path)
                return 0
            if begin_index >= end_index:
                print('Measurement empty or invalid: ' + cv_path)
                return 0

            # Set the number of rows to skip (header and footer)
            sr = begin_index + 1  # Skip rows up to and including BEGIN
            sf = len(lines) - end_index  # Skip rows from END to the end of the file

            # Extract additional metadata
            lab = "SSD"
            freq = float(lines[lines.index("LCRmeter:AgilentE4980A") + 1][11:-2])
            open_c = float(lines[lines.index(":LCRopencorrection:C[F],G[S]") + 1].split(',')[0])
            open_g = float(lines[lines.index(":LCRopencorrection:C[F],G[S]") + 1].split(',')[1])
            sensorID = os.path.basename(cv_path)

    except UnicodeDecodeError:
        print('Incompatible file format: ' + cv_path)
        return 0
    except Exception as e:
        print(f'Error parsing metadata: {e}')
        return 0

    try:
        # Load the data into a DataFrame
        cv = pd.read_csv(cv_path, skiprows=sr, skipfooter=sf, sep='\t', header=None, engine='python')
        cv.columns = col

        # Ensure all voltage values are positive
        cv.v_nom = abs(cv.v_nom)
        cv.v_meas = abs(cv.v_meas)

        # Add metadata to the DataFrame
        cv.sensorID = sensorID
        cv.freq = freq
        cv.lab = lab

        # Calculate additional capacitance values if lab is SSD
        if lab == "SSD":
            w = freq * 2 * pi
            Rp = 1 / (cv.cond)
            cv['cs'] = (cv.cond**2 + w**2 * (cv.cp)**2) / (w**2 * (cv.cp))

        return cv

    except Exception as e:
        print(f'Loading error of CV measurement: {cv_path}')
        print(f'Error: {e}')
        return 0
    


##############################################################
##############       OnPCB Measurements       ################
##############################################################

def makeDataFrame_IV(filename, skiprows=1):
    iv = pd.read_csv(filename,
                       names=["set voltage (V)", "real voltage (V)", "current (A)", "delta current", "input current (A)"],
                       decimal='.',
                       skiprows=skiprows,
                       engine='python',
                       delimiter=';')
    iv["set voltage (V)"] = pd.to_numeric(iv["set voltage (V)"], errors="coerce")
    iv["current (A)"] = pd.to_numeric(iv["current (A)"], errors="coerce")
    iv["Voltage"] = abs(iv["set voltage (V)"])
    iv["I"] = iv["current (A)"]
    iv["I_err"] = iv["delta current"]
    return iv[["Voltage", "I", "I_err"]]



##########################CV####################################
def makeDataFrame_CV(filename, open_corr=None, skiprows=1):
    # Read the entire CSV to get the first row as column names
    cv = pd.read_csv(filename, decimal='.', skiprows=0, engine='python', delimiter=';')

    cv['Voltage'] = abs(cv['set voltage (V)'])
    # cv['serial capacitance corrected'] = cv['serial capacitance'].sub(open_corr)
    
    # --- Safe check for open_corr ---
    try:
        open_corr_val = float(open_corr)
    except (TypeError, ValueError):
        open_corr_val = np.nan  # if None, string, or not convertible
        
    if not np.isnan(open_corr_val):
        cv["ser_cap"] = abs(cv["serial capacitance"].astype(np.float64)) - float(open_corr_val)
    else:
        cv["ser_cap"] = cv["serial capacitance"]
        
    cv['1/ser_cap2'] = cv['1/serial capacitance^2']
    cv['norm_1/ser_cap2'] = cv['1/ser_cap2'] / max(cv['1/ser_cap2'])

    # cv['1/serial capacitance^2 corrected'] = (1 / cv['serial capacitance corrected'])**2
    # cv['1/serial capacitance^2 corrected normalized'] = cv['1/serial capacitance^2 corrected'] / max(cv['1/serial capacitance^2 corrected'])

    return cv[["Voltage", "ser_cap", "1/ser_cap2", "norm_1/ser_cap2"]]
    


##########################TCT####################################

def makeDataFrame_TCT(filename, TCT_corr_factor, thickness):
    try:
        # First try reading as standard CSV
        try:
            TCT_df = pd.read_csv(filename)
            # Drop the Num column if it exists
            if 'Num' in TCT_df.columns:
                TCT_df = TCT_df.drop(columns=["Num"])

            TCT_df["Voltage"] = abs(TCT_df["Voltage"])
            
            TCT_df["CC_corr"] = TCT_df["CCE2[a.u.]"] * TCT_corr_factor * ConvFactor
            TCT_df["CC_err_corr"] = TCT_df["Error mean"] * TCT_corr_factor * ConvFactor

            # print(TCT_df["CC_corr"])

            # Calculate CCEff based on thickness
            # if thickness == 120:
            #     # fullcharge = 0.55480395
            #     # fullcharge = 0.574755
            #     # fullcharge = 0.5639227591 # prev
            #     # fullcharge = 66.33 # recalculate with new 120um sensor
            #     fullcharge = 58
            # elif thickness == 200:
            #     # fullcharge = 0.98381424
            #     # fullcharge = 1.0192
            #     # fullcharge = 1.02040907738
            #     fullcharge = 108.99
            # elif thickness == 300:
            #     # fullcharge = 1.38308191940752
            #     # fullcharge = 1.432751
            #     # fullcharge = 1.43278152868
            #     fullcharge = 143
            if thickness in [120, 200, 300]:
                fullcharge = FULLCHARGE_CC_DICT[thickness]
            else:
                raise ValueError(f"Unsupported thickness: {thickness}")

            TCT_df["CCEff_corr"] = TCT_df["CC_corr"] / fullcharge * 100
            TCT_df["CCEff_err_corr"] = TCT_df["CC_err_corr"] / fullcharge * 100
            # print(TCT_df["CCEff_corr"])

            return TCT_df[["Voltage", "CC_corr", "CC_err_corr", "CCEff_corr", "CCEff_err_corr"]]
        except:
            # If that fails, try reading as semicolon-separated with different column names
            TCT_df = pd.read_csv(filename,
                       names=["Num", "Voltage", "Ileak[nA]", "CCE[a.u.]", "CCE2[a.u.]", "CCE2err[a.u.]", "MPV[mV]", "Noise[mV]"],
                       decimal='.',
                       skiprows=1,
                       engine='python',
                       delimiter=';')
                       
        
            # Drop the Num column if it exists
            if 'Num' in TCT_df.columns:
                TCT_df = TCT_df.drop(columns=["Num"])

            TCT_df["Voltage"] = abs(TCT_df["Voltage"])
            
            TCT_df["CC_corr"] = TCT_df["CCE2[a.u.]"] * TCT_corr_factor * ConvFactor
            TCT_df["CC_err_corr"] = TCT_df["CCE2err[a.u.]"] * TCT_corr_factor * ConvFactor

            # Calculate CCEff based on thickness
            # if thickness == 120:
            #     # fullcharge = 0.55480395
            #     # fullcharge = 0.574755
            #     # fullcharge = 0.5639227591
            #     fullcharge = 66.33
            # elif thickness == 200:
            #     # fullcharge = 0.98381424
            #     # fullcharge = 1.0192
            #     # fullcharge = 1.02040907738
            #     fullcharge = 108.99
            # elif thickness == 300:
            #     # fullcharge = 1.38308191940752
            #     # fullcharge = 1.432751
            #     # fullcharge = 1.43278152868
            #     fullcharge = 143
            if thickness in [120, 200, 300]:
                fullcharge = FULLCHARGE_CC_DICT[thickness]
            else:
                raise ValueError(f"Unsupported thickness: {thickness}")

            TCT_df["CCEff_corr"] = TCT_df["CC_corr"] / fullcharge * 100
            TCT_df["CCEff_err_corr"] = TCT_df["CC_err_corr"] / fullcharge * 100

            return TCT_df[["Voltage", "CC_corr", "CC_err_corr", "CCEff_corr", "CCEff_err_corr"]]
    
    except Exception as e:
        print(f"Error processing TCT file {filename}: {e}")
        return None

def get_saturation_voltage_df_list_sensor(df, measrement_type, fit_from_TCT):
    """Get saturation voltage DataFrame list."""
    # Determine the file column based on fit_from_TCT
    file_column = "file_TCT" if fit_from_TCT else "file_CV"
    
    # Reset index to access columns directly
    df_reset = df.reset_index()
    
    # Build list of DataFrames directly by iterating through rows
    df_list = []
    sensor_ids_seen = set()
    
    for _, row in df_reset.iterrows():
        file_end = row[file_column]
        
        # Skip if file is None or "None"
        if pd.isna(file_end) or file_end == "None":
            continue
        
        # Build full path
        full_path = os.path.join(DEFAULT_DIR_DATA, file_end)
        
        # Check if file exists and has correct extension
        if not os.path.isfile(full_path):
            continue
        if not (full_path.endswith(".cv") or full_path.endswith(".csv")):
            continue
        
        # Load appropriate DataFrame based on measurement type
        if measrement_type == "bare":
            data_df = makeDataFrameBare_CV(full_path)
        elif measrement_type == "onPCB":
            if not fit_from_TCT:
                data_df = makeDataFrame_CV(full_path, open_corr=row["open_corr"])
            else:
                data_df = makeDataFrame_TCT(
                    full_path, 
                    TCT_corr_factor=row["TCT_corr"], 
                    thickness=row["thickness"]
                )
        else:
            continue
        
        # Add metadata columns if DataFrame is valid
        if isinstance(data_df, pd.DataFrame):
            data_df["sensor_id"] = row["sensor_id"]
            data_df["thickness"] = row["thickness"]
            data_df["annealing_time"] = row["annealing_time"]
            data_df["TCT_corr"] = row["TCT_corr"]
            df_list.append(data_df)
            sensor_ids_seen.add(row["sensor_id"])
    
    # Check if any measurements were found
    if not df_list:
        print("No CV measurements selected!")
        return 0
    
    # Create a single DataFrame
    combined_df = pd.concat(df_list, ignore_index=True)
    
    # Get unique sensor IDs (preserving order from original DataFrame)
    list_sensor_id = [sid for sid in df_reset["sensor_id"].unique() if sid in sensor_ids_seen]
    
    pd.set_option("display.max.rows", None)
    pd.set_option("display.max.columns", None)
    pd.set_option("display.width", None)
    pd.set_option("display.max_colwidth", None)
    
    return list_sensor_id, combined_df