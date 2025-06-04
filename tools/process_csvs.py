import shutil
import glob
import sys
import io
import os

# --- MODIFICATION START ---
# Force stdout and stderr to use UTF-8 and line buffering
# This is crucial for scripts frozen by PyInstaller that print Unicode
# and for ensuring line-by-line output when stdout/stderr are piped.

# Store original encodings for debug messages, if needed later.
# original_stdout_encoding = sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else None
# original_stderr_encoding = sys.stderr.encoding if hasattr(sys.stderr, 'encoding') else None

# Configure stdout
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    # This debug message will go to the *new* stderr, so configure stderr first if strict order is needed
    # or if stderr itself might be problematic.
    print("Successfully reconfigured sys.stdout to UTF-8 with line buffering.", file=sys.stderr)
except Exception as e:
    # Fallback print to original stderr if possible, or just let it be.
    # This error is unlikely if sys.stdout.buffer is standard.
    print(f"Error reconfiguring sys.stdout: {e}", file=sys.stderr) # Tries to use new stderr

# Configure stderr
try:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    # This message now uses the newly configured stderr.
    print("Successfully reconfigured sys.stderr to UTF-8 with line buffering.", file=sys.stderr)
except Exception as e:
    # If this fails, things are tricky. The original stderr might be gone.
    # For robustness in critical apps, one might os.write to stderr fileno 2.
    # print(f"Error reconfiguring sys.stderr: {e}", file=sys.stderr) # This might fail or go to old stderr
    # A more raw attempt if the above print fails:
    try:
        os.write(2, f"CRITICAL: Error reconfiguring sys.stderr: {e}\n".encode('utf-8', 'replace'))
    except:
        pass # give up if even raw write fails
# --- MODIFICATION END ---


def get_application_path():
    """ Get the base path for the application, whether running as script or frozen EXE. """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        application_path = os.path.dirname(sys.executable)
    elif getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return application_path

