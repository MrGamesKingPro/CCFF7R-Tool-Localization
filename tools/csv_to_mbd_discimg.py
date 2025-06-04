import re # Unused in the final flow, but kept from original
import sys
import io
import os # Make sure os is imported if not already
import pandas as pd

# --- MODIFICATION START ---
# Force stdout and stderr to use UTF-8 and line buffering
# This is crucial for scripts frozen by PyInstaller that print Unicode
# and for ensuring line-by-line output when stdout/stderr are piped.

# Configure stdout
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    # This debug message will go to the *new* stderr, so configure stderr first if strict order is needed
    # or if stderr itself might be problematic.
    # print("Successfully reconfigured sys.stdout to UTF-8 with line buffering.", file=sys.stderr) # Quieted for now
except Exception as e:
    # Fallback print to original stderr if possible, or just let it be.
    # This error is unlikely if sys.stdout.buffer is standard.
    print(f"Error reconfiguring sys.stdout: {e}", file=sys.stderr) # Tries to use new stderr

# Configure stderr
try:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    # This message now uses the newly configured stderr.
    # print("Successfully reconfigured sys.stderr to UTF-8 with line buffering.", file=sys.stderr) # Quieted for now
    if 'sys.stdout' in locals() and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding == 'utf-8':
         print("Successfully reconfigured sys.stdout and sys.stderr to UTF-8 with line buffering.", file=sys.stderr)
    else:
         print("Successfully reconfigured sys.stderr to UTF-8 with line buffering (stdout might have failed).", file=sys.stderr)

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




CHARACTERS_TABLE = {
    b'\x40\x01\x00\x00': '<CHOICE1>',
    b'\x40\x05\x01\x01': '<CHOICE2>',
    b'\x40\x02\x00\x00': '<NL>',
    b'\x40\x03\x00\x00': '<UNK1>',
    b'\x40\x05\x00\x01': '<M-CHOICE1>',
    b'\x40\x04\x00\x02': '<M-CHOICE2>', # Also used as TEXT_ENTRY_TERMINATOR
    b'\x40\x05\x00\x03': '<M-CHOICE3>',
    b'\x40\x05\x00\x04': '<M-CHOICE4>',
    b'\x40\x05\x00\x05': '<M-CHOICE5>',
    b'\x40\x05\x00\x06': '<M-CHOICE6>',
    b'\x40\x05\x00\x07': '<M-CHOICE7>',
    b'\x40\x05\x00\x08': '<M-CHOICE8>',
    b'\x40\x06\x00\x00': '<CROSS-PAD>',
    b'\x40\x07\x00\x00': '<CROSS-SQUARE>',
    b'\x40\x2B\x00\x00': '<VAR1>', b'\x40\x2C\x00\x00': '<VAR2>', b'\x40\x2D\x00\x00': '<VAR3>',
    b'\x40\x11\x00\x00': '<VAR4>', b'\x40\x12\x00\x00': '<VAR5>', b'\x40\x1C\x00\x00': '<VAR6>',
    b'\x40\x0B\x00\x00': '<VAR7>', b'\x40\x17\x00\x00': '<VAR8>', b'\x40\x10\x00\x00': '<VAR9>',
    b'\x40\x0E\x00\x00': '<VAR10>',b'\x40\x15\x00\x00': '<VAR11>',b'\x40\x1B\x00\x00': '<VAR12>',
    b'\x40\x0A\x00\x00': '<VAR13>',b'\x40\x0C\x00\x00': '<VAR14>',b'\x40\x0D\x00\x00': '<VAR15>',
    b'\x40\x08\x00\x00': '<VAR16>',b'\x40\x09\x00\x00': '<VAR17>',b'\x40\x0F\x00\x00': '<VAR18>',
    b'\x40\x13\x00\x00': '<VAR19>',b'\x40\x1A\x00\x00': '<VAR20>',b'\x40\x1D\x00\x00': '<VAR21>',
    b'\x40\x24\x00\x00': '<VAR22>',b'\x40\x36\x00\x00': '<FUNCTION1>',
    b'\x41\x0F\x01\x00': '<KEY-1>', b'\x41\x10\x01\x00': '<KEY-2>',b'\x41\x12\x01\x00': '<KEY-3>',
    b'\x41\xFF\x00\x00': '<KEY-4>', b'\x41\x01\x00\x00': '<KEY-5>',b'\x41\xFE\x00\x00': '<KEY-6>',
    b'\x41\xFD\x00\x00': '<KEY-7>', b'\x41\x00\x00\x00': '<KEY-8>',b'\x41\x17\x01\x00': '<KEY-9>',
    b'\x41\x11\x00\x00': '<KEY-10>',b'\x41\x12\x00\x00': '<KEY-11>',b'\x41\x00\x01\x00': '<KEY-12>',
    b'\x41\x04\x00\x00': '<KEY-13>',b'\x41\x11\x01\x00': '<KEY-14>',b'\x41\x01\x01\x00': '<KEY-15>',
    b'\x41\x03\x01\x00': '<KEY-16>',b'\x41\x04\x01\x00': '<KEY-17>',b'\x41\x02\x01\x00': '<KEY-18>',
    b'\x41\x0D\x01\x00': '<KEY-19>',b'\x41\xC4\x00\x00': '<KEY-20>',b'\x41\x0E\x01\x00': '<KEY-21>',
    b'\x41\x09\x01\x00': '<KEY-22>',b'\x41\x07\x01\x00': '<KEY-23>',b'\x41\x08\x01\x00': '<KEY-24>',
    b'\x41\xFC\x00\x00': '<KEY-25>',b'\x41\x05\x00\x00': '<KEY-26>',b'\x41\xDD\x00\x00': '<KEY-27>',
    b'\x41\xDC\x00\x00': '<KEY-28>',b'\x41\xE7\x00\x00': '<KEY-29>',b'\x41\xE6\x00\x00': '<KEY-30>',
    b'\x41\x21\x00\x00': '<KEY-31>',
    b'\x80\x00\xD7\x00': '×', b'\x80\x00\x1E\x22': '∞', b'\x80\x00\x05\x26': '★',
    b'\x80\x00\x06\x26': '☆', b'\x80\x00\x13\x20': '–',
}
REVERSED_CHARACTERS_TABLE = {v: k for k, v in CHARACTERS_TABLE.items()}
TEXT_ENTRY_TERMINATOR = b'\x40\x04\x00\x00' # <M-CHOICE2> used as a terminator for text entries

