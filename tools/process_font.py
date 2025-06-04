import os
import shutil
import pathlib
import sys
import io
import logging # Import logging

# --- UTF-8 Setup (Good as is) ---
# ... (your UTF-8 setup code) ...

# --- Global Path Configuration ---
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (frozen by PyInstaller)
    _executable_path = pathlib.Path(sys.executable).resolve() # Full path to the .exe

    # Typical PyInstaller outputs:
    # 1. One-dir: MyProject/dist/script_name/script_name.exe
    #    Here, _executable_path.parent is MyProject/dist/script_name/
    #    PROJECT_ROOT should be _executable_path.parent.parent.parent (to get MyProject/)
    # 2. One-file: MyProject/dist/script_name.exe
    #    Here, _executable_path.parent is MyProject/dist/
    #    PROJECT_ROOT should be _executable_path.parent.parent (to get MyProject/)

    # Let's try to be robust:
    # Assume 'dist' is always a direct child of MyProject
    if _executable_path.parent.name.lower() == 'dist': # Case: MyProject/dist/script_name.exe
        PROJECT_ROOT = _executable_path.parent.parent
    elif _executable_path.parent.parent.name.lower() == 'dist': # Case: MyProject/dist/script_name_folder/script_name.exe
        PROJECT_ROOT = _executable_path.parent.parent.parent
    else:
        # Fallback: If not in a 'dist' structure, maybe the .exe is directly in MyProject/ or MyProject/some_folder/
        # This could happen if you move the .exe manually.
        # Try to find 'tools' and 'font' relative to some common parent directories.
        potential_pr_1 = _executable_path.parent # Assume exe is in MyProject
        potential_pr_2 = _executable_path.parent.parent # Assume exe is in MyProject/some_subfolder

        if (potential_pr_1 / "tools").is_dir() and (potential_pr_1 / "font").is_dir():
            PROJECT_ROOT = potential_pr_1
        elif (potential_pr_2 / "tools").is_dir() and (potential_pr_2 / "font").is_dir():
            PROJECT_ROOT = potential_pr_2
        else:
            # Last resort: could be 3 levels up for dist/appname/app.exe
            PROJECT_ROOT = _executable_path.parent.parent.parent
            # Add a warning here if you use logging
            print(f"Warning: Could not definitively locate PROJECT_ROOT. Assuming: {PROJECT_ROOT}. "
                  f"Ensure 'tools' and 'font' are in the correct relative locations.", file=sys.stderr)

    SCRIPT_PATH_INFO = _executable_path # For informational purposes
    tools_DIR = PROJECT_ROOT / "tools"  # Source pakchunks are expected in MyProject/tools/
else:
    # If run as a normal Python script (.py)
    SCRIPT_PATH_INFO = pathlib.Path(__file__).resolve() # MyProject/tools/process_font.py
    tools_DIR = SCRIPT_PATH_INFO.parent                 # MyProject/tools/
    PROJECT_ROOT = tools_DIR.parent                     # MyProject/

# --- Setup Logging ---
# Place this AFTER PROJECT_ROOT is defined, so logs can go into MyProject if desired.
# Or place it next to the EXE / Script.

# Determine log file path
if getattr(sys, 'frozen', False):
    log_file_path = pathlib.Path(sys.executable).parent / "app_debug.log"
else:
    log_file_path = SCRIPT_PATH_INFO.parent / "app_debug.log" # Next to the script

try:
    # Ensure the directory for the log file exists (especially for frozen apps in protected areas, though usually not an issue for app's own dir)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_file_path,
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
        encoding='utf-8',
        filemode='w' # Overwrite log each time, or 'a' to append
    )
    logging.info("Logging initialized.")
except Exception as e:
    print(f"Error initializing logging: {e}", file=sys.stderr)
    # Fallback if logging can't be set up (e.g., permissions)
    logging.basicConfig(level=logging.CRITICAL) # Effectively disable logging output to file


# --- Replace print() with logging.info() or logging.error() throughout your script ---
# Example:
# print("--- Starting: Folder Creation and PKG/BIN File Copying ---")
# becomes:
# logging.info("--- Starting: Folder Creation and PKG/BIN File Copying ---")
#
# print(f"Error: Source file not found: {source_file1_path}")
# becomes:
# logging.error(f"Error: Source file not found: {source_file1_path}")


# --- Part 1: Logic from Createfplder.py ===

