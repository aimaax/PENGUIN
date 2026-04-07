import os
import sys
import matplotlib.pyplot as plt

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Helper_Functions.dataframe_helper import get_files, makeDataFrame_IV
from config import RC_PLOT_STYLE, FILLSTYLE, MARKERSIZE, LEGEND_SIZE

# base_path_pad_vs_gr = "C:/Users/MaxAn/Documents/VScode/CERN/Particulars_Analysis/particulars-analysis/Data/ProtonIrr2024/Pad_vs_GR"
# list_path_pad_vs_gr_measurements = [
#     base_path_pad_vs_gr + "/P6213_10_UL_8e15_90min_IV.csv",
#     base_path_pad_vs_gr + "/P6213_10_UL_8e15_90min_IV_pad.csv",
#     base_path_pad_vs_gr + "/N8740_4_UR_4e15_90min_IV.csv",
#     base_path_pad_vs_gr + "/N8740_4_UR_4e15_90min_IV_pad.csv",
#     base_path_pad_vs_gr + "/N8738_4_UR_4e15_90min_IV.csv",
#     base_path_pad_vs_gr + "/N8738_4_UR_4e15_90min_IV_pad.csv",
# ]
base_path_pad_vs_total = "C:/Users/MaxAn/Documents/VScode/CERN/Particulars_Analysis/particulars-analysis/Data/LowFluenceIrrNeutron2025/Pad_vs_Total_IV"
list_path_pad_vs_total_measurements = [
    # base_path_pad_vs_total + "/100228_UL_1e13_6days_IV.csv",
    # base_path_pad_vs_total + "/100228_UL_1e13_6days_IV_OLD.csv",
    # base_path_pad_vs_total + "/200169_UL_1e13_6days_IV.csv",
    # base_path_pad_vs_total + "/200169_UL_1e13_6days_IV_OLD.csv",
    # base_path_pad_vs_total + "/300053_UL_1e13_6days_IV.csv",
    # base_path_pad_vs_total + "/300053_UL_1e13_6days_IV_OLD.csv",
    # base_path_pad_vs_total + "/100228_UR1_1e13_250min_IV.csv",
    # base_path_pad_vs_total + "/100228_UR1_1e13_250min_IV_OLD.csv",
    # base_path_pad_vs_total + "/200169_LL2_1e13_250min_IV.csv",
    # base_path_pad_vs_total + "/200169_LL2_1e13_250min_IV_OLD.csv",
    # base_path_pad_vs_total + "/300053_UR2_1e13_250min_IV.csv",
    # base_path_pad_vs_total + "/300053_UR2_1e13_250min_IV_OLD.csv",
    base_path_pad_vs_total + "/100332_UR1_5e13_6days_IV.csv",
    base_path_pad_vs_total + "/100332_UR1_5e13_6days_IV_OLD.csv",
]

print(list_path_pad_vs_total_measurements)

files = get_files(list_path_pad_vs_total_measurements)

# attempt to load measurements and save them in a list of data frames
ivs_df = []
for iv in files:
    iv_df = makeDataFrame_IV(iv)
    if type(iv_df) != int:
        ivs_df.append(iv_df)
        
print(ivs_df)

# Stop if the IV list is empty
if ivs_df == []:
    print("No IV measurements selected!")

column = 'I'
    

###title
plt.title("Pad vs Total Current IV", weight='bold')

###plotting
i=0

# color = ["blue", "darkblue", "red", "darkred", "green", "darkgreen"]
# label = ["Abs Val. 100228_UL", "Total 100228_UL", "Abs Val. 200169_UL", "Total 200169_UL", "Abs Val. 300053_UL", "Total 300053_UL"]
color = ["blue", "darkblue"]
label = ["Abs Val. 100332_UR1", "Total 100332_UR1"]
style = ["o", "o"]

for iv_df in ivs_df: 
    curr = iv_df[column]*1e6
    curr = abs(curr)
    voltage = iv_df['Voltage']
        
    plt.plot(voltage, curr, color=color[i], marker=style[i], markersize=10, linestyle="-", label=label[i])
    i=i+1

plt.xlabel("Bias Voltage [V]", fontsize=14)
plt.ylabel("Leakage Current [uA]", fontsize=14)

plt.xlim(0, 900)

# make dotted grid
plt.grid(linestyle="--", color="gray", alpha=0.5)
# place legend on the upper right corner
plt.legend(bbox_to_anchor=(0.98, 0.02), fontsize=18, loc="lower right", frameon=True)
plt.show()