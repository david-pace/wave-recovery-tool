#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
'''
-- Wave Header Processor

Displays information about WAVE/AIFF file headers
and restores corrupted WAVE/AIFF file headers.

Copyright (C) 2019 David Hofmann

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

@author:     David Hofmann

@license:    GNU General Public License Version 3

@contact:    dev@davehofmann.de

@deffield    updated: Updated
'''

import os
import struct
import traceback
from utils import print_error, byte_string_to_hex,\
    print_with_condition, error_with_condition, warning_with_condition,\
    print_separator

__date__ = '2019-03-25'
__updated__ = '2019-09-28'

class WaveHeaderProcessor():
            
    def display_header_infos(self, path):
        
        if os.path.isdir(path):
            self.display_header_infos_in_directory(path)
        elif os.path.isfile(path):
            if self.is_wave_file(path):
                self.analyze_wave_header(path)
            elif self.is_aiff_file(path):
                self.analyze_aiff_header(path)
            else:
                print_error("File is neither a WAVE nor an AIFF file: {}".format(path))
        else:
            print_error("Given path is neither a file nor a directory: {}".format(path))
    
    def display_header_infos_in_directory(self, path):
        print("Scanning directory {}...".format(path))
        num_audio_files = 0
        for current_dir, subdirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(current_dir, file)
                is_wave_file = self.is_wave_file(full_path)
                is_aiff_file = self.is_aiff_file(full_path)
                if is_wave_file or is_aiff_file:
                    if is_wave_file:
                        self.analyze_wave_header(full_path)
                    else:
                        self.analyze_aiff_header(full_path)
                        
                    print_separator()
                    num_audio_files += 1
                else:
                    print("Unrecognized file extension, skipping file {}".format(full_path))
        print("Total Number of Audio Files:", num_audio_files)
                    
    def is_wave_file(self, file):
        extension = os.path.splitext(file)[-1].lower()
        return extension == ".wav" or extension == ".wave"
    
    def is_aiff_file(self, file):
        extension = os.path.splitext(file)[-1].lower()
        return extension == ".aif" or extension == ".aiff"
    
    """
    Displays information about the wave file header of the given file.
    Returns a boolean indicating whether the header has errors.
    
    Args:
        path: path to the wave file to analyze
        display: flag indicating whether analysis output should be displayed (True) or whether the method is just used for analysis (False)
    """
    def analyze_wave_header(self, path, display=True):
        
        found_error = False
        
        file_name = os.path.basename(path)
        num_bytes = os.path.getsize(path)
        
        print_with_condition(display, "Displaying WAVE File Header Data for File {}".format(file_name))
        print_with_condition(display, "Number of Bytes: {}".format(num_bytes))
        
        if num_bytes < 44:
            print_with_condition(display, "File is only {} bytes long and therefore can not contain a complete WAVE file header.".format(num_bytes))
            found_error = True
        
        print_with_condition(display, "Reading WAVE Header...")
        header_bytes = None
        with open(path, "rb") as waveFile:
            header_bytes = waveFile.read(44)
            
        print_with_condition(display, "Header contains the following bytes (hexadecimal): {}".format(byte_string_to_hex(header_bytes)))
            
        if header_bytes[:4] != b"RIFF":
            error_with_condition(display, "File does not start with 'RIFF' and therefore does not contain a correct wave file header.".format(file_name))
            found_error = True
            
        chunk_size_bytes = header_bytes[4:8]
        chunk_size = struct.unpack("<I", chunk_size_bytes)[0]
        
        print_with_condition(display, "Chunk Size: {}".format(chunk_size))
        
        expected_chunk_size = num_bytes - 8
        if chunk_size != expected_chunk_size:
            warning_with_condition(display, "Chunk size does not match file size. Should be equal to total number of bytes - 8 = {}, but was: {} (difference: {})".format(expected_chunk_size, chunk_size, abs(expected_chunk_size-chunk_size)))
        
        if header_bytes[8:12] != b"WAVE":
            error_with_condition(display, "Bytes 8-12 do not contain 'WAVE'")
            found_error = True
            
        if header_bytes[12:16] != b"fmt ":
            error_with_condition(display, "Bytes 12-16 do not contain 'fmt '")
            found_error = True
        
        sub_chunk_size_bytes = header_bytes[16:20]
        sub_chunk_size = struct.unpack("<I", sub_chunk_size_bytes)[0]
        
        print_with_condition(display, "Subchuck Size: {}".format(sub_chunk_size))
        
        if sub_chunk_size != 16:
            error_with_condition(display, "Subchunk size is not equal to 16.")
            found_error = True
            
        audio_format_bytes = header_bytes[20:22]
        audio_format = struct.unpack("<H", audio_format_bytes)[0]
        
        print_with_condition(display, "Audio Format: {}".format(audio_format))
        if audio_format != 1:
            error_with_condition(display, "Audio format is not equal to 1.")
            found_error = True
        
        num_channel_bytes = header_bytes[22:24]
        num_channels = struct.unpack("<H", num_channel_bytes)[0]
        
        print_with_condition(display, "Number of Channels: {}".format(num_channels))
        if num_channels < 1:
            error_with_condition(display, "Number of channels in invalid.")
            found_error = True
            
        sample_rate_bytes = header_bytes[24:28]
        sample_rate = struct.unpack("<I", sample_rate_bytes)[0]
        
        print_with_condition(display, "Sample Rate: {}".format(sample_rate))
        if sample_rate < 1:
            error_with_condition(display, "Sample rate is invalid.")
            found_error = True
            
        byte_rate_bytes = header_bytes[28:32]
        byte_rate = struct.unpack("<I", byte_rate_bytes)[0]
        
        print_with_condition(display, "Byte Rate (number of bytes per second): {}".format(byte_rate))
        if byte_rate < 1:
            error_with_condition(display, "Byte rate is invalid.")
            found_error = True
        
        block_align_bytes = header_bytes[32:34]
        block_align = struct.unpack("<H", block_align_bytes)[0]
        
        print_with_condition(display, "Bytes per Sample in all Channels (Block Align): {}".format(block_align))
        if block_align < 1:
            error_with_condition(display, "Block align in invalid.")
            found_error = True
        
        bits_per_sample_bytes = header_bytes[34:36]
        bits_per_sample = struct.unpack("<H", bits_per_sample_bytes)[0]
        
        print_with_condition(display, "Bits per Sample: {}".format(bits_per_sample))
        if bits_per_sample < 1:
            error_with_condition(display, "Bits per sample value is invalid.")
            found_error = True
        
        computed_block_align = num_channels * bits_per_sample / 8
        
        if block_align != computed_block_align:
            error_with_condition(display, "Block align should be equal to number of channels * bits per sample / 8 = {}, but is: {} (difference: {})".format(computed_block_align, block_align, abs(computed_block_align-block_align)))
            found_error = True
        
        computed_byte_rate = sample_rate * computed_block_align
        if byte_rate != computed_byte_rate:
            error_with_condition(display, "Byte rate should be equal to sample rate * number of channels * bits per sample / 8 = {}, but is: {} (difference: {})".format(computed_byte_rate, byte_rate, abs(computed_byte_rate-byte_rate)))
            found_error = True
        
        if header_bytes[36:40] != b"data":
            error_with_condition(display, "Bytes 36-40 do not contain 'data'")
            found_error = True
            
        data_subchunk_size_bytes = header_bytes[40:44]
        data_subchunk_size = struct.unpack("<I", data_subchunk_size_bytes)[0]
        
        print_with_condition(display, "Data Subchunk Size: {}".format(data_subchunk_size))
        
        expected_data_subchunk_size = num_bytes - 44
        if data_subchunk_size != expected_data_subchunk_size:
            warning_with_condition(display, "Data subchunk size does not match file size. Should be {}, but is: {} (difference: {})".format(expected_data_subchunk_size, data_subchunk_size, abs(expected_data_subchunk_size-data_subchunk_size)))
        
        return found_error
    
    """
    Displays information about the WAVE file header of the given file.
    Returns a boolean indicating whether the header has errors.
    
    Args:
        path: path to the WAVE file to analyze
        display: flag indicating whether analysis output should be displayed (True) or whether the method is just used for analysis (False)
    """
    def analyze_aiff_header(self, path, display=True):
        
        found_error = False
        
        file_name = os.path.basename(path)
        num_bytes = os.path.getsize(path)
        
        print_with_condition(display, "Displaying AIFF File Header Data for File {}".format(file_name))
        print_with_condition(display, "Number of Bytes: {}".format(num_bytes))
        
        if num_bytes < 12:
            print_with_condition(display, "File is only {} bytes long and therefore can not contain an AIFF header.".format(num_bytes))
            found_error = True
        
        print_with_condition(display, "Reading AIFF Header...")
        with open(path, "rb") as aiff_file:
            header_bytes = aiff_file.read(12)
            
            #print_with_condition(display, "Header contains the following bytes (hexadecimal): {}".format(byte_string_to_hex(header_bytes)))
                
            if header_bytes[:4] != b"FORM":
                error_with_condition(display, "File does not start with 'FORM' and therefore does not contain a correct AIFF file header.".format(file_name))
                found_error = True
                
            chunk_size_bytes = header_bytes[4:8]
            chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
            
            print_with_condition(display, "Chunk Size: {}".format(chunk_size))
            
            expected_chunk_size = num_bytes - 8
            if chunk_size != expected_chunk_size:
                warning_with_condition(display, "Chunk size does not match file size. Should be equal to total number of bytes - 8 = {}, but was: {} (difference: {})".format(expected_chunk_size, chunk_size, abs(expected_chunk_size-chunk_size)))
            
            if header_bytes[8:12] != b"AIFF":
                error_with_condition(display, "Bytes 8-12 do not contain 'AIFF'")
                found_error = True
            
            while aiff_file.tell() < num_bytes:
                chunk_header = aiff_file.read(8)
                chunk_name_bytes = chunk_header[:4]
                
                if not self.is_valid_chunk_name(chunk_name_bytes):
                    found_error = True
                    error_with_condition(display, "Invalid (non-printable) chunk name encountered (byte sequence {}). Aborting analysis.".format(chunk_name_bytes))
                    break
                    
                chunk_size_bytes = chunk_header[4:8]
                chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
                
                current_position = aiff_file.tell()
                
                if self.analyze_aiff_chunk(chunk_name_bytes, chunk_size, aiff_file, display):
                    found_error = True
                    
                if aiff_file.tell() == current_position:
                    print_error("No bytes consumed while processing chunk.")
                    break
                
        return found_error
    
    def analyze_aiff_chunk(self, chunk_name_bytes, chunk_size, aiff_file, display):
        if chunk_name_bytes == b'COMM':
            return self.analyze_comm_chunk(chunk_size, aiff_file, display)
        elif chunk_name_bytes == b'SSND':
            return self.analyze_ssnd_chunk(chunk_size, aiff_file, display)
        else:
            print_with_condition(display, "Skipping {} chunk (size: {}).".format(chunk_name_bytes.decode("utf-8"), chunk_size))
            aiff_file.seek(chunk_size, 1) # skip chunk and set file position to next chunk
            
        return False
            

    """
    Decodes an extended precision float (10 bytes, 80 bits) number.
    Encoding is:
    Sign (1 bit)
    Exponent (15 bits)
    Integer part (1 bit)
    Mantissa (63 bits)
    """
    def decode_float80(self, byte_string):
        """
        >>> p = WaveHeaderProcessor()
        >>> p.decode_float80((0x400BFA00000000000000).to_bytes(10, "big"))  
        8000.0
        >>> p.decode_float80((0x400EAC44000000000000).to_bytes(10, "big"))  
        44100.0
        >>> p.decode_float80((0x400EBB80000000000000).to_bytes(10, "big"))  
        48000.0
        >>> p.decode_float80((0x400FAC44000000000000).to_bytes(10, "big"))  
        88200.0
        >>> p.decode_float80((0x400FBB80000000000000).to_bytes(10, "big"))  
        96000.0
        >>> p.decode_float80((0x4010BB80000000000000).to_bytes(10, "big"))  
        192000.0
        """
        # first two bytes contain sign bit and 15 exponent bits
        sign_and_exponent_bytes = byte_string[:2]
        sign_and_exponent_int = int.from_bytes(sign_and_exponent_bytes, "big")
        
        # 8 bytes for the integer part (1 bit) and mantissa (63 bits)
        integer_part_and_fraction_bytes = byte_string[2:]
        integer_part_and_fraction_int = int.from_bytes(integer_part_and_fraction_bytes, "big")
        
        sign = 1 if sign_and_exponent_int & 0x80 != 0 else 0
        #print("Sign:", sign)
        
        exponent = sign_and_exponent_int & 0x7FFF
        #print("Exponent:", exponent)
        
        integer_part = 1 if (integer_part_and_fraction_int & 0x8000000000000000) != 0 else 0
        #print("Integer Part:", integer_part)
            
        mantissa = integer_part_and_fraction_int & 0x7FFFFFFFFFFFFFFF
        #print("Mantissa:", mantissa)
        return (-1) ** sign * (integer_part + float(mantissa) / (2 ** 63)) * (2 ** (exponent - 16383))
    
    def encode_float80(self, number):
        u"""
        >>> p = WaveHeaderProcessor()
        >>> p.encode_float80(8000.0) 
        b'@\\x0b\\xfa\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> p.encode_float80(44100.0)  
        b'@\\x0e\\xacD\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> p.encode_float80(48000.0)  
        b'@\\x0e\\xbb\\x80\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> p.encode_float80(88200.0)  
        b'@\\x0f\\xacD\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> p.encode_float80(96000.0)  
        b'@\\x0f\\xbb\\x80\\x00\\x00\\x00\\x00\\x00\\x00'
        >>> p.encode_float80(192000.0)  
        b'@\\x10\\xbb\\x80\\x00\\x00\\x00\\x00\\x00\\x00'
        """
        if number == 8000.0:
            return (0x400BFA00000000000000).to_bytes(10, "big")
        elif number == 44100.0:
            return (0x400EAC44000000000000).to_bytes(10, "big")
        elif number == 48000.0:
            return (0x400EBB80000000000000).to_bytes(10, "big")
        elif number == 88200.0:
            return (0x400FAC44000000000000).to_bytes(10, "big")
        elif number == 96000.0:
            return (0x400FBB80000000000000).to_bytes(10, "big")
        elif number == 192000.0:
            return (0x4010BB80000000000000).to_bytes(10, "big")
        else:
            raise RuntimeError("Encoding of number {} not implemented yet.".format(number))
        

    def analyze_comm_chunk(self, chunk_size, aiff_file, display):
        found_error = False
        print_with_condition(display, "Reading COMM chunk.")
        if chunk_size != 18:
            error_with_condition(display, "Expected chunk size of COMM chunk is 18, but was: {}".format(chunk_size))
            found_error = True
        
        num_channel_bytes = aiff_file.read(2)
        num_channels = struct.unpack(">H", num_channel_bytes)[0]
        print_with_condition(display, "Number of Channels: {}".format(num_channels))
        if num_channels < 1:
            error_with_condition(display, "Number of channels in invalid.")
            found_error = True
            
        num_frames_bytes = aiff_file.read(4)
        num_frames = struct.unpack(">I", num_frames_bytes)[0]
        print_with_condition(display, "Number of Frames: {}".format(num_frames))
        if num_channels < 1:
            error_with_condition(display, "Number of frames in invalid.")
            found_error = True
            
        bits_per_sample_bytes = aiff_file.read(2)
        bits_per_sample = struct.unpack(">H", bits_per_sample_bytes)[0]
        
        print_with_condition(display, "Bits per Sample: {}".format(bits_per_sample))
        if bits_per_sample < 1:
            error_with_condition(display, "Bits per sample value is invalid.")
            found_error = True
            
        sample_rate_bytes = aiff_file.read(10)
        sample_rate = self.decode_float80(sample_rate_bytes) 
        
        print_with_condition(display, "Sample Rate: {}".format(sample_rate))
        if sample_rate < 1:
            error_with_condition(display, "Sample rate is invalid.")
            found_error = True
            
        return found_error
        
    def analyze_ssnd_chunk(self, chunk_size, aiff_file, display):
        print_with_condition(display, "Reading SSND chunk (size: {}).".format(chunk_size))
        offset_bytes = aiff_file.read(4)
        offset = struct.unpack(">I", offset_bytes)[0]
        print_with_condition(display, "Offset: {}".format(offset))
        
        block_size_bytes = aiff_file.read(4)
        block_size = struct.unpack(">I", block_size_bytes)[0]
        print_with_condition(display, "Block Size: {}".format(block_size))
        
        
        aiff_file.seek(chunk_size - 8, 1) # skip audio data
        return False
            
    def repair_audio_file_headers(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels, verbose):
        if os.path.isdir(source_path):
            self.repair_audio_file_headers_in_directory(source_path, destination_path, sample_rate, bits_per_sample, num_channels)
        elif os.path.isfile(source_path):
            if os.path.exists(destination_path):
                if not self.ask_user_to_overwrite_destination_file(destination_path):
                    return
            
            if self.is_wave_file(source_path):
                self.repair_wave_file_header(source_path, destination_path, sample_rate, bits_per_sample, num_channels)
            elif self.is_aiff_file(source_path):
                self.repair_aiff_file_header(source_path, destination_path, sample_rate, bits_per_sample, num_channels)
            else:
                print("Unrecognized file extension, skipping file {}".format(source_path))
        else:
            print_error("Given path is neither a file nor a directory: {}".format(source_path))
        

    def ask_user_to_overwrite_destination_file(self, destination_path):
        user_input = input("Destination file {} already exists. Do you want to overwrite the file (y/N)? ".format(destination_path))
        if user_input.strip().lower() == "y":
            return True
        return False

    def repair_audio_file_headers_in_directory(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels):
        if not os.path.exists(destination_path):
            print("Creating destination directory {}...".format(destination_path))
            os.mkdir(destination_path)
        else:
            if not os.path.isdir(destination_path):
                print_error("File at destination path already exists but is not a directory.")
                return
        
        print("Scanning directory {}...".format(source_path))
        print_separator()
        num_repaired_audio_files = 0
        for current_dir, subdirs, files in os.walk(source_path):
            for file in files:
                full_path = os.path.join(current_dir, file)
                is_wave_file = self.is_wave_file(full_path)
                is_aiff_file = self.is_aiff_file(full_path)
                if is_wave_file or is_aiff_file:
                    found_error = False
                    
                    # we print an analysis notification here because nothing is displayed during analysis due the display=False flag
                    if is_wave_file:
                        print("Analyzing WAVE file {}".format(full_path))
                        found_error = self.analyze_wave_header(full_path, False)
                    else:
                        print("Analyzing AIFF file {}".format(full_path))
                        found_error = self.analyze_aiff_header(full_path, False)
                        
                    if found_error:
                        print("Found errors in file {}, trying to restore...".format(full_path))
                        full_destination_path = os.path.join(destination_path, file)
                        
                        if os.path.exists(full_destination_path):
                            if not self.ask_user_to_overwrite_destination_file(full_destination_path):
                                continue
                        
                        repair_result = False
                        if is_wave_file:
                            repair_result = self.repair_wave_file_header(full_path, full_destination_path, sample_rate, bits_per_sample, num_channels)
                        else:
                            repair_result = self.repair_aiff_file_header(full_path, full_destination_path, sample_rate, bits_per_sample, num_channels)
                        
                        if repair_result:
                            num_repaired_audio_files += 1
                        
                        print_separator()
                else:
                    print("Unrecognized file extension, skipping file {}".format(full_path))
                    
        print("Total Number of Repaired Audio Files:", num_repaired_audio_files)
    
    def repair_wave_file_header(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels):
        
        print("Restoring WAVE header in source file {}, storing result file in {}".format(source_path, destination_path))
        
        print("Writing WAVE file header with sample rate {} Hz, {} bits per sample, {} audio channels...".format(sample_rate, bits_per_sample, num_channels))
        num_bytes = os.path.getsize(source_path)
        
        chunk_size = num_bytes-8
        data_chunk_size = num_bytes-44
        
        print("Computed chunk size: {} bytes, data chunk size: {} bytes".format(chunk_size, data_chunk_size))
        
        try:
            with open(destination_path, "wb") as wave_file:
                wave_file.write(b"RIFF")
                wave_file.write(struct.pack("<I", chunk_size)) # chunk size = total byte size - 8
                wave_file.write(b"WAVE")
                wave_file.write(b"fmt ")
                wave_file.write(struct.pack("<I", 16)) # subchunk 1 size
                wave_file.write(struct.pack("<H", 1)) # audio format
                wave_file.write(struct.pack("<H", num_channels)) # number of channels
                wave_file.write(struct.pack("<I", sample_rate)) # sample rate
                block_align = int(num_channels * bits_per_sample / 8)
                byte_rate = sample_rate * block_align
                wave_file.write(struct.pack("<I", byte_rate)) # byte rate
                wave_file.write(struct.pack("<H", block_align)) # block align
                wave_file.write(struct.pack("<H", bits_per_sample)) # bits per sample
                wave_file.write(b"data")
                wave_file.write(struct.pack("<I", data_chunk_size)) # data chunk size (raw audio data size)
                
                print("WAVE header written, copying audio data...")
                
                with open(source_path, "rb") as source_wave_file:
                    # read audio data after the header
                    source_wave_file.seek(44)
                    while True:
                        buffer = source_wave_file.read(2048)
                        if buffer:
                            wave_file.write(buffer)
                        else:
                            break
                    
        except Exception:
            print_error("Error while writing WAVE file {}:".format(destination_path))
            traceback.print_exc()
            return False
        else:
            print("WAVE file {} written successfully.".format(destination_path))
        
        return True
    
    def is_valid_chunk_name(self, chunk_name_bytes):
        try:
            chunk_name_bytes.decode("utf-8")
            return True
        except UnicodeDecodeError:
            return False
    
    def repair_aiff_file_header(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels):
        print("Restoring AIFF header in source file {}, storing result file in {}".format(source_path, destination_path))
        print("Writing AIFF file header with sample rate {} Hz, {} bits per sample, {} audio channels...".format(sample_rate, bits_per_sample, num_channels))
        num_bytes = os.path.getsize(source_path)
        
        form_chunk_size = num_bytes-8
        
        print("Computed FORM chunk size: {} bytes".format(form_chunk_size))
        
        try:
            with open(source_path, "rb") as source_aiff_file, open(destination_path, "wb") as aiff_file:
                aiff_file.write(b"FORM")
                aiff_file.write(struct.pack(">I", form_chunk_size)) # chunk size = total byte size - 8
                aiff_file.write(b"AIFF")
                
                comm_chunk_written = False
                ssnd_chunk_written = False
                
                source_aiff_file.seek(12)
                while source_aiff_file.tell() < num_bytes:
                    chunk_header = source_aiff_file.read(8)
                    chunk_name_bytes = chunk_header[:4]
                    chunk_size_bytes = chunk_header[4:8]
                    chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
                    
                    valid_chunk_name = self.is_valid_chunk_name(chunk_name_bytes)
                    
                    if not valid_chunk_name or chunk_name_bytes == b"\x00\x00\x00\x00":
                        print("AIFF header is destroyed completely. Writing a default Logic-style AIFF header...")
                        self.write_aiff_headers(aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes)
                        comm_chunk_written = True
                        ssnd_chunk_written = True
                        # assume audio data starts at byte 512
                        source_aiff_file.seek(512)
                        self.copy_audio_data(source_aiff_file, aiff_file)
                        return True
                    
                    if chunk_size == 0:
                        raise RuntimeError("Invalid chunk size (0) for chunk with name '{}'".format(chunk_name_bytes.decode("utf-8")))
                    
                    current_position = source_aiff_file.tell()
                    
                    self.repair_aiff_chunk(source_aiff_file, aiff_file, chunk_name_bytes, chunk_size, sample_rate, bits_per_sample, num_channels, num_bytes)
                        
                    if source_aiff_file.tell() == current_position:
                        raise RuntimeError("No bytes consumed while processing chunk.")
                    
                    if chunk_name_bytes == b"COMM":
                        comm_chunk_written = True
                    elif chunk_name_bytes == b"SSND":
                        ssnd_chunk_written = True
                    
        except Exception:
            print_error("Error while restoring AIFF file {}:".format(destination_path))
            traceback.print_exc()
            return False
        else:
            if comm_chunk_written and ssnd_chunk_written:
                print("AIFF file {} written successfully.".format(destination_path))
            else:
                print("AIFF file could not be restored because the COMM and/or SSND chunks could not be located in the source file.")
                return False
        
        return True
    
    def write_aiff_headers(self, aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes):
        self.write_comt_chunk(aiff_file)
        self.write_comm_chunk(aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes)
        self.write_chan_chunk(aiff_file)
        self.write_ssnd_chunk(aiff_file, num_bytes)
        
    def write_comt_chunk(self, aiff_file):
        print("Writing COMT chunk.")
        
        aiff_file.write(b"COMT")
        aiff_file.write(struct.pack(">I", 410))
        comment = b"This AIFF file was restored using Wave Recovery Tool developed by David Hofmann. Visit https://github.com/davehofmann/wave-recovery-tool for more information."
        aiff_file.write(comment)
        aiff_file.write(b"\x00" * (410-len(comment)))
        
    def write_comm_chunk(self, aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes):
        print("Writing COMM chunk.")
        
        num_frames = (num_bytes-8-410-32)//(bits_per_sample//8) # TODO: check formula
            
        aiff_file.write(b"COMM")
        aiff_file.write(struct.pack(">I", 18)) # COMM chunk size
        aiff_file.write(struct.pack(">H", num_channels)) # number of channels
        aiff_file.write(struct.pack(">I", num_frames))
        aiff_file.write(struct.pack(">H", bits_per_sample)) # bits per sample
        aiff_file.write(self.encode_float80(sample_rate)) # sample rate
        
    def write_chan_chunk(self, aiff_file):
        print("Writing CHAN chunk.")
        
        aiff_file.write(b"CHAN")
        # TODO: find spec for CHAN chunk
        aiff_file.write(b"\x00\x00\x00\x20\x00\x64\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        
    def write_ssnd_chunk(self, aiff_file, num_bytes):
        print("Writing SSND chunk.")
        
        aiff_file.write(b"SSND")
        ssnd_chunk_size = num_bytes - 2184 # TODO: check formula
        aiff_file.write(struct.pack(">I", ssnd_chunk_size))
        aiff_file.write(struct.pack(">I", 0)) # offset
        aiff_file.write(struct.pack(">I", 0)) # block size
        
        
    
    def repair_aiff_chunk(self, source_aiff_file, aiff_file, chunk_name_bytes, chunk_size, sample_rate, bits_per_sample, num_channels, num_bytes):
        if chunk_name_bytes == b'COMM':
            self.repair_comm_chunk(source_aiff_file, aiff_file, chunk_size, sample_rate, bits_per_sample, num_channels)
        elif chunk_name_bytes == b'SSND':
            self.repair_ssnd_chunk(source_aiff_file, aiff_file, num_bytes)
        else:
            print("Copying {} chunk.".format(chunk_name_bytes.decode("utf-8")))
            aiff_file.write(chunk_name_bytes)
            aiff_file.write(struct.pack(">I", chunk_size))
            buffer = source_aiff_file.read(chunk_size)
            aiff_file.write(buffer)
            
    def repair_comm_chunk(self, source_aiff_file, aiff_file, chunk_size, sample_rate, bits_per_sample, num_channels):
        
        print("Repairing COMM chunk.")
        
        # skip num channel bytes
        source_aiff_file.seek(2, 1)
        
        # read number of frames from source file
        num_frames_bytes = source_aiff_file.read(4)
        num_frames = struct.unpack(">I", num_frames_bytes)[0]
        
        source_aiff_file.seek(chunk_size-6, 1)
            
        aiff_file.write(b"COMM")
        aiff_file.write(struct.pack(">I", 18)) # COMM chunk size
        aiff_file.write(struct.pack(">H", num_channels)) # number of channels
        aiff_file.write(struct.pack(">I", num_frames))
        aiff_file.write(struct.pack(">H", bits_per_sample)) # bits per sample
        aiff_file.write(self.encode_float80(sample_rate)) # sample rate
        
    
    def repair_ssnd_chunk(self, source_aiff_file, aiff_file, num_bytes):
        print("Repairing and copying SSND chunk.")
        
        aiff_file.write(b"SSND")
        ssnd_chunk_size = num_bytes - source_aiff_file.tell()
        aiff_file.write(struct.pack("<I", ssnd_chunk_size)) # data chunk size (raw audio data size)
        # offset and block size are copied from the source file
        #aiff_file.write(struct.pack(">I", 0)) # offset
        #aiff_file.write(struct.pack(">I", 0)) # block size
        
        self.copy_audio_data(source_aiff_file, aiff_file)
        
    def copy_audio_data(self, source_aiff_file, aiff_file):
        print("Copying audio data...")
        
        while True:
            buffer = source_aiff_file.read(2048)
            if buffer:
                aiff_file.write(buffer)
            else:
                break
            
        
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()