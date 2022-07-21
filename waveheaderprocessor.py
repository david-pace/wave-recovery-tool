#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
'''
-- Wave Header Processor

Displays information about WAVE/AIFF file headers
and restores corrupted WAVE/AIFF file headers.

Copyright (C) 2019-2022 David Pace

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

@author:     David Pace

@license:    GNU General Public License Version 3

@contact:    dev@davidpace.de

@deffield    updated: Updated
'''

import os
import struct
import traceback
from utils import print_error,\
    print_with_condition, error_with_condition, warning_with_condition,\
    print_separator

__date__ = '2019-03-25'
__updated__ = '2022-07-15'

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
        return extension == ".aif" or extension == ".aiff" or extension == ".aifc"
    
    def analyze_wave_header(self, path, display=True):
        """
        Displays information about the wave file header of the given file.
        Returns a boolean indicating whether the header has errors.
        
        Args:
            path: path to the wave file to analyze
            display: flag indicating whether analysis output should be displayed (True) or whether the method is just used for analysis (False)
        """
        
        file_name = os.path.basename(path)
        num_bytes = os.path.getsize(path)
        
        print_with_condition(display, "Displaying WAVE File Header Data for File {}".format(file_name))
        print_with_condition(display, "Number of Bytes: {}".format(num_bytes))
        
        if num_bytes < 12:
            print_with_condition(display, "File is only {} bytes long and therefore can not contain a WAVE file header.".format(num_bytes))
            return True
        
        print_with_condition(display, "Reading WAVE Header...")
        
        with open(path, "rb") as wave_file:
            header_bytes = wave_file.read(12)
                
            if header_bytes[:4] != b"RIFF":
                error_with_condition(display, "File does not start with 'RIFF' and therefore does not contain a correct WAVE file header.")
                return True
                
            chunk_size_bytes = header_bytes[4:8]
            chunk_size = struct.unpack("<I", chunk_size_bytes)[0]
            
            print_with_condition(display, "Chunk Size: {}".format(chunk_size))
            
            expected_chunk_size = num_bytes - 8
            if chunk_size != expected_chunk_size:
                warning_with_condition(display, "Chunk size does not match file size. Should be equal to total number of bytes - 8 = {}, but was: {} (difference: {})".format(expected_chunk_size, chunk_size, abs(expected_chunk_size-chunk_size)))
            
            if header_bytes[8:12] != b"WAVE":
                error_with_condition(display, "Bytes 8-12 do not contain 'WAVE'")
                return True
                
            while wave_file.tell() < num_bytes:
                chunk_header = wave_file.read(8)
                chunk_name_bytes = chunk_header[:4]
                
                if not self.is_decodable(chunk_name_bytes):
                    error_with_condition(display, "Invalid (non-printable) chunk name encountered (byte sequence {}). Aborting analysis.".format(chunk_name_bytes))
                    return True
                    
                chunk_size_bytes = chunk_header[4:8]
                chunk_size = struct.unpack("<I", chunk_size_bytes)[0]
                
                current_position = wave_file.tell()
                
                if self.analyze_wave_chunk(chunk_name_bytes, chunk_size, wave_file, num_bytes, display):
                    return True
                    
                if wave_file.tell() == current_position:
                    raise RuntimeError("No bytes consumed while processing '{}' chunk.".format(self.decode_bytes(chunk_name_bytes)))
                    
                if chunk_name_bytes == b'data':
                    # skip remaining parts of the file in case the data chunk is not correct
                    # otherwise this may lead to follow-up errors
                    break
        
        return False
    
    def analyze_wave_chunk(self, chunk_name_bytes, chunk_size, wave_file, num_bytes, display):
        if chunk_name_bytes == b'fmt ':
            return self.analyze_fmt_chunk(chunk_size, wave_file, display)
        elif chunk_name_bytes == b'data':
            return self.analyze_data_chunk(chunk_size, wave_file, num_bytes, display)
        else:
            print_with_condition(display, "Skipping {} chunk (size: {}).".format(self.decode_bytes(chunk_name_bytes), chunk_size))
            wave_file.seek(chunk_size, 1) # skip chunk and set file position to next chunk
            
        return False
    
    def analyze_fmt_chunk(self, chunk_size, wave_file, display):
        found_error = False
        fmt_chunk_bytes = wave_file.read(chunk_size)
        
        print_with_condition(display, "Reading fmt chunk (size: {})".format(chunk_size))
        
        if chunk_size != 16:
            error_with_condition(display, "fmt chunk size is not equal to 16.")
            found_error = True
            
        audio_format_bytes = fmt_chunk_bytes[0:2]
        audio_format = struct.unpack("<H", audio_format_bytes)[0]
        
        print_with_condition(display, "Audio Format: {}".format(audio_format))
        if audio_format != 1:
            error_with_condition(display, "Audio format is not equal to 1.")
            found_error = True
        
        num_channel_bytes = fmt_chunk_bytes[2:4]
        num_channels = struct.unpack("<H", num_channel_bytes)[0]
        
        print_with_condition(display, "Number of Channels: {}".format(num_channels))
        if num_channels < 1:
            error_with_condition(display, "Number of channels in invalid.")
            found_error = True
            
        sample_rate_bytes = fmt_chunk_bytes[4:8]
        sample_rate = struct.unpack("<I", sample_rate_bytes)[0]
        
        print_with_condition(display, "Sample Rate: {}".format(sample_rate))
        if sample_rate < 1:
            error_with_condition(display, "Sample rate is invalid.")
            found_error = True
            
        byte_rate_bytes = fmt_chunk_bytes[8:12]
        byte_rate = struct.unpack("<I", byte_rate_bytes)[0]
        
        print_with_condition(display, "Byte Rate (number of bytes per second): {}".format(byte_rate))
        if byte_rate < 1:
            error_with_condition(display, "Byte rate is invalid.")
            found_error = True
        
        block_align_bytes = fmt_chunk_bytes[12:14]
        block_align = struct.unpack("<H", block_align_bytes)[0]
        
        print_with_condition(display, "Bytes per Sample in all Channels (Block Align): {}".format(block_align))
        if block_align < 1:
            error_with_condition(display, "Block align in invalid.")
            found_error = True
        
        bits_per_sample_bytes = fmt_chunk_bytes[14:16]
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
            
        return found_error
            
    
    def analyze_data_chunk(self, chunk_size, wave_file, num_bytes, display):
        print_with_condition(display, "Reading data chunk (size: {}).".format(chunk_size))
        
        expected_data_subchunk_size = num_bytes - wave_file.tell()
        if chunk_size != expected_data_subchunk_size:
            warning_with_condition(display, "Data subchunk size does not match file size. Should be {}, but is: {} (difference: {})".format(expected_data_subchunk_size, chunk_size, abs(expected_data_subchunk_size-chunk_size)))
            
        wave_file.seek(chunk_size - 8, 1) # skip audio data
            
        return False
    
    def analyze_aiff_header(self, path, display=True):
        """
        Displays information about the AIFF file header of the given file.
        Returns a boolean indicating whether the header has errors.
        
        Args:
            path: path to the AIFF file to analyze
            display: flag indicating whether analysis output should be displayed (True) or whether the method is just used for analysis (False)
        """
        
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
            form_chunk_bytes = aiff_file.read(12)
            
            #print_with_condition(display, "Header contains the following bytes (hexadecimal): {}".format(byte_string_to_hex(form_chunk_bytes)))
                
            if form_chunk_bytes[:4] != b"FORM":
                error_with_condition(display, "File does not start with 'FORM' and therefore does not contain a correct AIFF file header.")
                found_error = True
                
            chunk_size_bytes = form_chunk_bytes[4:8]
            chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
            
            print_with_condition(display, "Chunk Size: {}".format(chunk_size))
            
            expected_chunk_size = num_bytes - 8
            if chunk_size != expected_chunk_size:
                warning_with_condition(display, "Chunk size does not match file size. Should be equal to total number of bytes - 8 = {}, but was: {} (difference: {})".format(expected_chunk_size, chunk_size, abs(expected_chunk_size-chunk_size)))
            
            format_name_bytes = form_chunk_bytes[8:12]
            if self.is_decodable(format_name_bytes):
                print_with_condition(display, "Format: {}".format(self.decode_bytes(format_name_bytes)))
            else:
                error_with_condition(display, "Invalid (non-printable) format name encountered (byte sequence {}).".format(format_name_bytes))
                found_error = True
                
            is_aiff = format_name_bytes == b"AIFF"
            is_aifc = format_name_bytes == b"AIFC"
            if not (is_aifc or is_aiff):
                error_with_condition(display, "Bytes 8-12 do neither contain 'AIFF' nor 'AIFC'")
                found_error = True
            
            while aiff_file.tell() < num_bytes:
                chunk_header = aiff_file.read(8)
                chunk_name_bytes = chunk_header[:4]
                
                if not self.is_decodable(chunk_name_bytes):
                    found_error = True
                    error_with_condition(display, "Invalid (non-printable) chunk name encountered (byte sequence {}). Aborting analysis.".format(chunk_name_bytes))
                    break
                    
                chunk_size_bytes = chunk_header[4:8]
                chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
                
                current_position = aiff_file.tell()
                
                if self.analyze_aiff_chunk(chunk_name_bytes, chunk_size, aiff_file, display, is_aifc):
                    found_error = True
                    
                if aiff_file.tell() == current_position:
                    print_error("No bytes consumed while processing '{}' chunk.".format(self.decode_bytes(chunk_name_bytes)))
                    break
                
        return found_error
    
    def analyze_aiff_chunk(self, chunk_name_bytes, chunk_size, aiff_file, display, is_aifc):
        if chunk_name_bytes == b'COMM':
            return self.analyze_comm_chunk(chunk_size, aiff_file, display, is_aifc)
        elif chunk_name_bytes == b'SSND':
            return self.analyze_ssnd_chunk(chunk_size, aiff_file, display)
        else:
            print_with_condition(display, "Skipping {} chunk (size: {}).".format(self.decode_bytes(chunk_name_bytes), chunk_size))
            aiff_file.seek(chunk_size, 1) # skip chunk and set file position to next chunk
            
        return False
            

    def decode_float80(self, byte_string):
        """Decodes an extended precision float (10 bytes, 80 bits) number.
        Encoding is:
        Sign (1 bit)
        Exponent (15 bits)
        Integer part (1 bit)
        Mantissa (63 bits)
        
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
        

    def analyze_comm_chunk(self, chunk_size, aiff_file, display, is_aifc):
        found_error = False
        print_with_condition(display, "Reading COMM chunk (size: {})".format(chunk_size))
        comm_chunk_bytes = aiff_file.read(chunk_size)
        
        if is_aifc:
            # AIFC file
            if chunk_size < 22:
                error_with_condition(display, "Expected chunk size of COMM chunk to be at least 22, but was: {}".format(chunk_size))
                found_error = True
        else:
            # AIFF file
            if chunk_size != 18:
                error_with_condition(display, "Expected chunk size of COMM chunk to be 18, but was: {}".format(chunk_size))
                found_error = True
            
        
        num_channel_bytes = comm_chunk_bytes[:2]
        num_channels = struct.unpack(">H", num_channel_bytes)[0]
        print_with_condition(display, "Number of Channels: {}".format(num_channels))
        if num_channels < 1:
            error_with_condition(display, "Number of channels in invalid.")
            found_error = True
            
        num_frames_bytes = comm_chunk_bytes[2:6]
        num_frames = struct.unpack(">I", num_frames_bytes)[0]
        print_with_condition(display, "Number of Frames: {}".format(num_frames))
        if num_channels < 1:
            error_with_condition(display, "Number of frames in invalid.")
            found_error = True
            
        bits_per_sample_bytes = comm_chunk_bytes[6:8]
        bits_per_sample = struct.unpack(">H", bits_per_sample_bytes)[0]
        
        print_with_condition(display, "Bits per Sample: {}".format(bits_per_sample))
        if bits_per_sample < 1:
            error_with_condition(display, "Bits per sample value is invalid.")
            found_error = True
            
        sample_rate_bytes = comm_chunk_bytes[8:18]
        sample_rate = self.decode_float80(sample_rate_bytes) 
        
        print_with_condition(display, "Sample Rate: {}".format(sample_rate))
        if sample_rate < 1:
            error_with_condition(display, "Sample rate is invalid.")
            found_error = True
            
        if is_aifc:
            # compression type and compression name are only available in AIFF-C
            if chunk_size >= 22:
                compression_type_bytes = comm_chunk_bytes[18:22]
                if self.is_decodable(compression_type_bytes):
                    print_with_condition(display, "Compression Type: {}".format(self.decode_bytes(compression_type_bytes)))
            if chunk_size > 22:
                compression_name_bytes = comm_chunk_bytes[22:]
                if self.is_decodable(compression_name_bytes):
                    print_with_condition(display, "Compression Name: {}".format(self.decode_bytes(compression_name_bytes)))
            
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
            
    def repair_audio_file_headers(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels, verbose, force, application, offset, end_offset):
        if os.path.isdir(source_path):
            self.repair_audio_file_headers_in_directory(source_path, destination_path, sample_rate, bits_per_sample, num_channels, force, application, offset, end_offset)
        elif os.path.isfile(source_path):
            if os.path.exists(destination_path):
                if not self.ask_user_to_overwrite_destination_file(destination_path):
                    return
            
            if self.is_wave_file(source_path):
                self.repair_wave_file_header(source_path, destination_path, sample_rate, bits_per_sample, num_channels, application, offset, end_offset)
            elif self.is_aiff_file(source_path):
                self.repair_aiff_file_header(source_path, destination_path, sample_rate, bits_per_sample, num_channels, application, offset, end_offset)
            else:
                print("Unrecognized file extension, skipping file {}".format(source_path))
        else:
            print_error("Given path is neither a file nor a directory: {}".format(source_path))
        

    def ask_user_to_overwrite_destination_file(self, destination_path):
        user_input = input("Destination file {} already exists. Do you want to overwrite the file (y/N)? ".format(destination_path))
        if user_input.strip().lower() == "y":
            return True
        return False

    def repair_audio_file_headers_in_directory(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels, force, application, offset, end_offset):
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
                    
                    if force:
                        print("Skipping check of file {} because restore is enforced.".format(full_path))
                    else:
                        found_error = self.check_file_for_errors(full_path, is_wave_file)
                        if found_error:
                            print("Found errors in file {}, trying to restore...".format(full_path))
                        else:
                            print("Skipping file {} because no errors were found.".format(full_path))
                        
                    if force or found_error:
                        full_destination_path = os.path.join(destination_path, file)
                        
                        if os.path.exists(full_destination_path):
                            if not self.ask_user_to_overwrite_destination_file(full_destination_path):
                                continue
                        
                        repair_result = False
                        if is_wave_file:
                            repair_result = self.repair_wave_file_header(full_path, full_destination_path, sample_rate, bits_per_sample, num_channels, application, offset, end_offset)
                        else:
                            repair_result = self.repair_aiff_file_header(full_path, full_destination_path, sample_rate, bits_per_sample, num_channels, application, offset, end_offset)
                        
                        if repair_result:
                            num_repaired_audio_files += 1
                        
                        print_separator()
                else:
                    print("Unrecognized file extension, skipping file {}".format(full_path))
                    
        print("Total Number of Repaired Audio Files:", num_repaired_audio_files)
        
    def check_file_for_errors(self, path, is_wave_file):
        # we print an analysis notification here because nothing is displayed during analysis due the display=False flag
        if is_wave_file:
            print("Analyzing WAVE file {}".format(path))
            return self.analyze_wave_header(path, False)
        else:
            print("Analyzing AIFF file {}".format(path))
            return self.analyze_aiff_header(path, False)
    
    def repair_wave_file_header(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels, application, offset, end_offset):
        
        print("Restoring WAVE header in source file {}, storing result file in {}".format(source_path, destination_path))
        
        print("Writing WAVE file header with sample rate {} Hz, {} bits per sample, {} audio channels...".format(sample_rate, bits_per_sample, num_channels))
        num_bytes = os.path.getsize(source_path)
        
        chunk_size = num_bytes - 8
        
        try:
            with open(source_path, "rb") as source_wave_file, open(destination_path, "wb") as wave_file:
                
                wave_file.write(b"RIFF")
                wave_file.write(struct.pack("<I", chunk_size)) # chunk size = total byte size - 8
                wave_file.write(b"WAVE")
                
                source_riff_chunk_bytes = source_wave_file.read(12)
                is_destroyed = source_riff_chunk_bytes[:4] != b"RIFF" or source_riff_chunk_bytes[8:12] != b"WAVE"
                
                fmt_chunk_written = False
                data_chunk_written = False
                
                while source_wave_file.tell() < num_bytes:
                    chunk_header = source_wave_file.read(8)
                    chunk_name_bytes = chunk_header[:4]
                    chunk_size_bytes = chunk_header[4:8]
                    chunk_size = struct.unpack("<I", chunk_size_bytes)[0]
                    
                    valid_chunk_name = self.is_decodable(chunk_name_bytes)
                    
                    if is_destroyed or not valid_chunk_name or chunk_name_bytes == b"\x00\x00\x00\x00":
                        print("WAVE header is destroyed completely. Writing a default Logic-style WAVE header...")
                        self.write_default_wave_headers(wave_file, sample_rate, bits_per_sample, num_channels, num_bytes)
                        fmt_chunk_written = True
                        data_chunk_written = True
                        # if no explicit offset is provided, assume audio data starts at byte 44
                        self.copy_audio_data(source_wave_file, wave_file, num_bytes, 44, offset, end_offset)
                        return True
                    
                    if chunk_size == 0:
                        raise RuntimeError("Invalid chunk size (0) for chunk with name '{}'".format(self.decode_bytes(chunk_name_bytes)))
                    
                    current_position = source_wave_file.tell()
                    
                    self.repair_wave_chunk(source_wave_file, wave_file, chunk_name_bytes, chunk_size, sample_rate, bits_per_sample, num_channels, num_bytes, offset, end_offset)
                        
                    if source_wave_file.tell() == current_position:
                        raise RuntimeError("No bytes consumed while processing '{}' chunk.".format(self.decode_bytes(chunk_name_bytes)))
                    
                    if chunk_name_bytes == b"fmt ":
                        fmt_chunk_written = True
                    elif chunk_name_bytes == b"data":
                        data_chunk_written = True
                    
        except Exception:
            print_error("Error while writing WAVE file {}:".format(destination_path))
            traceback.print_exc()
            return False
        else:
            if fmt_chunk_written and data_chunk_written:
                print("WAVE file {} written successfully.".format(destination_path))
            else:
                print("WAVE file could not be restored because the fmt and/or data chunks could not be located in the source file.")
                return False            
        
        return True
    
    def write_default_wave_headers(self, wave_file, sample_rate, bits_per_sample, num_channels, num_bytes):
        self.write_default_fmt_chunk(wave_file, sample_rate, bits_per_sample, num_channels)
        self.write_default_data_chunk(wave_file, num_bytes)
    
    def write_default_fmt_chunk(self, wave_file, sample_rate, bits_per_sample, num_channels):
        """
        Writes a WAVE fmt chunk containing:
        1. fmt (4 bytes)
        2. Chunk size = 16 (4 bytes)
        3. Audio Format (2 bytes)
        4. Number of Channels (2 bytes)
        5. Sample Rate (4 bytes)
        6. Byte Rate (4 bytes),  Sample Rate * Num Channels * Bits Per Sample / 8
        7. Block Align (2 bytes), Num Channels * Bits Per Sample / 8
        8. Bits per Sample (2 bytes)
        Total size: 24 bytes
        """
        
        print("Writing default fmt chunk.")
        wave_file.write(b"fmt ")
        wave_file.write(struct.pack("<I", 16)) # fmt chunk size
        wave_file.write(struct.pack("<H", 1)) # audio format
        wave_file.write(struct.pack("<H", num_channels)) # number of channels
        wave_file.write(struct.pack("<I", sample_rate)) # sample rate
        block_align = int(num_channels * bits_per_sample / 8)
        byte_rate = sample_rate * block_align
        wave_file.write(struct.pack("<I", byte_rate)) # byte rate
        wave_file.write(struct.pack("<H", block_align)) # block align
        wave_file.write(struct.pack("<H", bits_per_sample)) # bits per sample
        
    def write_default_data_chunk(self, wave_file, num_bytes):
        print("Writing default data chunk.")
        wave_file.write(b"data")
        
        data_chunk_size = num_bytes - 44
        wave_file.write(struct.pack("<I", data_chunk_size)) # data chunk size (raw audio data size)   
        
    def repair_wave_chunk(self, source_wave_file, wave_file, chunk_name_bytes, chunk_size, sample_rate, bits_per_sample, num_channels, num_bytes, offset, end_offset):
        if chunk_name_bytes == b'fmt ':
            self.repair_fmt_chunk(source_wave_file, wave_file, chunk_size, sample_rate, bits_per_sample, num_channels)
        elif chunk_name_bytes == b'data':
            self.repair_data_chunk(source_wave_file, wave_file, num_bytes, offset, end_offset)
        else:
            print("Copying {} chunk.".format(self.decode_bytes(chunk_name_bytes)))
            wave_file.write(chunk_name_bytes)
            wave_file.write(struct.pack("<I", chunk_size))
            buffer = source_wave_file.read(chunk_size)
            wave_file.write(buffer)
            
    def repair_fmt_chunk(self, source_wave_file, wave_file, chunk_size, sample_rate, bits_per_sample, num_channels):
        # skip fmt chunk in source file
        source_wave_file.read(chunk_size)
        
        self.write_default_fmt_chunk(wave_file, sample_rate, bits_per_sample, num_channels)
    
    def repair_data_chunk(self, source_wave_file, wave_file, num_bytes, offset, end_offset):
        print("Repairing and copying data chunk.")
        
        wave_file.write(b"data")
        current_offset = source_wave_file.tell()
        data_chunk_size = num_bytes - current_offset
        wave_file.write(struct.pack("<I", data_chunk_size)) # data chunk size (raw audio data size)
        
        self.copy_audio_data(source_wave_file, wave_file, num_bytes, current_offset, offset, end_offset)
    
    def is_decodable(self, byte_string):
        try:
            self.decode_bytes(byte_string)
            return True
        except UnicodeDecodeError:
            return False
    
    def decode_bytes(self, byte_string):
        return byte_string.decode("utf-8")

    def repair_aiff_file_header(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels, application, offset, end_offset):
        print("Restoring AIFF header in source file {}, storing result file in {}".format(source_path, destination_path))
        print("Writing AIFF file header with sample rate {} Hz, {} bits per sample, {} audio channels...".format(sample_rate, bits_per_sample, num_channels))
        num_bytes = os.path.getsize(source_path)
        
        # TODO: this number is not correct when some chunks are skipped, see issue #11
        form_chunk_size = num_bytes - 8
        
        print("Computed FORM chunk size: {} bytes".format(form_chunk_size))
        
        try:
            with open(source_path, "rb") as source_aiff_file, open(destination_path, "wb") as aiff_file:
                
                aiff_file.write(b"FORM")
                aiff_file.write(struct.pack(">I", form_chunk_size))
                
                source_form_chunk_bytes = source_aiff_file.read(12)
                if source_form_chunk_bytes[8:12] == b"AIFC":
                    aiff_file.write(b"AIFC")
                else:
                    aiff_file.write(b"AIFF")
                
                comm_chunk_written = False
                ssnd_chunk_written = False
                
                while source_aiff_file.tell() < num_bytes:
                    chunk_header = source_aiff_file.read(8)
                    chunk_name_bytes = chunk_header[:4]
                    chunk_size_bytes = chunk_header[4:8]
                    chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
                    
                    valid_chunk_name = self.is_decodable(chunk_name_bytes)
                    
                    if not valid_chunk_name or chunk_name_bytes == b"\x00\x00\x00\x00":
                        print("AIFF header is destroyed completely.")
                        self.write_default_aiff_headers(aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes, application)
                        comm_chunk_written = True
                        ssnd_chunk_written = True
                        audio_data_start_offset = self.get_aiff_data_start_offset(application)
                        self.copy_audio_data(source_aiff_file, aiff_file, num_bytes, audio_data_start_offset, offset, end_offset)
                        return True
                    
                    if chunk_size == 0:
                        raise RuntimeError("Invalid chunk size (0) for chunk with name '{}'".format(self.decode_bytes(chunk_name_bytes)))
                    
                    current_position = source_aiff_file.tell()
                    
                    self.repair_aiff_chunk(source_aiff_file, aiff_file, chunk_name_bytes, chunk_size, sample_rate, bits_per_sample, num_channels, num_bytes, offset, end_offset)
                        
                    if source_aiff_file.tell() == current_position:
                        raise RuntimeError("No bytes consumed while processing '{}' chunk.".format(self.decode_bytes(chunk_name_bytes)))
                    
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
    
    def get_aiff_data_start_offset(self, application):
        if application == "live":
            return 46 + 8
        # default offset for Logic files: audio data starts at byte 512
        return 512
    
    def write_default_aiff_headers(self, aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes, application):
        """
        Writes the AIFF headers depending on the provided application (logic or live):
        """
        
        # total size of COMM chunk + total size of SSND chunk header
        num_header_bytes = 26 + 16
        
        if application == "logic":
            # for logic we write additional 418 bytes for the COMT chunk and 40 bytes for the CHAN chunk
            num_header_bytes += 418 + 40
            # 418 bytes
            self.write_default_comt_chunk(aiff_file)
        
        # 26 bytes, already counted above
        self.write_default_comm_chunk(aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes, num_header_bytes)
        
        if application == "logic":
            # 40 bytes, already counted above
            self.write_default_chan_chunk(aiff_file)
        
        # 16 bytes, already counted above
        self.write_default_ssnd_chunk(aiff_file, num_bytes, num_header_bytes)
    
    def write_default_comt_chunk(self, aiff_file):
        """
        Writes a default Logic-style COMT chunk containing:
        1. COMT (4 bytes)
        2. Length = 410 (4 bytes)
        3. Comment data, filled up with zero bytes (410 bytes)
        Total size: 418 bytes
        """   
    
        print("Writing default COMT chunk.")
        
        aiff_file.write(b"COMT")
        aiff_file.write(struct.pack(">I", 410))
        comment = b"This AIFF file was restored using Wave Recovery Tool developed by David Pace. Visit https://github.com/david-pace/wave-recovery-tool for more information."
        aiff_file.write(comment)
        aiff_file.write(b"\x00" * (410-len(comment)))
    
    
    def write_default_comm_chunk(self, aiff_file, sample_rate, bits_per_sample, num_channels, num_bytes, num_header_bytes):
        """
        Writes a default COMM chunk containing:
        1. COMM (4 bytes)
        2. Length = 18 (4 bytes)
        3. Number of Channels (2 bytes)
        4. Number of Frames (4 bytes)
        5. Bits per Sample (2 bytes)
        6. Sample Rate (10 bytes)
        Total size: 26 bytes
        """
        
        print("Writing COMM chunk.")
        
        # 12 bytes for FORM + length + AIFF/AIFC
        # num_header_bytes includes COMM, SSND Header and possibly COMT and CHAN in case of Logic
        num_frames = (num_bytes - 12 - num_header_bytes) // (bits_per_sample // 8)
            
        aiff_file.write(b"COMM")
        aiff_file.write(struct.pack(">I", 18)) # COMM chunk size
        aiff_file.write(struct.pack(">H", num_channels)) # number of channels
        aiff_file.write(struct.pack(">I", num_frames)) # number of frames
        aiff_file.write(struct.pack(">H", bits_per_sample)) # bits per sample
        aiff_file.write(self.encode_float80(sample_rate)) # sample rate
    
    
    def write_default_chan_chunk(self, aiff_file):
        """
        Writes a default Logic-style CHAN chunk containing:
        1. CHAN (4 bytes)
        2. Length = 32 (4 bytes)
        3. Data (32 bytes)
        Total size: 40 bytes
        """
        
        print("Writing default CHAN chunk.")
        
        aiff_file.write(b"CHAN")
        # TODO: find spec for CHAN chunk
        # the following Logic chunk has 4 bytes for the length (32) + 32 bytes actual data
        aiff_file.write(b"\x00\x00\x00\x20\x00\x64\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
    
    def write_default_ssnd_chunk(self, aiff_file, num_bytes, num_header_bytes):
        """
        Writes the beginning of the SSND chunk containing:
        1. SSND (4 bytes)
        2. SSND Chunk Size (4 bytes)
        3. Offset (4 bytes)
        4. Block Size (4 bytes)
        Total size: 16 bytes
        """
        
        print("Writing default SSND chunk.")
        
        aiff_file.write(b"SSND")
        ssnd_chunk_size = num_bytes - 12 - num_header_bytes + 8
        aiff_file.write(struct.pack(">I", ssnd_chunk_size))
        aiff_file.write(struct.pack(">I", 0)) # offset
        aiff_file.write(struct.pack(">I", 0)) # block size
        
        
    
    def repair_aiff_chunk(self, source_aiff_file, aiff_file, chunk_name_bytes, chunk_size, sample_rate, bits_per_sample, num_channels, num_bytes, offset, end_offset):
        if chunk_name_bytes == b'COMM':
            self.repair_comm_chunk(source_aiff_file, aiff_file, chunk_size, sample_rate, bits_per_sample, num_channels)
        elif chunk_name_bytes == b'SSND':
            self.repair_ssnd_chunk(source_aiff_file, aiff_file, num_bytes, offset, end_offset)
        else:
            print("Copying {} chunk.".format(self.decode_bytes(chunk_name_bytes)))
            aiff_file.write(chunk_name_bytes)
            aiff_file.write(struct.pack(">I", chunk_size))
            buffer = source_aiff_file.read(chunk_size)
            aiff_file.write(buffer)
            
    def repair_comm_chunk(self, source_aiff_file, aiff_file, chunk_size, sample_rate, bits_per_sample, num_channels):
        
        print("Repairing COMM chunk.")
        
        source_comm_chunk_bytes = source_aiff_file.read(chunk_size)
        
        aiff_file.write(b"COMM")
        aiff_file.write(struct.pack(">I", chunk_size)) # COMM chunk size
        aiff_file.write(struct.pack(">H", num_channels)) # number of channels
        
        # read number of frames from source file
        num_frames_bytes = source_comm_chunk_bytes[2:6]
        num_frames = struct.unpack(">I", num_frames_bytes)[0]
            
        aiff_file.write(struct.pack(">I", num_frames))
        aiff_file.write(struct.pack(">H", bits_per_sample)) # bits per sample
        aiff_file.write(self.encode_float80(sample_rate)) # sample rate
        
        aiff_file.write(source_comm_chunk_bytes[18:])
        
    
    def repair_ssnd_chunk(self, source_aiff_file, aiff_file, num_bytes, offset, end_offset):
        print("Repairing SSND chunk.")
        
        aiff_file.write(b"SSND")
        current_offset = source_aiff_file.tell()
        ssnd_chunk_size = num_bytes - current_offset
        aiff_file.write(struct.pack(">I", ssnd_chunk_size)) # data chunk size (raw audio data size)
        # offset and block size are copied from the source file
        # if an audio offset is specified manually, write offset and block size here
        if offset is not None:
            aiff_file.write(struct.pack(">I", 0)) # offset
            aiff_file.write(struct.pack(">I", 0)) # block size
            
        self.copy_audio_data(source_aiff_file, aiff_file, num_bytes, current_offset, offset, end_offset)
        
    def copy_audio_data(self, source_file, destination_file, num_bytes, default_offset, offset_argument, end_offset_argument):
        start_offset = default_offset if offset_argument is None else offset_argument
        end_offset = num_bytes if end_offset_argument is None else end_offset_argument
        # if offset is negative, interpret as offset from the end of the file
        effective_start_offset = start_offset if start_offset >= 0 else num_bytes + start_offset
        effective_end_offset = end_offset if end_offset >= 0 else num_bytes + end_offset
        
        if effective_end_offset < effective_start_offset:
            raise RuntimeError("Effective end offset {} is smaller than effective start offset {}".format(effective_end_offset, effective_start_offset))
        
        print("Copying data from input file starting at offset {}, end offset {}...".format(effective_start_offset, effective_end_offset))
        
        if source_file.tell() != effective_start_offset:
            source_file.seek(effective_start_offset)
        
        while True:
            buffer_size = 4096 if end_offset_argument is None else min(4096, effective_end_offset - source_file.tell())
            buffer = source_file.read(buffer_size)
            if buffer:
                destination_file.write(buffer)
            else:
                break
            
        print("Data copied successfully.")
            
        
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()