def create_folders_and_copy_pkgs():
    logging.info("--- Starting: Folder Creation and PKG/BIN File Copying ---")
    logging.info(f"Using PROJECT_ROOT: {PROJECT_ROOT}")
    logging.info(f"Using tools_DIR for source pakchunks: {tools_DIR}")

    common_sub_path_parts = ("CCFF7R", "Content", "PSP", "Discimg")
    source_folder1_name = "pakchunk1-WindowsNoEditor"
    file1_name = "discimg.pkg"
    source_file1_path = tools_DIR / source_folder1_name / pathlib.Path(*common_sub_path_parts) / file1_name

    source_folder2_name = "pakchunk2-WindowsNoEditor"
    file2_name = "system.bin"
    source_file2_path = tools_DIR / source_folder2_name / pathlib.Path(*common_sub_path_parts) / file2_name

    destination_folder_name = "pakchunkMrGamesKingPro"
    destination_target_dir = PROJECT_ROOT / destination_folder_name / pathlib.Path(*common_sub_path_parts)

    if not PROJECT_ROOT.exists() or not PROJECT_ROOT.is_dir():
        logging.error(f"PROJECT_ROOT '{PROJECT_ROOT}' does not exist or is not a directory. Cannot proceed.")
        return False
    if not tools_DIR.exists() or not tools_DIR.is_dir():
        logging.error(f"tools_DIR '{tools_DIR}' for source data does not exist or is not a directory. Cannot proceed.")
        return False

    try:
        destination_target_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Destination directory created/ensured: {destination_target_dir}")
    except Exception as e:
        logging.error(f"Error creating destination directory '{destination_target_dir}': {e}")
        return False

    destination_file1_path = destination_target_dir / file1_name
    destination_file2_path = destination_target_dir / file2_name

    try:
        if source_file1_path.exists():
            logging.info(f"Copying '{source_file1_path}'\n  to    '{destination_file1_path}'...")
            shutil.copy2(source_file1_path, destination_file1_path)
            logging.info(f"Successfully copied {file1_name}")
        else:
            logging.error(f"Source file not found: {source_file1_path}")

        if source_file2_path.exists():
            logging.info(f"Copying '{source_file2_path}'\n  to    '{destination_file2_path}'...")
            shutil.copy2(source_file2_path, destination_file2_path)
            logging.info(f"Successfully copied {file2_name}")
        else:
            logging.error(f"Source file not found: {source_file2_path}")
            
        logging.info("PKG/BIN file copying process completed.")
        return True

    except Exception as e:
        logging.error(f"An error occurred during PKG/BIN copying: {e}", exc_info=True)
        return False

# === Part 2: Logic from cahngefont.py ===
NEW_FONT_NAME_1 = "FOT-SKIPSTD-B.ufont"
NEW_FONT_NAME_2 = "FOT-UDKAKUGO_LARGEPRO-M.ufont"
TARGET_FONT_SUBPATH_PARTS = ["pakchunkMrGamesKingPro", "CCFF7R", "Content", "UI", "01_Common", "00_Font"]

def change_font_files():
    logging.info("--- Starting: Font Changing Process ---")
    logging.info(f"Using PROJECT_ROOT: {PROJECT_ROOT}")

    source_font_dir = PROJECT_ROOT / "font"

    if not source_font_dir.is_dir():
        logging.error(f"Source font directory not found at '{source_font_dir}'")
        logging.info("Please create the 'font' directory in the project root and place a font file inside it.")
        return False

    font_files_found = []
    common_font_extensions = ['*.ttf', '*.otf', '*.woff', '*.woff2', '*.ufont']
    for ext_pattern in common_font_extensions:
        font_files_found.extend(list(source_font_dir.glob(ext_pattern)))
    
    if not font_files_found:
        logging.error(f"No font files (e.g., .ttf, .otf) found in '{source_font_dir}'.")
        logging.info("Please place a font file in that directory.")
        return False
    
    source_font_path = font_files_found[0]

    if len(font_files_found) > 1:
        logging.warning(f"Multiple font files found in '{source_font_dir}':")
        for f_path in font_files_found:
            logging.warning(f"  - {f_path.name}")
        logging.warning(f"Using the first one found: '{source_font_path.name}'")
    else:
        logging.info(f"Source font found: '{source_font_path}'")

    target_font_dir = PROJECT_ROOT
    for part in TARGET_FONT_SUBPATH_PARTS:
        target_font_dir = target_font_dir / part
    
    try:
        target_font_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Target font directory ensured: '{target_font_dir}'")
    except Exception as e:
        logging.error(f"Error creating target font directory '{target_font_dir}': {e}")
        return False

    destination_path_1 = target_font_dir / NEW_FONT_NAME_1
    destination_path_2 = target_font_dir / NEW_FONT_NAME_2

    try:
        logging.info(f"Attempting to copy '{source_font_path.name}' to:")
        shutil.copy2(source_font_path, destination_path_1)
        logging.info(f"  Successfully copied and renamed to: '{destination_path_1}'")

        shutil.copy2(source_font_path, destination_path_2)
        logging.info(f"  Successfully copied and renamed to: '{destination_path_2}'")
        
        logging.info("Font processing completed successfully!")
        logging.info(f"The duplicated and renamed fonts are now in: '{target_font_dir}'")
        return True

    except FileNotFoundError:
        logging.error(f"Source font file '{source_font_path}' not found during copy.", exc_info=True)
    except PermissionError:
        logging.error(f"Permission denied. Check file/folder permissions for '{source_font_path}' or '{target_font_dir}'.", exc_info=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred during font processing: {e}", exc_info=True)
    return False

# === Main Execution Block ===
if __name__ == "__main__":
    logging.info(f"Script/Executable running from: {SCRIPT_PATH_INFO}")
    logging.info(f"Project Root determined as: {PROJECT_ROOT}")
    logging.info(f"tools_DIR determined as: {tools_DIR}")

    step1_success = create_folders_and_copy_pkgs()

    if step1_success:
        logging.info("Step 1 completed successfully.")
        step2_success = change_font_files()
        if step2_success:
            logging.info("Step 2 completed successfully.")
            logging.info("All operations finished successfully!")
        else:
            logging.error("Step 2 failed. Font processing encountered an error.")
    else:
        logging.error("Step 1 failed. PKG/BIN file copying encountered an error. Skipping font processing.")

    logging.info("Script execution finished.")
    print("Script execution finished. Check app_debug.log for details.") # Keep a console print