def split_byte_string(target_bytes, delimiter_bytes):
    for r in range(0, len(target_bytes), 4):
        if target_bytes[r:r + 4] == delimiter_bytes:
            return [target_bytes[:r + 4], target_bytes[r + 4:]]
    return [target_bytes, b'']

def write_mbd_file(data_list, output_filename, output_directory):
    os.makedirs(output_directory, exist_ok=True)
    output_filepath = os.path.join(output_directory, output_filename)
    try:
        with open(output_filepath, "wb") as f:
            f.write(b''.join(data_list))
        # MODIFIED: Removed per-file success message from here.
        return True
    except Exception as e:
        print(f"Error writing MBD file {output_filepath}: {e}", file=sys.stderr)
        return False

def csv_parse(fil, translation_column_index=2, csv_encoding='utf-8'):
    try:
        if not os.path.exists(fil):
            raise FileNotFoundError(f"CSV file '{fil}' not found.")
        # Ensure dtype=str for consistency
        my_csv = pd.read_csv(fil, header=None, encoding=csv_encoding, keep_default_na=True, dtype=str)
        if translation_column_index >= len(my_csv.columns):
            raise IndexError(f"Translation column index {translation_column_index} is out of bounds for CSV '{fil}'.")
        
        column_data = my_csv.iloc[:, translation_column_index]
        processed_column = []
        # nan_count = 0 # Removed for less verbosity
        # valid_translations_found = 0 # Removed for less verbosity
        for value in column_data:
            if pd.isna(value) or str(value).strip() == "":
                processed_column.append(float('nan'))
                # nan_count += 1
            else:
                processed_column.append(str(value).strip())
                # valid_translations_found +=1
        # MODIFIED: Removed per-file CSV info message.
        # print(f"Info: CSV parsing for '{fil}': Total {len(column_data)}, Valid {valid_translations_found}, Empty/NaN {nan_count}")
        return processed_column
    except Exception as e: 
        # Caller will handle printing specific messages for FileNotFoundError/IndexError
        # For other errors, this general message might be printed by the caller's generic catch block.
        # print(f"Error during CSV parsing of '{fil}': {e}", file=sys.stderr) 
        raise