def process_csv_files():
    script_location_dir = get_application_path()
    # Standard print, will now be line-buffered
    print(f"SCRIPT_DIR_EFFECTIVE: Script/EXE is considered to be running from: {script_location_dir}")

    project_root_dir = os.path.dirname(script_location_dir)
    print(f"EFFECTIVE_ROOT_DIR: Project root directory determined as: {project_root_dir}")

    configurations = [
        {
            "source_path_relative_to_settings": os.path.join("discimg", "csv"),
            "target_dir_name": "discimg_CSV"
        },
        {
            "source_path_relative_to_settings": os.path.join("system", "csv"),
            "target_dir_name": "system_CSV"
        }
    ]

    for config in configurations:
        source_csv_dir = os.path.join(script_location_dir, config["source_path_relative_to_settings"])
        target_root_dir_path = os.path.join(project_root_dir, config["target_dir_name"])

        print(f"\nProcessing configuration for source: {config['source_path_relative_to_settings']}") # Intentionally adding newlines
        print(f"  Source CSV directory (expected): {source_csv_dir}")
        print(f"  Target output directory: {target_root_dir_path}")

        if not os.path.isdir(source_csv_dir):
            print(f"Warning: Source directory {source_csv_dir} not found. Skipping this configuration.")
            continue

        try:
            os.makedirs(target_root_dir_path, exist_ok=True)
            print(f"Ensured target directory exists: {target_root_dir_path}")
        except OSError as e:
            print(f"Error: Could not create target directory {target_root_dir_path}: {e}. Skipping this configuration.")
            continue

        csv_file_pattern = os.path.join(source_csv_dir, "*.csv")
        csv_files = glob.glob(csv_file_pattern)

        if not csv_files:
            print(f"Info: No CSV files found in {source_csv_dir} matching {csv_file_pattern}.")
        else:
            # --- PROGRESS UPDATE MODIFICATION START ---
            total_files = len(csv_files) # NEW: Get the total number of files for progress reporting.
            print(f"Found {total_files} CSV files in {source_csv_dir}.") # MODIFIED: Using total_files variable.
            for i, csv_file_path in enumerate(csv_files): # NEW: Enumerate to get an index for progress reporting.
            # --- PROGRESS UPDATE MODIFICATION END ---
                file_name = os.path.basename(csv_file_path)
                destination_path = os.path.join(target_root_dir_path, file_name)

                # --- PROGRESS UPDATE MODIFICATION START ---
                # NEW: This is the main progress line that will be updated (printed anew for each file).
                print(f"PROGRESS_UPDATE: Processing file {i+1}/{total_files}: {file_name}")
                # NEW: Important to ensure the line is sent immediately, especially if the tool is frozen or output is piped.
                sys.stdout.flush()
                # REMOVED: print(f"  Processing file: {file_name}") - Replaced by PROGRESS_UPDATE
                # --- PROGRESS UPDATE MODIFICATION END ---

                try:
                    shutil.copy2(csv_file_path, destination_path)
                    # --- PROGRESS UPDATE MODIFICATION START ---
                    # REMOVED: print(f"    Copied '{file_name}' to: {destination_path}") - This detail is now part of the progress line or implicit.
                    # --- PROGRESS UPDATE MODIFICATION END ---
                except Exception as e:
                    # --- PROGRESS UPDATE MODIFICATION START ---
                    # MODIFIED: Added newline before error to ensure it doesn't overwrite a progress line if terminal handles \r poorly.
                    print(f"\nError copying {csv_file_path} to {destination_path}: {e}. Skipping this file.")
                    # --- PROGRESS UPDATE MODIFICATION END ---
                    continue

                try:
                    with open(destination_path, 'r', encoding='utf-8') as f_read:
                        lines = f_read.readlines()

                    if not lines:
                        print(f"    Info: '{file_name}' (copied) is empty. No header to remove.")
                    else:
                        modified_lines = lines[1:]
                        with open(destination_path, 'w', encoding='utf-8') as f_write:
                            f_write.writelines(modified_lines)
                        # --- PROGRESS UPDATE MODIFICATION START ---
                        # REMOVED: print(f"    Removed header from copied file: '{file_name}' at {destination_path}") - This detail is now part of the progress line or implicit.
                        # --- PROGRESS UPDATE MODIFICATION END ---

                except Exception as e:
                    print(f"    Error processing header for copied file {destination_path}: {e}. "
                          f"The copied file at target might be as original or partially modified.")
        try:
            if os.path.isdir(source_csv_dir):
                if not os.listdir(source_csv_dir): # Check if directory is empty
                    print(f"Info: Source directory {source_csv_dir} is now empty. It will be kept.")
                else:
                    print(f"Info: Source directory {source_csv_dir} still contains files. It will be kept.")
            # No specific message if it was not found initially, as that's handled above
        except Exception as e: # Broad exception for safety during directory check
            print(f"Notice: Error during final status check of source directory {source_csv_dir}: {e}")


    print("\n--- CSV processing complete. ---") # The initial newline helps clear any potential lingering progress line characters if `end='\r'` was used.

if __name__ == "__main__":
    if not getattr(sys, 'frozen', False):
        print("\n--- Running Mock Directory Setup (because script is not frozen) ---", file=sys.stderr)
        mock_script_location_dir = get_application_path()

        mock_discimg_csv_path = os.path.join(mock_script_location_dir, "discimg", "csv")
        os.makedirs(mock_discimg_csv_path, exist_ok=True)
        print(f"Mock setup: Ensured directory {mock_discimg_csv_path}", file=sys.stderr)

        with open(os.path.join(mock_discimg_csv_path, "file1_disc.csv"), "w", encoding='utf-8') as f:
            f.write("HeaderRow_Disc1\nDataRow1_Disc1\nDataRow2_Disc1\n")
        with open(os.path.join(mock_discimg_csv_path, "file2_disc.csv"), "w", encoding='utf-8') as f:
            f.write("HeaderRow_Disc2\nDataRow1_Disc2\n")

        mock_system_csv_path = os.path.join(mock_script_location_dir, "system", "csv")
        os.makedirs(mock_system_csv_path, exist_ok=True)
        print(f"Mock setup: Ensured directory {mock_system_csv_path}", file=sys.stderr)

        with open(os.path.join(mock_system_csv_path, "file1_sys.csv"), "w", encoding='utf-8') as f:
            f.write("HeaderRow_Sys1\nDataRow1_Sys1\n")

        print("Mock directory structure and sample files created/ensured for testing.", file=sys.stderr)
        print("--- End of Mock Directory Setup ---\n", file=sys.stderr)
    else:
        print("Skipping mock directory setup as script is frozen (running as EXE).", file=sys.stderr)

    print("\nStarting CSV processing from main guard...")
    process_csv_files()
    print("CSV processing finished from main guard.")
