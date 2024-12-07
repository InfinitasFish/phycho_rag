import os
import zipfile

def unzip_and_remove(zip_folder_path):
    for file_name in os.listdir(zip_folder_path):
        file_path = os.path.join(zip_folder_path, file_name)
        
        # Check if the file is a zip archive
        if zipfile.is_zipfile(file_path):
            try:
                # Try extracting the zip file
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(zip_folder_path)
                    print(f"Extracted: {file_name}")
                
                # Remove the original zip file
                os.remove(file_path)
                print(f"Removed: {file_name}")
            
            except zipfile.BadZipFile as e:
                # Log the corrupted file and continue
                print(f"Error: {file_name} is corrupted. Skipping. {e}")
            except Exception as e:
                # Handle any other exceptions
                print(f"Error processing {file_name}: {e}")

# Replace 'your_folder_path' with the path to your folder
your_folder_path = ''
unzip_and_remove(your_folder_path)