def cut_str_sem(strin):
    cew, lj, cv, rt = [], '', '', False
    for x in strin:
        if x == '<' and not rt:
            rt = True
            if lj: cew.append(lj); lj = ''
            cv += x
        elif x == '>' and rt:
            cv += x; cew.append(cv); cv = ''; rt = False
        elif rt: cv += x
        else: lj += x
    if lj: cew.append(lj)
    if cv: cew.append(cv) 
    return cew

def parse_to_byt(segmented_str_list):
    byte_parts = []
    for segment in segmented_str_list:
        if segment in REVERSED_CHARACTERS_TABLE:
            byte_parts.append(REVERSED_CHARACTERS_TABLE[segment])
        else:
            processed_char_segment = b''
            for char_in_segment in segment:
                char_bytes_utf32le = char_in_segment.encode('utf_32_le')
                if char_bytes_utf32le[0:2] != b'\x00\x00':
                     processed_char_segment += b'\x80\x00' + char_bytes_utf32le[0:2]
            byte_parts.append(processed_char_segment)
    return b"".join(byte_parts)

def forming_head(byte_string_payload):
    segments, current_segment_start_idx, accumulated_offset = [], 0, 0
    for i in range(0, len(byte_string_payload), 4):
        chunk = byte_string_payload[i:i + 4]
        if chunk == b'\x40\x03\x00\x00' or chunk == TEXT_ENTRY_TERMINATOR: 
            segment_size = (i + 4) - current_segment_start_idx
            segments.append({'size': segment_size, 'offset': accumulated_offset})
            accumulated_offset += segment_size
            current_segment_start_idx = i + 4
    return segments

def to_bytes_str(arr_text_lines):
    output_byte_strings = []
    for text_line_str in arr_text_lines:
        if text_line_str != text_line_str: # Handles float('nan')
            output_byte_strings.append('') # Represents an empty/NaN entry, to be filled by old data
        else:
            segmented_text = cut_str_sem(str(text_line_str))
            parsed_bytes_for_line = parse_to_byt(segmented_text)
            payload_with_terminator = parsed_bytes_for_line + TEXT_ENTRY_TERMINATOR
            
            segment_descriptors = forming_head(payload_with_terminator)
            num_segments = len(segment_descriptors)
            header_parts = [num_segments.to_bytes(4, 'little')]
            base_offset_for_segment_data = 4 + num_segments * 8 # Header: count (4B) + N * (size(4B)+offset(4B))
            for desc in segment_descriptors:
                size_in_words = desc['size'] // 4
                header_parts.append(size_in_words.to_bytes(4, 'little'))
                header_parts.append((desc['offset'] + base_offset_for_segment_data).to_bytes(4, 'little'))
            
            entry_header_bytes = b''.join(header_parts)
            full_entry_bytes = entry_header_bytes + payload_with_terminator
            output_byte_strings.append(full_entry_bytes)
    return output_byte_strings

def comp_item(old_text_items_bytes, new_text_items_bytes_potentially_nan, lang_table_bytes):
    new_table_entries_as_bytes = []
    original_offsets = [int.from_bytes(lang_table_bytes[i:i+4], 'little') for i in range(0, len(lang_table_bytes), 4)]
    final_new_text_items_bytes = list(new_text_items_bytes_potentially_nan) # Make a mutable copy
    current_total_size_difference = 0

    for i in range(len(original_offsets)):
        new_offset_for_current_item = original_offsets[i] + current_total_size_difference
        new_table_entries_as_bytes.append(new_offset_for_current_item.to_bytes(4, 'little'))

        old_item_data = old_text_items_bytes[i]
        new_item_data_candidate = final_new_text_items_bytes[i] 

        # If new_item_data_candidate is '', it means CSV was NaN or empty, so use old data
        if new_item_data_candidate == '': 
            final_new_text_items_bytes[i] = old_item_data
        else:
            # New data exists, combine it with potential trailing metadata from old data
            _original_payload, trailing_metadata = split_byte_string(old_item_data, TEXT_ENTRY_TERMINATOR)
            current_final_new_item_data = new_item_data_candidate + trailing_metadata # new payload + old trailer
            final_new_text_items_bytes[i] = current_final_new_item_data
            
            size_change_for_this_item = len(current_final_new_item_data) - len(old_item_data)
            current_total_size_difference += size_change_for_this_item
            
    return new_table_entries_as_bytes, current_total_size_difference, final_new_text_items_bytes

