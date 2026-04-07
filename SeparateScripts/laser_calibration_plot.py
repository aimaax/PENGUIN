import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import sys
from collections import defaultdict

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEFAULT_DIR_DATA

UIRAD_data_dir = os.path.join(DEFAULT_DIR_DATA, "300um_UIRAD")
data = defaultdict(list)  

# Walk through directories and find relevant CSV files
for dirpath, _, filenames in os.walk(UIRAD_data_dir):
    for file in filenames:
        if file.endswith('.npz'):
            # remove the npz file
            os.remove(os.path.join(dirpath, file))
        if file.endswith('.csv') and 'Laser' in file:
            parts = file.split('_')
            if len(parts) >= 5:
                date_str = parts[3]
                laser_part = parts[4]
                try:
                    date = datetime.strptime(date_str, '%y%m%d')
                    laser_id = laser_part.replace('Laser', '').replace('.csv', '')
                    filepath = os.path.join(dirpath, file)
                    df = pd.read_csv(filepath)
                    mean_cce2 = df['CCE2[a.u.]'].mean()
                    data[laser_id].append((date, mean_cce2))
                except Exception as e:
                    print(f"Error processing {file}: {e}")

# Plotting
plt.figure(figsize=(10, 5))

for laser_id, values in data.items():
    values.sort() 
    dates, means = zip(*values)
    plt.scatter(dates, means, label=f'Laser {laser_id}', s=70) 

plt.xlabel('Date')
plt.ylabel('Mean CCE2 [a.u.]')
plt.title('Mean CCE2 over Time 300um UIRAD')
plt.grid(True, alpha=0.5)
plt.legend(fontsize=16)
plt.tight_layout()
plt.show()
