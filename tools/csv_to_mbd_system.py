# import csv # Not directly used in the snippet, but pandas uses it for CSV parsing
import os
import re
import sys
import pandas as pd
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
    # print("Successfully reconfigured sys.stdout to UTF-8 with line buffering.", file=sys.stderr) # Less verbose
except Exception as e:
    # Fallback print to original stderr if possible, or just let it be.
    # This error is unlikely if sys.stdout.buffer is standard.
    print(f"Error reconfiguring sys.stdout: {e}", file=sys.stderr) # Tries to use new stderr

# Configure stderr
try:
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    # This message now uses the newly configured stderr.
    print("Successfully reconfigured sys.stdout and sys.stderr to UTF-8 with line buffering.", file=sys.stderr) # Combined message
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
    b'\x40\x04\x00\x02': '<M-CHOICE2>', # Also used as a general entry terminator
    b'\x40\x05\x00\x03': '<M-CHOICE3>',
    b'\x40\x05\x00\x04': '<M-CHOICE4>',
    b'\x40\x05\x00\x05': '<M-CHOICE5>',
    b'\x40\x05\x00\x06': '<M-CHOICE6>',
    b'\x40\x05\x00\x07': '<M-CHOICE7>',
    b'\x40\x05\x00\x08': '<M-CHOICE8>',
    b'\x40\x06\x00\x00': '<CROSS-PAD>',
    b'\x40\x07\x00\x00': '<CROSS-SQUARE>',
    b'\x40\x2B\x00\x00': '<VAR1>',
    b'\x40\x2C\x00\x00': '<VAR2>',
    b'\x40\x2D\x00\x00': '<VAR3>',
    b'\x40\x11\x00\x00': '<VAR4>',
    b'\x40\x12\x00\x00': '<VAR5>',
    b'\x40\x1C\x00\x00': '<VAR6>',
    b'\x40\x0B\x00\x00': '<VAR7>',
    b'\x40\x17\x00\x00': '<VAR8>',
    b'\x40\x10\x00\x00': '<VAR9>',
    b'\x40\x0E\x00\x00': '<VAR10>',
    b'\x40\x15\x00\x00': '<VAR11>',
    b'\x40\x1B\x00\x00': '<VAR12>',
    b'\x40\x0A\x00\x00': '<VAR13>',
    b'\x40\x0C\x00\x00': '<VAR14>',
    b'\x40\x0D\x00\x00': '<VAR15>',
    b'\x40\x08\x00\x00': '<VAR16>',
    b'\x40\x09\x00\x00': '<VAR17>',
    b'\x40\x0F\x00\x00': '<VAR18>',
    b'\x40\x13\x00\x00': '<VAR19>',
    b'\x40\x1A\x00\x00': '<VAR20>',
    b'\x40\x1D\x00\x00': '<VAR21>',
    b'\x40\x24\x00\x00': '<VAR22>',
    b'\x40\x36\x00\x00': '<FUNCTION1>',
    b'\x41\x0F\x01\x00': '<KEY-1>',
    b'\x41\x10\x01\x00': '<KEY-2>',
    b'\x41\x12\x01\x00': '<KEY-3>',
    b'\x41\xFF\x00\x00': '<KEY-4>',
    b'\x41\x01\x00\x00': '<KEY-5>',
    b'\x41\xFE\x00\x00': '<KEY-6>',
    b'\x41\xFD\x00\x00': '<KEY-7>',
    b'\x41\x00\x00\x00': '<KEY-8>',
    b'\x41\x17\x01\x00': '<KEY-9>',
    b'\x41\x11\x00\x00': '<KEY-10>',
    b'\x41\x12\x00\x00': '<KEY-11>',
    b'\x41\x00\x01\x00': '<KEY-12>',
    b'\x41\x04\x00\x00': '<KEY-13>',
    b'\x41\x11\x01\x00': '<KEY-14>',
    b'\x41\x01\x01\x00': '<KEY-15>',
    b'\x41\x03\x01\x00': '<KEY-16>',
    b'\x41\x04\x01\x00': '<KEY-17>',
    b'\x41\x02\x01\x00': '<KEY-18>',
    b'\x41\x0D\x01\x00': '<KEY-19>',
    b'\x41\xC4\x00\x00': '<KEY-20>',
    b'\x41\x0E\x01\x00': '<KEY-21>',
    b'\x41\x09\x01\x00': '<KEY-22>',
    b'\x41\x07\x01\x00': '<KEY-23>',
    b'\x41\x08\x01\x00': '<KEY-24>',
    b'\x41\xFC\x00\x00': '<KEY-25>',
    b'\x41\x05\x00\x00': '<KEY-26>',
    b'\x41\xDD\x00\x00': '<KEY-27>',
    b'\x41\xDC\x00\x00': '<KEY-28>',
    b'\x41\xE7\x00\x00': '<KEY-29>',
    b'\x41\xE6\x00\x00': '<KEY-30>',
    b'\x41\x21\x00\x00': '<KEY-31>',
    b'\x80\x00\xD7\x00': '×',
    b'\x80\x00\x1E\x22': '∞',
    b'\x80\x00\x05\x26': '★',
    b'\x80\x00\x06\x26': '☆',
    b'\x80\x00\x13\x20': '–',
}
ENTRY_TERMINATOR_BYTES = b'\x40\x04\x00\x00' # Corresponds to '<M-CHOICE2>' in CHARACTERS_TABLE