def read_pr_items(mbd_file_obj, num_items, abs_start_of_block_table, size_of_data_block_for_items):
    item_byte_strings = []
    mbd_file_obj.seek(abs_start_of_block_table, 0) 
    
    offsets_in_table = [int.from_bytes(mbd_file_obj.read(4), 'little') for _ in range(num_items)]
    # The absolute offset to the start of the actual data items for this block
    # is abs_start_of_block_table + (num_items * 4)
    # The size_of_data_block_for_items is the size of *only the item data*, not including the offset table.
    absolute_data_end_offset = abs_start_of_block_table + (num_items * 4) + size_of_data_block_for_items
    file_pointer_after_table_read = mbd_file_obj.tell() # Should be abs_start_of_block_table + num_items * 4

    for i in range(num_items):
        current_item_abs_start_offset = offsets_in_table[i]
        
        # Handle zero-offset entries (typically means empty string or special case)
        if current_item_abs_start_offset == 0 and num_items > 0 : 
             item_byte_strings.append(b'') # Append empty bytes, comp_item will handle it
             continue

        # Determine size of current item
        if i == num_items - 1: # Last item
            current_item_size = absolute_data_end_offset - current_item_abs_start_offset
        else: # Not the last item, calculate size based on next item's offset
            next_item_abs_start_offset_candidate = offsets_in_table[i+1]
            
            # If next item's offset is 0, find the next non-zero offset to determine current item's end
            if next_item_abs_start_offset_candidate == 0:
                actual_next_item_start_offset = 0
                for k_next_nz in range(i + 1, num_items): 
                    if offsets_in_table[k_next_nz] != 0:
                        actual_next_item_start_offset = offsets_in_table[k_next_nz]
                        break
                if actual_next_item_start_offset != 0:
                    current_item_size = actual_next_item_start_offset - current_item_abs_start_offset
                else: # All subsequent items are zero offset, so this item goes to the end of the data block
                    current_item_size = absolute_data_end_offset - current_item_abs_start_offset
            else: # Next item has a non-zero offset
                 current_item_size = next_item_abs_start_offset_candidate - current_item_abs_start_offset

        if current_item_size < 0:
            # Added MBD file path context to warning
            mbd_filename_for_warning = mbd_file_obj.name if hasattr(mbd_file_obj, 'name') else "current MBD"
            print(f"Warning: Negative size ({current_item_size}) for item {i} in '{mbd_filename_for_warning}' at offset {current_item_abs_start_offset} (table starts {abs_start_of_block_table}). Appending empty.", file=sys.stderr)
            item_byte_strings.append(b'')
            continue
            
        mbd_file_obj.seek(current_item_abs_start_offset, 0)
        item_data = mbd_file_obj.read(current_item_size)
        item_byte_strings.append(item_data)

    mbd_file_obj.seek(file_pointer_after_table_read, 0) # Restore file pointer
    return item_byte_strings

def correcting_offsets(data_block_bytes, offset_adjustment, num_entries_in_table):
    if not data_block_bytes or len(data_block_bytes) < num_entries_in_table * 4: # Not enough data for even the table
        return data_block_bytes

    table_size_bytes = num_entries_in_table * 4
    table_part = data_block_bytes[:table_size_bytes]
    data_part = data_block_bytes[table_size_bytes:] # The rest is actual data

    modified_table_offsets = []
    for i in range(0, table_size_bytes, 4):
        original_offset = int.from_bytes(table_part[i:i+4], 'little')
        if original_offset != 0: # Only adjust non-zero offsets
             adjusted_offset = original_offset + offset_adjustment
             modified_table_offsets.append(adjusted_offset.to_bytes(4, 'little'))
        else: # Keep zero offsets as they are
             modified_table_offsets.append(original_offset.to_bytes(4, 'little'))
             
    return b''.join(modified_table_offsets) + data_part

