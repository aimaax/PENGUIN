import os
import shutil

def move_csv_files(root_folder):
    destination_folder = os.path.join(root_folder, "TCT_ALL_CSV")
    os.makedirs(destination_folder, exist_ok=True)
    
    for dirpath, _, filenames in os.walk(root_folder):
        if dirpath == destination_folder:
            continue  # Skip the destination folder itself
        
        for file in filenames:
            if file.lower().endswith(".csv"):
                source_path = os.path.join(dirpath, file)
                destination_path = os.path.join(destination_folder, file)
                
                # Ensure unique filenames in destination
                counter = 1
                while os.path.exists(destination_path):
                    name, ext = os.path.splitext(file)
                    destination_path = os.path.join(destination_folder, f"{name}_{counter}{ext}")
                    counter += 1
                
                shutil.copy2(source_path, destination_path)
                print(f"Copied: {source_path} -> {destination_path}")

if __name__ == "__main__":
    folder_to_search = r"C:\Users\MaxAn\Documents\VScode\CERN\IVCV_Analyses\Data\LowFluenceIrrNeutron2025\TCT"
    move_csv_files(folder_to_search)