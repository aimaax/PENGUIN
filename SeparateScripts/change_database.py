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

# Print before changes
print("Before conversion:")
print(df)
print("Annealing time dtype:", df.index.get_level_values('annealing_time').dtype)

# Reset the index to make all index levels regular columns
df_reset = df.reset_index()

# Convert annealing_time column to string
df_reset['annealing_time'] = df_reset['annealing_time'].astype(str)

# Set the index back using the specified index levels
df = df_reset.set_index(DATABASE_INDEX_LEVEL)

# Print after changes
print("\nAfter conversion:")
print(df)
print("Annealing time dtype:", df.index.get_level_values('annealing_time').dtype)

# Save the database
df.to_pickle(DEFAULT_DATABASE_PATH)
print(f"\nDatabase saved with string annealing_time values to {DEFAULT_DATABASE_PATH}")