def process_single_mbd_csv_pair(mbd_file_path, csv_file_path, output_dir_for_this_mbd, output_mbd_filename):
    # MODIFIED: Removed per-file "Processing..." message
    try:
        with open(mbd_file_path, "rb") as mbd_file:
            magic_number = mbd_file.read(4)
            if magic_number != b'\x4D\x42\x44\x00':
                print(f"Warning: MBD file '{mbd_file_path}' has incorrect magic number ({magic_number!r}). Skipping.", file=sys.stderr)
                return False
            
            count_items = int.from_bytes(mbd_file.read(4), "little")
            mbd_file.seek(28); dssx_flag = mbd_file.read(4) # Offset 28, size 4
            mbd_file.seek(36); lef_flag = mbd_file.read(4)  # Offset 36, size 4
            mbd_file.seek(8) # Reposition after count_items to start of item definition block
            
            # Determine item definition size and skip to end of item definitions
            if dssx_flag in (b'\x00\x00\x00\x00', b'\x01\x00\x00\x00', b'\x03\x00\x00\x00'): # DSSX present
                mbd_file.seek(count_items * 44, 1) # Skip item definitions (44 bytes each)
            elif lef_flag == b'\xff\xff\xff\xff': # LEF structure
                mbd_file.seek(count_items * 32, 1) # Skip item definitions (32 bytes each)
            else: # Default structure
                mbd_file.seek(count_items * 28, 1) # Skip item definitions (28 bytes each)
            
            size_of_main_mbd_header_section = mbd_file.tell() # Current position is end of header / item defs
            mbd_file.seek(0); main_mbd_header_bytes = mbd_file.read(size_of_main_mbd_header_section)

            try:
                list_of_strings_from_csv = csv_parse(csv_file_path)
            except FileNotFoundError: # csv_parse re-raises this
                print(f"Error: CSV file '{csv_file_path}' not found for MBD '{mbd_file_path}'. Skipping.", file=sys.stderr)
                return False
            except IndexError as e: # csv_parse re-raises this
                 print(f"Error: CSV column issue for '{csv_file_path}'. {e}. Skipping MBD '{mbd_file_path}'.", file=sys.stderr)
                 return False
            except Exception as e: # Other csv_parse errors
                 print(f"Error parsing CSV '{csv_file_path}' for MBD '{mbd_file_path}': {e}. Skipping.", file=sys.stderr)
                 return False

            if len(list_of_strings_from_csv) != count_items:
                 print(f"Warning: CSV rows ({len(list_of_strings_from_csv)}) != MBD items ({count_items}) for '{mbd_file_path}'. Adjusting CSV data to match MBD item count.", file=sys.stderr)
                 if len(list_of_strings_from_csv) < count_items:
                     list_of_strings_from_csv.extend([float('nan')] * (count_items - len(list_of_strings_from_csv)))
                 else: # CSV has more rows than MBD items
                     list_of_strings_from_csv = list_of_strings_from_csv[:count_items]
            
            new_text_byte_data_for_lang2_candidates = to_bytes_str(list_of_strings_from_csv)
            
            # Read language table absolute offsets (10 languages, 4 bytes each = 40 bytes)
            # File pointer is currently at the start of this table
            lang_table_absolute_offsets_bytes = [mbd_file.read(4) for _ in range(10)]
            lang_data_blocks = [] # Store byte content of each language block

            for i in range(10): # For each language slot
                start_abs = int.from_bytes(lang_table_absolute_offsets_bytes[i], 'little')
                
                if start_abs == 0: # This language slot is not used or points to nothing
                    # If it's not the first language and it's zero, assume subsequent ones might also be zero
                    # or this is the end of used language blocks.
                    # The original logic would append empty blocks for the rest.
                    lang_data_blocks.append(b'')
                    if i > 0: # Optimization: if a non-first lang block is 0, assume rest are too (or fill with empty)
                        # Original logic: for _ in range(i, 10): lang_data_blocks.append(b''). This seems safer.
                        # This loop will continue and append b'' for remaining slots if their start_abs is 0.
                        continue 


                # Determine end offset for this language block
                end_abs_target = 0
                if i + 1 < 10: # If there is a next language entry in the table
                    end_abs_target = int.from_bytes(lang_table_absolute_offsets_bytes[i+1], 'little')
                
                if end_abs_target == 0: # Next lang offset is 0, or this is the last lang entry
                    actual_end_abs = 0
                    # Find the next non-zero language offset to determine current block's end
                    for k in range(i + 1, 10):
                        next_nz_offset = int.from_bytes(lang_table_absolute_offsets_bytes[k], 'little')
                        if next_nz_offset != 0:
                            actual_end_abs = next_nz_offset
                            break
                    if actual_end_abs == 0: # No more non-zero lang offsets, this block goes to EOF
                        current_pos_before_eof_seek = mbd_file.tell()
                        mbd_file.seek(0, 2) # Seek to end of file
                        actual_end_abs = mbd_file.tell()
                        mbd_file.seek(current_pos_before_eof_seek) # Restore pointer
                    end_abs_target = actual_end_abs
                
                size = end_abs_target - start_abs if start_abs > 0 and start_abs <= end_abs_target else 0

                if size > 0 :
                    mbd_file.seek(start_abs) # Go to the start of this language block's data
                    lang_data_blocks.append(mbd_file.read(size))
                else:
                    lang_data_blocks.append(b'') # Append empty if size is zero or invalid

            original_lang2_block_bytes = lang_data_blocks[1] # Lang 2 is English (index 1)
            offset_table_size_for_lang2 = count_items * 4 # Each item has a 4-byte offset in the table

            if len(original_lang2_block_bytes) < offset_table_size_for_lang2 and count_items > 0:
                print(f"Error: Lang2 block in '{mbd_file_path}' is too small for its offset table (expected at least {offset_table_size_for_lang2} bytes, got {len(original_lang2_block_bytes)}). Skipping.", file=sys.stderr)
                return False

            original_lang2_offset_table_bytes = original_lang2_block_bytes[:offset_table_size_for_lang2]
            # Size of the actual text data portion for Lang2 (excluding its own offset table)
            size_of_lang2_data_portion = len(original_lang2_block_bytes) - offset_table_size_for_lang2
            
            abs_start_offset_lang2_block_table = int.from_bytes(lang_table_absolute_offsets_bytes[1], 'little')
            
            if count_items > 0 and abs_start_offset_lang2_block_table > 0:
                # Pass the MBD file object to read_pr_items
                original_lang2_text_items_as_bytelist = read_pr_items(mbd_file, count_items, abs_start_offset_lang2_block_table, size_of_lang2_data_portion)
            else: # No items or Lang2 block doesn't exist
                original_lang2_text_items_as_bytelist = [b''] * count_items

            new_lang2_item_offset_table_entries, total_size_change_in_lang2, final_new_lang2_byte_items = comp_item(
                original_lang2_text_items_as_bytelist, 
                new_text_byte_data_for_lang2_candidates, 
                original_lang2_offset_table_bytes
            )
            
            rebuilt_lang2_block_bytes = b''.join(new_lang2_item_offset_table_entries) + b''.join(final_new_lang2_byte_items)

            # Adjust main language table offsets for languages *after* Lang2
            new_main_lang_table_offsets_bytes_list = list(lang_table_absolute_offsets_bytes)
            for i in range(2, 10): # Start from Lang3 (index 2)
                original_offset = int.from_bytes(new_main_lang_table_offsets_bytes_list[i], 'little')
                if original_offset != 0: # Only adjust if offset is non-zero
                    new_main_lang_table_offsets_bytes_list[i] = (original_offset + total_size_change_in_lang2).to_bytes(4, 'little')
            
            final_mbd_parts = [main_mbd_header_bytes, b''.join(new_main_lang_table_offsets_bytes_list)]
            final_mbd_parts.append(lang_data_blocks[0]) # Lang1 (Japanese) unchanged
            final_mbd_parts.append(rebuilt_lang2_block_bytes) # Modified Lang2 (English)

            # Append other language blocks, adjusting their internal offsets if they exist
            for i in range(2, 10): # Lang3 onwards
                block = lang_data_blocks[i]
                if len(block) >= count_items * 4 and count_items > 0: # If block has at least an offset table
                    # This assumes other language blocks also have item structures that need offset adjustments.
                    # The offset_adjustment here is total_size_change_in_lang2, which affects the *start* of these blocks.
                    # The internal offsets within these blocks are relative to their own start, so they don't need
                    # correcting_offsets based on total_size_change_in_lang2.
                    # The original correcting_offsets was intended for a block whose data items had changed size.
                    # Here, we are rebuilding the file: Header, MainLangTable, Lang1, Lang2_new, Lang3, ...
                    # The start offsets in MainLangTable for Lang3 onwards are already adjusted.
                    # The internal structure of Lang3, Lang4, etc., should be preserved as read.
                    # The original `correcting_offsets(block, total_size_change_in_lang2, count_items)` call
                    # would be incorrect here, as `total_size_change_in_lang2` is not an adjustment *within* these blocks.
                    final_mbd_parts.append(block)
                else:
                    final_mbd_parts.append(block) # Append as is (e.g. empty or too small for table)
            
            return write_mbd_file(final_mbd_parts, output_mbd_filename, output_dir_for_this_mbd)

    except FileNotFoundError: # MBD file not found
        print(f"Error: MBD file not found at {mbd_file_path}. Skipping.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Unexpected error processing MBD {mbd_file_path}: {e}. Skipping.", file=sys.stderr)
        import traceback; traceback.print_exc(file=sys.stderr)
        return False