def split_byte_string(target, value):
    arra = []
    count = int(len(target))
    for r in range(0, count, 4):
        segxx = target[r:r + 4]
        if segxx == value:
            arra.append(target[:r + 4])
            arra.append(target[r + 4:])
            return arra
    return arra

def write_mbd_data(mbd_data_list, output_filepath):
    output_dir = os.path.dirname(output_filepath)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_filepath, "wb") as mbd_out_file:
        mbd_out_file.write(b''.join(mbd_data_list))

def csv_parse(fil, translation_column_index=2, csv_encoding='utf-8'):
    try:
        my_csv = pd.read_csv(fil, header=None, encoding=csv_encoding, keep_default_na=True)

        if translation_column_index >= len(my_csv.columns):
            raise IndexError(f"Translation column index {translation_column_index} is out of bounds "
                             f"for CSV file '{fil}' with {len(my_csv.columns)} columns.")

        column_data = my_csv[translation_column_index]
        processed_column = []
        # nan_count = 0 # No longer printing these details per file
        # valid_translations_found = 0
        for i, value in enumerate(column_data):
            if pd.isna(value):
                processed_column.append(float('nan'))
                # nan_count += 1
            else:
                processed_column.append(str(value).strip())
                # if str(value).strip():
                #     valid_translations_found +=1
        
        # print(f"Info: CSV parsing for '{fil}':") # Removed verbose output
        # print(f"  - Total rows processed: {len(column_data)}")
        # print(f"  - Valid translations found: {valid_translations_found}")
        # print(f"  - Empty/NaN translations (original game text will be used): {nan_count}")
        return processed_column

    except pd.errors.EmptyDataError:
        print(f"Error: CSV file '{fil}' is empty.", file=sys.stderr)
        raise
    except IndexError as e:
        print(f"Error accessing column in CSV '{fil}': {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"An unexpected error occurred during CSV parsing of '{fil}': {e}", file=sys.stderr)
        raise

def cut_str_sem(strin):
    cew = []
    lj = ''
    cv = ''
    rt = False
    for x_char in strin:
        if x_char == '<' or rt:
            rt = True
            if lj != "":
                cew.append(lj)
                lj = ''
            cv += x_char
            if x_char == '>':
                rt = False
                cew.append(cv)
                cv = ''
        else:
            lj += x_char
    if lj:
        cew.append(lj)
    if cv:
        cew.append(cv)
    return cew

def parse_to_byt(bt_str_segments):
    lnijp_byte_list = []
    for l_segment in bt_str_segments:
        if l_segment in CHARACTERS_TABLE.values():
            sgrr_tag_bytes = [k for k, v in CHARACTERS_TABLE.items() if v == l_segment][0]
            lnijp_byte_list.append(sgrr_tag_bytes)
        else:
            opl_encoded_text = l_segment.encode('utf-16-le')
            oj_processed_bytes = []
            for v_idx in range(0, len(opl_encoded_text), 2):
                char_bytes_pair = opl_encoded_text[v_idx:v_idx + 2]
                oj_processed_bytes.append(b'\x80\x00')
                oj_processed_bytes.append(char_bytes_pair)
            lnijp_byte_list.append(b"".join(oj_processed_bytes))
    return b"".join(lnijp_byte_list)

def forming_head(bt_str_data_part):
    size = 0
    offset = 0
    tmp_prev_delimiter_pos = 0
    ls_dt_segment_info = []
    for i in range(0, len(bt_str_data_part), 4):
        # Check for delimiters <UNK1> or <M-CHOICE2>/ENTRY_TERMINATOR_BYTES
        if bt_str_data_part[i:i+4] == CHARACTERS_TABLE.get(b'\x40\x03\x00\x00',None) or \
           bt_str_data_part[i:i+4] == ENTRY_TERMINATOR_BYTES:
            size = (i + 4) - tmp_prev_delimiter_pos
            ls_dt_segment_info.append({'size': size, 'offset': offset})
            offset += size
            tmp_prev_delimiter_pos = i + 4
    return ls_dt_segment_info

def to_bytes_str(arr):
    dsfe = []
    for c_text in arr:
        if c_text != c_text: # Check for NaN
            dsfe.append('')
        else:
            tmp = []
            flij = cut_str_sem(c_text)
            fogw = parse_to_byt(flij)

            tmp.append(fogw)
            tmp.append(ENTRY_TERMINATOR_BYTES) # Appends terminator
            dfss = b''.join(tmp)

            jij_header_info = forming_head(dfss)
            coount_segments = len(jij_header_info)

            rrrrr_header_bytes = []
            rrrrr_header_bytes.append(coount_segments.to_bytes(4, 'little'))

            header_size_for_offsets = 4 + coount_segments * 8

            for l_idx in range(coount_segments):
                segment_offset_in_dfss = jij_header_info[l_idx]['offset']
                final_offset_for_header = segment_offset_in_dfss + header_size_for_offsets

                sizz_segment_in_words = int(jij_header_info[l_idx]['size'] / 4)

                rrrrr_header_bytes.append(sizz_segment_in_words.to_bytes(4, 'little'))
                rrrrr_header_bytes.append(final_offset_for_header.to_bytes(4, 'little'))

            rrrr_str_full_header = b''.join(rrrrr_header_bytes)
            dsfe.append(b"".join([rrrr_str_full_header, dfss]))
    return dsfe

def comp_item(old_tx_list, nw_tx_list, old_offset_table_bytes):
    artb_new_offset_table_chunks = [old_offset_table_bytes[i:i + 4] for i in range(0, len(old_offset_table_bytes), 4)]
    dfg_total_size_diff = 0

    for i in range(len(artb_new_offset_table_chunks)):
        current_original_offset = int.from_bytes(artb_new_offset_table_chunks[i], 'little')
        adjusted_offset = current_original_offset + dfg_total_size_diff
        artb_new_offset_table_chunks[i] = adjusted_offset.to_bytes(4, 'little')

        if nw_tx_list[i] == '':
            nw_tx_list[i] = old_tx_list[i]
        else:
            old_item_size = len(old_tx_list[i])
            split_result = split_byte_string(old_tx_list[i], ENTRY_TERMINATOR_BYTES)

            dfre_trailer = b''
            if len(split_result) > 1:
                dfre_trailer = split_result[1]

            nw_tx_list[i] = b''.join([nw_tx_list[i], dfre_trailer])
            dfg_total_size_diff += len(nw_tx_list[i]) - old_item_size

    return (artb_new_offset_table_chunks, dfg_total_size_diff)

def read_pr_items(op_fl, count_items, total_block_size):
    text_items_list = []
    block_start_abs_offset = op_fl.tell() # Current pos is start of this block's offset table
    block_end_abs_offset = block_start_abs_offset + total_block_size

    text_offsets_relative_to_block_start = [] # These are offsets from MBD file start
    for _ in range(count_items):
        text_offsets_relative_to_block_start.append(int.from_bytes(op_fl.read(4), 'little'))

    for i in range(count_items):
        current_text_start_abs_offset = text_offsets_relative_to_block_start[i]

        if current_text_start_abs_offset == 0 and i > 0 : # Treat 0 offset as empty/non-existent for non-first items
             text_items_list.append(b'')
             continue
        if current_text_start_abs_offset < block_start_abs_offset and current_text_start_abs_offset !=0 : # Check if offset is outside plausible range
            raise ValueError(f"Text item {i} offset {current_text_start_abs_offset} is before block data start {block_start_abs_offset}.")


        text_size = 0
        if i == count_items - 1:
            text_size = block_end_abs_offset - current_text_start_abs_offset
        else:
            next_text_start_abs_offset = text_offsets_relative_to_block_start[i+1]
            if next_text_start_abs_offset == 0: # If next is null, this one goes to end of block
                 text_size = block_end_abs_offset - current_text_start_abs_offset
            else:
                 text_size = next_text_start_abs_offset - current_text_start_abs_offset

        if text_size < 0:
            # print(f"Warning: Calculated negative text size ({text_size}) for item {i} at offset {current_text_start_abs_offset}. Appending empty string.", file=sys.stderr) # Less verbose
            text_items_list.append(b'')
            continue

        op_fl.seek(current_text_start_abs_offset, 0)
        text_items_list.append(op_fl.read(text_size))

    return text_items_list

def ne_tlng(table_lenguaes_pointers, size_diff):
    for i in range(2, len(table_lenguaes_pointers)): # Pointers for lang3 onwards
        original_offset = int.from_bytes(table_lenguaes_pointers[i], 'little')
        if original_offset == 0: # Don't adjust null pointers
            continue
        adjusted_offset = original_offset + size_diff
        table_lenguaes_pointers[i] = adjusted_offset.to_bytes(4, 'little')

def correcting_offsets(lang_block_data, global_size_adjustment, count_items):
    if not lang_block_data:
        return b''

    sub_table_size = count_items * 4

    if len(lang_block_data) < sub_table_size:
        # print(f"Warning: Language block (size {len(lang_block_data)}) too small for offset correction (expected sub-table: {sub_table_size}). Returning as is.", file=sys.stderr) # Less verbose
        return lang_block_data

    offset_table_part = lang_block_data[0:sub_table_size]
    text_data_part = lang_block_data[sub_table_size:]

    adjusted_offsets_list = []
    for i in range(0, len(offset_table_part), 4):
        original_sub_offset = int.from_bytes(offset_table_part[i:i+4], 'little')
        if original_sub_offset == 0: # Don't adjust null internal offsets
            adjusted_offsets_list.append(original_sub_offset.to_bytes(4, 'little'))
            continue
        adjusted_sub_offset = original_sub_offset + global_size_adjustment
        adjusted_offsets_list.append(adjusted_sub_offset.to_bytes(4, 'little'))

    return b''.join(adjusted_offsets_list) + text_data_part

def process_single_mbd_file(mbd_filepath_param, csv_filepath_param, output_mbd_filepath_param):
    mbd_file = None
    try:
        mbd_file = open(mbd_filepath_param, "rb")

        if mbd_file.read(4) != b'\x4D\x42\x44\x00': # MBD Magic
            raise ValueError(f"{mbd_filepath_param} is not a valid MBD file or magic number mismatch.")

        count_items = int.from_bytes(mbd_file.read(4), "little")
        mbd_file.seek(28, 1)

        if mbd_file.read(4) == b'\x00\x00\x00\x00':
            mbd_file.seek(-32, 1)
            mbd_file.seek(count_items * 28 + 4, 1)
        else:
            mbd_file.seek(-32, 1)
            mbd_file.seek(count_items * 44, 1)

        size_header_main = mbd_file.tell()
        mbd_file.seek(0, 0)

        data_from_csv = csv_parse(csv_filepath_param)
        data_bytes_for_block2 = to_bytes_str(data_from_csv)

        header_content = mbd_file.read(size_header_main)
        table_lenguaes_pointers = [mbd_file.read(4) for _ in range(10)]

        pos_after_lang_pointers = mbd_file.tell()

        def get_lang_block(file_handle, start_offset_bytes, end_offset_bytes_or_eof_marker):
            start_abs_offset = int.from_bytes(start_offset_bytes, 'little')
            if start_abs_offset == 0:
                 return b''

            file_handle.seek(start_abs_offset, 0)
            block_size = -1
            if end_offset_bytes_or_eof_marker == "EOF":
                current_pos = file_handle.tell()
                file_handle.seek(0, os.SEEK_END)
                eof_pos = file_handle.tell()
                block_size = eof_pos - current_pos
                file_handle.seek(current_pos, 0)
            else:
                end_abs_offset = int.from_bytes(end_offset_bytes_or_eof_marker, 'little')
                if end_abs_offset == 0: # Next block pointer is 0, current block extends to EOF
                    current_pos = file_handle.tell()
                    file_handle.seek(0, os.SEEK_END)
                    eof_pos = file_handle.tell()
                    block_size = eof_pos - current_pos
                    file_handle.seek(current_pos, 0)
                elif end_abs_offset < start_abs_offset:
                     raise ValueError(f"Invalid MBD structure: Lang block end offset ({end_abs_offset}) < start offset ({start_abs_offset}).")
                else:
                    block_size = end_abs_offset - start_abs_offset

            if block_size < 0:
                raise ValueError(f"Calculated negative size ({block_size}) for lang block starting at {start_abs_offset}.")
            return file_handle.read(block_size)

        mbd_file.seek(pos_after_lang_pointers)
        lang1_current_pos = mbd_file.tell()
        lang1_end_marker_offset = int.from_bytes(table_lenguaes_pointers[1], 'little')
        lang1_size = 0

        if lang1_end_marker_offset == 0:
            all_subsequent_pointers_zero = all(int.from_bytes(p, 'little') == 0 for p in table_lenguaes_pointers[1:])
            if all_subsequent_pointers_zero:
                mbd_file.seek(0, os.SEEK_END)
                eof_pos = mbd_file.tell()
                lang1_size = eof_pos - lang1_current_pos
                mbd_file.seek(lang1_current_pos, 0)
            else:
                lang1_size = 0
        else:
            if lang1_end_marker_offset < lang1_current_pos :
                 raise ValueError(f"Lang 1 end offset {lang1_end_marker_offset} < start {lang1_current_pos}.")
            lang1_size = lang1_end_marker_offset - lang1_current_pos

        language_translate_1_data = mbd_file.read(lang1_size)


        lang2_start_offset = int.from_bytes(table_lenguaes_pointers[1], 'little')
        if lang2_start_offset == 0:
             raise ValueError(f"Lang block 2 pointer is 0 in MBD '{mbd_filepath_param}'. Cannot process this file as script targets block 2.")

        lang3_start_offset_marker = int.from_bytes(table_lenguaes_pointers[2], 'little')
        size_total_block2 = 0
        if lang3_start_offset_marker == 0:
            mbd_file.seek(lang2_start_offset, 0)
            current_pos = mbd_file.tell()
            mbd_file.seek(0, os.SEEK_END)
            eof_pos = mbd_file.tell()
            size_total_block2 = eof_pos - current_pos
        else:
            if lang3_start_offset_marker < lang2_start_offset:
                raise ValueError(f"Lang 2 size calculation error: lang3_start ({lang3_start_offset_marker}) < lang2_start ({lang2_start_offset}).")
            size_total_block2 = lang3_start_offset_marker - lang2_start_offset

        mbd_file.seek(lang2_start_offset, 0)
        language_translate_2_original_texts = read_pr_items(mbd_file, count_items, size_total_block2)

        mbd_file.seek(lang2_start_offset, 0)
        language_translate_2_original_table = mbd_file.read(count_items * 4)

        language_translate_3_data = get_lang_block(mbd_file, table_lenguaes_pointers[2], table_lenguaes_pointers[3])
        language_translate_4_data = get_lang_block(mbd_file, table_lenguaes_pointers[3], table_lenguaes_pointers[4])
        language_translate_5_data = get_lang_block(mbd_file, table_lenguaes_pointers[4], table_lenguaes_pointers[5])
        language_translate_6_data = get_lang_block(mbd_file, table_lenguaes_pointers[5], table_lenguaes_pointers[6])
        language_translate_7_data = get_lang_block(mbd_file, table_lenguaes_pointers[6], table_lenguaes_pointers[7])
        language_translate_8_data = get_lang_block(mbd_file, table_lenguaes_pointers[7], table_lenguaes_pointers[8])
        language_translate_9_data = get_lang_block(mbd_file, table_lenguaes_pointers[8], table_lenguaes_pointers[9])
        language_translate_10_data = get_lang_block(mbd_file, table_lenguaes_pointers[9], "EOF")

        new_block2_table_chunks, total_size_diff_for_block2 = comp_item(
            language_translate_2_original_texts, data_bytes_for_block2, language_translate_2_original_table
        )

        new_block2_table_bytes = b''.join(new_block2_table_chunks)
        new_block2_texts_bytes = b''.join(data_bytes_for_block2)
        new_block2_full_data = b''.join([new_block2_table_bytes, new_block2_texts_bytes])

        ne_tlng(table_lenguaes_pointers, total_size_diff_for_block2)

        language_translate_3_data = correcting_offsets(language_translate_3_data, total_size_diff_for_block2, count_items)
        language_translate_4_data = correcting_offsets(language_translate_4_data, total_size_diff_for_block2, count_items)
        language_translate_5_data = correcting_offsets(language_translate_5_data, total_size_diff_for_block2, count_items)
        language_translate_6_data = correcting_offsets(language_translate_6_data, total_size_diff_for_block2, count_items)
        language_translate_7_data = correcting_offsets(language_translate_7_data, total_size_diff_for_block2, count_items)
        language_translate_8_data = correcting_offsets(language_translate_8_data, total_size_diff_for_block2, count_items)
        language_translate_9_data = correcting_offsets(language_translate_9_data, total_size_diff_for_block2, count_items)
        language_translate_10_data = correcting_offsets(language_translate_10_data, total_size_diff_for_block2, count_items)

        final_mbd_data_list = [
            header_content,
            b''.join(table_lenguaes_pointers),
            language_translate_1_data,
            new_block2_full_data,
            language_translate_3_data,
            language_translate_4_data,
            language_translate_5_data,
            language_translate_6_data,
            language_translate_7_data,
            language_translate_8_data,
            language_translate_9_data,
            language_translate_10_data
        ]

        write_mbd_data(final_mbd_data_list, output_mbd_filepath_param)
        # print(f"Successfully processed MBD file. Output saved to: {output_mbd_filepath_param}") # Removed verbose success message

    except FileNotFoundError:
        print(f"Error: Input MBD file '{mbd_filepath_param}' not found.", file=sys.stderr)
        raise
    except (pd.errors.EmptyDataError, IndexError) as e:
        # Error message for CSV parsing is already specific from csv_parse
        # print(f"Error parsing CSV file '{csv_filepath_param}': {e}", file=sys.stderr)
        raise
    except ValueError as e:
        print(f"Error processing MBD file '{mbd_filepath_param}': {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"An unexpected error occurred while processing '{mbd_filepath_param}': {e}", file=sys.stderr)
        # import traceback
        # traceback.print_exc()
        raise
    finally:
        if mbd_file:
            mbd_file.close()

def main(mbd_input_dir, csv_input_dir, output_base_dir):
    if not os.path.isdir(mbd_input_dir):
        print(f"Error: Input MBD directory '{mbd_input_dir}' not found or is not a directory.", file=sys.stderr)
        return
    if not os.path.isdir(csv_input_dir):
        print(f"Error: Input CSV directory '{csv_input_dir}' not found or is not a directory.", file=sys.stderr)
        return

    if not os.path.isdir(output_base_dir):
        try:
            os.makedirs(output_base_dir, exist_ok=True)
            print(f"Created output directory: '{output_base_dir}'")
        except OSError as e:
            print(f"Error: Could not create output directory '{output_base_dir}': {e}", file=sys.stderr)
            return

    mbd_files_to_attempt = []
    skipped_due_to_missing_csv = 0

    print("Scanning for MBD files and corresponding CSVs...")
    all_mbd_filenames = [f for f in os.listdir(mbd_input_dir) if f.lower().endswith(".mbd")]
    
    for mbd_filename in all_mbd_filenames:
        mbd_filepath = os.path.join(mbd_input_dir, mbd_filename)
        csv_filename_base = os.path.splitext(mbd_filename)[0]
        csv_filename = csv_filename_base + ".csv"
        csv_filepath = os.path.join(csv_input_dir, csv_filename)
        output_mbd_filepath = os.path.join(output_base_dir, mbd_filename)

        if not os.path.isfile(csv_filepath):
            print(f"Warning: Corresponding CSV file '{csv_filename}' not found in '{csv_input_dir}' for MBD file '{mbd_filename}'. Skipping.", file=sys.stderr)
            skipped_due_to_missing_csv += 1
        else:
            mbd_files_to_attempt.append({
                "mbd_filepath": mbd_filepath,
                "csv_filepath": csv_filepath,
                "output_filepath": output_mbd_filepath,
                "mbd_filename": mbd_filename
            })

    total_to_process = len(mbd_files_to_attempt)
    if total_to_process == 0 and skipped_due_to_missing_csv == 0:
        print("No MBD files found in the input directory.")
        return
    if total_to_process == 0 and skipped_due_to_missing_csv > 0:
        print(f"No MBD files to process (all {skipped_due_to_missing_csv} file(s) were missing corresponding CSVs).")
        return
        
    print(f"Found {total_to_process} MBD file(s) with corresponding CSVs to process.\n")

    mbd_files_processed_successfully = 0
    mbd_files_failed = 0
    
    for i, file_info in enumerate(mbd_files_to_attempt):
        mbd_filename = file_info["mbd_filename"]
        # Ensure the line is long enough to overwrite previous, shorter filenames
        progress_message = f"\rProcessing [{i+1}/{total_to_process}]: {mbd_filename:<60} ..." 
        sys.stdout.write(progress_message)
        sys.stdout.flush()
        
        try:
            process_single_mbd_file(file_info["mbd_filepath"], file_info["csv_filepath"], file_info["output_filepath"])
            mbd_files_processed_successfully += 1
        except Exception: # Catch any exception from process_single_mbd_file
            # Error message already printed by process_single_mbd_file or its callees to stderr
            # Need to print a newline to avoid stderr message overwriting progress bar
            sys.stdout.write("\n") # Move cursor to next line so stderr doesn't clobber progress
            print(f"Failed to process '{mbd_filename}'. Check error messages above. Skipping.", file=sys.stderr)
            mbd_files_failed += 1
            # To ensure the next progress line starts clean if error messages were short
            # and didn't cause a full line wrap on their own.
            # sys.stdout.write("\r" + " " * (len(progress_message) + 5) + "\r") # Clear line after error
            # sys.stdout.flush()


    # Clear the last progress line
    sys.stdout.write("\r" + " " * (len(progress_message) + 10) + "\r") # len of last progress_message + buffer
    sys.stdout.flush()
    print("Processing complete.")

    print(f"\n--- Summary ---")
    print(f"Total MBD files processed successfully: {mbd_files_processed_successfully}")
    print(f"Total MBD files failed during processing: {mbd_files_failed}")
    print(f"Total MBD files skipped (due to missing CSV): {skipped_due_to_missing_csv}")

if __name__ == '__main__':
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    mbd_input_rel_path = "system/all_files"
    csv_input_rel_path = "../system_CSV"
    output_base_rel_path = "system/all_files"

    inp_path = os.path.normpath(os.path.join(application_path, mbd_input_rel_path))
    inp2_path = os.path.normpath(os.path.join(application_path, csv_input_rel_path))
    o_path = os.path.normpath(os.path.join(application_path, output_base_rel_path))

    print(f"Application base path: {application_path}")
    print(f"MBD input directory (-inp): {inp_path}")
    print(f"CSV input directory (-inp2): {inp2_path}")
    print(f"Output directory (-o): {o_path}\n")

    main(inp_path, inp2_path, o_path)
