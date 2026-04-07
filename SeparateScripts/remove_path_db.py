import pandas as pd
import os
import sys

# Add parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.insert(0, parent_dir)

from config import DEFAULT_DATABASE_PATH, DATABASE_COLUMNS, DATABASE_INDEX_LEVEL
# import the database
df = pd.read_pickle(DEFAULT_DATABASE_PATH)

# Reset the index to make all index levels regular columns
df_reset = df.reset_index()

# Print before changes
print("Before conversion:")
print(df_reset)

print(f"Unique columns: {df_reset.columns.unique()}")

# Prepend campaign to file paths with special case, avoiding duplicates
for file_col in ['file_IV', 'file_CV', 'file_TCT']:
    if file_col in df_reset.columns:
        df_reset[file_col] = df_reset.apply(
            lambda row: (
                os.path.join(
                    'DoubleIrrNeutron2025' if row['campaign'] == 'DoubleIrrSRNeutron2025' else row['campaign'],
                    row[file_col]
                )
                if pd.notna(row[file_col]) and 
                   not (( 'DoubleIrrNeutron2025' if row['campaign'] == 'DoubleIrrSRNeutron2025' else row['campaign']) in row[file_col])
                else row[file_col]
            ),
            axis=1
        )



# Check results
print(df_reset[['campaign', 'file_IV', 'file_CV', 'file_TCT']].head())

print(f"Unique columns: {df_reset.columns.unique()}")

print(f"Unique values of file_iv columns: {df_reset['file_IV'].unique()}")

# Set the index back using the specified index levels
df = df_reset.set_index(DATABASE_INDEX_LEVEL)

# Save the database
df.to_pickle(DEFAULT_DATABASE_PATH)
print(f"\nDatabase saved with string annealing_time values to {DEFAULT_DATABASE_PATH}")