def main_entrypoint(root_mbd_path, root_csv_path, root_output_dir):
    if os.path.isdir(root_mbd_path):
        # --- Batch Mode ---
        print(f"Batch processing MBDs from: {root_mbd_path}") 
        print(f"Looking for corresponding CSVs in/under: {root_csv_path}")
        print(f"Outputting modified MBDs to subdirectories under: {root_output_dir}")
        
        if not os.path.isdir(root_csv_path):
            print(f"Error: CSV input path '{root_csv_path}' must be a directory for batch mode. Aborting.", file=sys.stderr)
            return

        # --- File Discovery Phase ---
        files_to_process = []
        for dirpath, _, filenames in os.walk(root_mbd_path):
            for mbd_filename in filter(lambda f: f.lower().endswith(".mbd"), filenames):
                mbd_full_path = os.path.join(dirpath, mbd_filename)
                csv_filename = os.path.splitext(mbd_filename)[0] + ".csv"
                
                relative_mbd_dir_from_root = os.path.relpath(dirpath, root_mbd_path)
                csv_full_path_mirrored = os.path.join(root_csv_path, relative_mbd_dir_from_root, csv_filename)
                csv_full_path_flat = os.path.join(root_csv_path, csv_filename)

                csv_full_path_to_use = None
                is_mbd_in_subdir = (relative_mbd_dir_from_root != '.' and relative_mbd_dir_from_root != '')

                if is_mbd_in_subdir:
                    if os.path.exists(csv_full_path_mirrored):
                        csv_full_path_to_use = csv_full_path_mirrored
                    elif os.path.exists(csv_full_path_flat): # Fallback to flat if mirrored fails FOR SUBDIR
                        csv_full_path_to_use = csv_full_path_flat
                else: # MBD in root of mbd_path
                    if os.path.exists(csv_full_path_flat):
                        csv_full_path_to_use = csv_full_path_flat
                
                if not csv_full_path_to_use:
                    # This warning is about missing CSVs before processing starts, printed once per missing CSV.
                    # It doesn't interrupt the progress bar later.
                    print(f"Warning: CSV for MBD '{mbd_full_path}' not found. Tried mirrored path '{csv_full_path_mirrored}' and flat path '{csv_full_path_flat}'. This MBD will be skipped.", file=sys.stderr)
                    continue # Skip this MBD file
                
                # Construct output directory preserving relative structure
                output_dir_for_mbd = os.path.join(root_output_dir, relative_mbd_dir_from_root)
                files_to_process.append((mbd_full_path, csv_full_path_to_use, output_dir_for_mbd, mbd_filename))

        total_files_to_attempt = len(files_to_process)
        if total_files_to_attempt == 0:
            print("No MBD files with corresponding CSVs found to process.")
            return

        # --- Processing Phase ---
        successful_processing_count = 0
        print(f"Found {total_files_to_attempt} MBD files with matching CSVs to process...")
        for i, (mbd_full_path, csv_full_path_to_use, output_dir_for_mbd, mbd_filename) in enumerate(files_to_process):
            # Ensure filename part of progress bar is not excessively long visually
            display_filename = (mbd_filename[:57] + '...') if len(mbd_filename) > 60 else mbd_filename
            progress_message = f"\rProcessing file {i+1}/{total_files_to_attempt}: {display_filename.ljust(60)}"
            sys.stdout.write(progress_message)
            sys.stdout.flush()
            
            try:
                if process_single_mbd_csv_pair(mbd_full_path, csv_full_path_to_use, output_dir_for_mbd, mbd_filename):
                    successful_processing_count += 1
                else:
                    # Error/warning already printed to stderr by process_single_mbd_csv_pair which returned False.
                    # The progress bar continues to the next file.
                    # No explicit newline needed here as stderr is separate.
                    pass 
            except Exception as e:
                # This catches unexpected errors from process_single_mbd_csv_pair itself (if it didn't return False)
                sys.stdout.write("\n") # Move off the progress line before printing error to stderr
                sys.stdout.flush()
                print(f"Critical error during batch processing of {mbd_filename}: {e}. File skipped.", file=sys.stderr)
                import traceback; traceback.print_exc(file=sys.stderr)

        sys.stdout.write("\n") # Newline after progress bar is complete
        sys.stdout.flush()
        print(f"\nBatch processing complete. Successfully processed {successful_processing_count} out of {total_files_to_attempt} MBD files.")
    
    elif os.path.isfile(root_mbd_path):
        # --- Single File Mode ---
        print(f"Single file processing: MBD: {root_mbd_path}, CSV: {root_csv_path}")
        if not os.path.isfile(root_csv_path):
            print(f"Error: CSV input '{root_csv_path}' must be a file for single MBD mode. Aborting.", file=sys.stderr)
            return
        
        output_filename = os.path.basename(root_mbd_path)
        # For single file, root_output_dir is the direct directory for the output file
        print(f"Outputting modified MBD to: {os.path.join(root_output_dir, output_filename)}")

        if process_single_mbd_csv_pair(root_mbd_path, root_csv_path, root_output_dir, output_filename):
            print(f"Successfully processed and wrote: {output_filename}")
        else:
            # Errors would have been printed by process_single_mbd_csv_pair
            print(f"Failed to process MBD: {output_filename}. See error messages above for details.", file=sys.stderr)
    else:
        print(f"Error: MBD input '{root_mbd_path}' not found or not a file/directory.", file=sys.stderr)

