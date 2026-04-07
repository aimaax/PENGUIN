
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import sys
import os

def plot_temperature_data(csv_file1: str, csv_file2: str = None, output_file: str = None, label1: str = None, label2: str = None):
    """
    Plot temperature data from one or two CSV files.
    
    Parameters
    ----------
    csv_file1 : str
        Path to the first CSV file containing temperature data
    csv_file2 : str, optional
        Path to the second CSV file containing temperature data
    output_file : str, optional
        Path to save the plot. If None, displays the plot interactively.
    label1 : str, optional
        Label for the first dataset. If None, uses filename.
    label2 : str, optional
        Label for the second dataset. If None, uses filename.
    """
    # Create figure and axes
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Function to load and process a single file
    def load_data(csv_file: str):
        """Load and process temperature data from CSV file."""
        df = pd.read_csv(csv_file)
        df["Time"] = pd.to_datetime(df["Time"])
        
        # Check which column name is used for temperature
        if "PM8_Room.mean" in df.columns:
            df["Temperature"] = df["PM8_Room.mean"].str.replace("°C", "").str.strip().astype(float)
        elif "Temperature" in df.columns:
            df["Temperature"] = df["Temperature"].str.replace("°C", "").str.strip().astype(float)
        else:
            raise ValueError(f"Could not find temperature column in {csv_file}")
        df = df[(df["Temperature"] >= 15) & (df["Temperature"] <= 25)]
        df = df.sort_values("Time")
        return df
    
    # Load first file
    df1 = load_data(csv_file1)
    label1 = "Temperature in Clean Room"
    ax.plot(df1["Time"], df1["Temperature"], marker="o", linestyle="none", linewidth=1.5, 
            markersize=5, color="blue", label=label1, alpha=1)
    
    # Calculate mean for first file
    mean1 = df1["Temperature"].mean()
    
    # Load and plot second file if provided
    if csv_file2:
        df2 = load_data(csv_file2)
        label2 = "Temperature in Storage Cabinet"
        ax.plot(df2["Time"], df2["Temperature"], marker="o", linestyle="none", linewidth=1.5, 
                markersize=5, color="red", label=label2, alpha=1)
        
        # Calculate mean for second file
        mean2 = df2["Temperature"].mean()
        
        # Plot horizontal dashed lines for means
        ax.axhline(mean1, color="blue", linestyle="--", linewidth=1.5, alpha=0.7,
                   label=f"Mean {label1}: {mean1:.2f}°C")
        ax.axhline(mean2, color="red", linestyle="--", linewidth=1.5, alpha=0.7,
                   label=f"Mean {label2}: {mean2:.2f}°C")
        
        # Use the combined time range for x-axis
        all_times = pd.concat([df1["Time"], df2["Time"]])
        min_time = all_times.min()
        max_time = all_times.max()
    else:
        # Plot horizontal dashed line for mean (single file)
        ax.axhline(mean1, color="blue", linestyle="--", linewidth=1.5, alpha=0.7,
                   label=f"Mean {label1}: {mean1:.2f}°C")
        
        min_time = df1["Time"].min()
        max_time = df1["Time"].max()
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    
    # Calculate appropriate interval for date labels
    time_span = (max_time - min_time).days
    if time_span > 0:
        interval = max(1, time_span // 20)  # Show ~20 date labels
    else:
        interval = 1
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=interval))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")
    
    # Labels and title
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Temperature [°C]", fontsize=12)
    ax.set_title("Temperature in Clean Room and Storage Cabinet", fontsize=18, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=16, loc="best")
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"Plot saved to: {output_file}")
    else:
        plt.show()

if __name__ == "__main__":
    # Get CSV file paths from command line arguments or use defaults
    if len(sys.argv) > 1:
        csv_file1 = sys.argv[1]
    else:
        # Default to the first file
        csv_file1 = r"TempCleanRoom.csv"
    
    if len(sys.argv) > 2:
        csv_file2 = sys.argv[2]
    else:
        # Default to the second file if it exists
        csv_file2 = r"TempCleanRoomStorageCabinet.csv"
        if not os.path.isfile(csv_file2):
            csv_file2 = None
    
    # Check if first file exists
    if not os.path.isfile(csv_file1):
        print(f"Error: File not found: {csv_file1}")
        sys.exit(1)
    
    # Check if second file exists (if provided)
    if csv_file2 and not os.path.isfile(csv_file2):
        print(f"Warning: Second file not found: {csv_file2}")
        print("Plotting only the first file...")
        csv_file2 = None
    
    # Optional: output file path
    output_file = None
    if len(sys.argv) > 3:
        output_file = sys.argv[3]
    
    # Plot the data
    plot_temperature_data(csv_file1, csv_file2, output_file)