if __name__ == '__main__':
    # --- Path Setup ---
    def get_project_root():
        if getattr(sys, 'frozen', False): # Running as a frozen executable
            executable_path = sys.executable
            tools_dir = os.path.dirname(executable_path)
            project_root = os.path.dirname(tools_dir)
        else: # Running as a normal script
            script_path = os.path.abspath(__file__)
            tools_dir = os.path.dirname(script_path)
            project_root = os.path.dirname(tools_dir)
        return project_root

    PROJECT_ROOT = get_project_root()
    
    # Define paths relative to PROJECT_ROOT
    abs_inp_mbd = os.path.normpath(os.path.join(PROJECT_ROOT, "tools", "discimg", "mbd_ecx"))
    abs_inp_csv = os.path.normpath(os.path.join(PROJECT_ROOT, "discimg_CSV"))
    # Output MBDs will mirror the structure of input MBDs, rooted in this output directory
    abs_out_dir = os.path.normpath(os.path.join(PROJECT_ROOT, "tools", "discimg", "mbd_ecx_modified")) # Changed output path
    
    print(f"--- Using Resolved Paths (csv_to_mbd_discimg) ---")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"MBD Input Path:  {abs_inp_mbd}")
    print(f"CSV Input Path: {abs_inp_csv}")
    print(f"Base Output Dir:   {abs_out_dir}") # This is where the mirrored structure will be created
    print(f"-------------------------------------------------")

    if not os.path.exists(abs_inp_mbd):
        print(f"Error: MBD input path '{abs_inp_mbd}' does not exist. Aborting.", file=sys.stderr); sys.exit(1)
    if not os.path.exists(abs_inp_csv):
        print(f"Error: CSV input path '{abs_inp_csv}' does not exist. Aborting.", file=sys.stderr); sys.exit(1)

    # Ensure the base output directory exists. Subdirectories will be created as needed.
    os.makedirs(abs_out_dir, exist_ok=True)
    
    main_entrypoint(abs_inp_mbd, abs_inp_csv, abs_out_dir)
