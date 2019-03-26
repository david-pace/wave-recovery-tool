#!/usr/local/bin/python3
# encoding: utf-8
'''
-- Wave Header Processor

Displays information about wave file headers and restores corrupted wave file headers.

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
from utils import print_error, print_warning, byte_string_to_hex

__date__ = '2019-03-25'
__updated__ = '2019-03-26'

class WaveHeaderProcessor():
            
    def displayHeaderInfos(self, path):
        
        if os.path.isdir(path):
            self.displayHeaderInfosDirectory(path)
        elif os.path.isfile(path):
            self.analyzeWaveHeader(path)
        else:
            print_error("Given path is neither a file nor a directory:", path)
    
    def displayHeaderInfosDirectory(self, path):
        print("Scanning directory {}...".format(path))
        num_wave_files = 0
        for current_dir, subdirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(current_dir, file)
                if self.isWaveFile(full_path):
                    self.analyzeWaveHeader(full_path)
                    print("---------------------------------------------------------------")
                    num_wave_files += 1
        print("Total Number of Wave Files:", num_wave_files)
                    
    def isWaveFile(self, file):
        return os.path.splitext(file)[-1].lower() == ".wav"
    
    """
    Displays information about the wave file header of the given file.
    Returns a boolean indicating whether the header has errors.
    """
    def analyzeWaveHeader(self, path):
        
        found_error = False
        
        file_name = os.path.basename(path)
        num_bytes = os.path.getsize(path)
        
        print("Displaying Wave File Header Data for File {}".format(file_name))
        print("Number of Bytes: {}".format(num_bytes))
        
        if num_bytes < 44:
            print("File is only {} bytes long and therefore can not contain a complete wave file header.".format(num_bytes))
            found_error = True
        
        print("Reading Wave Header...")
        header_bytes = None
        with open(path, "rb") as waveFile:
            header_bytes = waveFile.read(44)
            
        print("Header contains the following bytes (hexadecimal): {}".format(byte_string_to_hex(header_bytes)))
            
        if header_bytes[:4] != b"RIFF":
            print_error("File does not start with 'RIFF' and therefore does not contain a correct wave file header.".format(file_name))
            found_error = True
            
        chunk_size_bytes = header_bytes[4:8]
        chunk_size = struct.unpack("<I", chunk_size_bytes)[0]
        
        print("Chunk Size: {}".format(chunk_size))
        
        expected_chunk_size = num_bytes - 8
        if chunk_size != expected_chunk_size:
            print_warning("Chunk size does not match file size. Should be equal to total number of bytes - 8 = {}, but was: {} (difference: {})".format(expected_chunk_size, chunk_size, abs(expected_chunk_size-chunk_size)))
        
        if header_bytes[8:12] != b"WAVE":
            print_error("Bytes 8-12 do not contain 'WAVE'")
            found_error = True
            
        if header_bytes[12:16] != b"fmt ":
            print_error("Bytes 12-16 do not contain 'fmt '")
            found_error = True
        
        sub_chunk_size_bytes = header_bytes[16:20]
        sub_chunk_size = struct.unpack("<I", sub_chunk_size_bytes)[0]
        
        print("Subchuck Size: {}".format(sub_chunk_size))
        
        if sub_chunk_size != 16:
            print_error("Subchunk size is not equal to 16.")
            found_error = True
            
        audio_format_bytes = header_bytes[20:22]
        audio_format = struct.unpack("<H", audio_format_bytes)[0]
        
        print("Audio Format: {}".format(audio_format))
        if audio_format != 1:
            print_error("Audio format is not equal to 1.")
            found_error = True
        
        num_channel_bytes = header_bytes[22:24]
        num_channels = struct.unpack("<H", num_channel_bytes)[0]
        
        print("Number of Channels: {}".format(num_channels))
        if num_channels < 1:
            print_error("Number of channels in invalid.")
            found_error = True
            
        sample_rate_bytes = header_bytes[24:28]
        sample_rate = struct.unpack("<I", sample_rate_bytes)[0]
        
        print("Sample Rate: {}".format(sample_rate))
        if sample_rate < 1:
            print_error("Sample rate is invalid.")
            found_error = True
            
        byte_rate_bytes = header_bytes[28:32]
        byte_rate = struct.unpack("<I", byte_rate_bytes)[0]
        
        print("Byte Rate (number of bytes per second): {}".format(byte_rate))
        if byte_rate < 1:
            print_error("Byte rate is invalid.")
            found_error = True
        
        block_align_bytes = header_bytes[32:34]
        block_align = struct.unpack("<H", block_align_bytes)[0]
        
        print("Bytes per Sample in all Channels (Block Align): {}".format(block_align))
        if block_align < 1:
            print_error("Block align in invalid.")
            found_error = True
        
        bits_per_sample_bytes = header_bytes[34:36]
        bits_per_sample = struct.unpack("<H", bits_per_sample_bytes)[0]
        
        print("Bits per Sample: {}".format(bits_per_sample))
        if bits_per_sample < 1:
            print_error("Bits per sample is invalid.")
            found_error = True
        
        computed_block_align = num_channels * bits_per_sample / 8
        
        if block_align != computed_block_align:
            print_error("Block align should be equal to number of channels * bits per sample / 8 = {}, but is: {} (difference: {})".format(computed_block_align, block_align, abs(computed_block_align-block_align)))
            found_error = True
        
        computed_byte_rate = sample_rate * computed_block_align
        if byte_rate != computed_byte_rate:
            print_error("Byte rate should be equal to sample rate * number of channels * bits per sample / 8 = {}, but is: {} (difference: {})".format(computed_byte_rate, byte_rate, abs(computed_byte_rate-byte_rate)))
            found_error = True
        
        if header_bytes[36:40] != b"data":
            print_error("Bytes 36-40 do not contain 'data'")
            found_error = True
            
        data_subchunk_size_bytes = header_bytes[40:44]
        data_subchunk_size = struct.unpack("<I", data_subchunk_size_bytes)[0]
        
        print("Data Subchunk Size: {}".format(data_subchunk_size))
        
        expected_data_subchunk_size = num_bytes - 44
        if data_subchunk_size != expected_data_subchunk_size:
            print_warning("Data subchunk size does not match file size. Should be {}, but is: {} (difference: {})".format(expected_data_subchunk_size, data_subchunk_size, abs(expected_data_subchunk_size-data_subchunk_size)))
        
        return found_error
            
    def repairWaveFileHeaders(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels, verbose):
        if os.path.isdir(source_path):
            self.repairWaveFileHeadersInDirectory(source_path, destination_path, sample_rate, bits_per_sample, num_channels)
        elif os.path.isfile(source_path):
            self.repairWaveFileHeader(source_path, destination_path, sample_rate, bits_per_sample, num_channels)
        else:
            print_error("Given path is neither a file nor a directory:", source_path)
        
    def repairWaveFileHeadersInDirectory(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels):
        if not os.path.exists(destination_path):
            print("Creating destination directory {}...".format(destination_path))
            os.mkdir(destination_path)
        else:
            if not os.path.isdir(destination_path):
                print_error("File at destination path already exists but is not a directory.")
                return
        
        print("Scanning directory {}...".format(source_path))
        num_repaired_wave_files = 0
        for current_dir, subdirs, files in os.walk(source_path):
            for file in files:
                full_path = os.path.join(current_dir, file)
                if self.isWaveFile(full_path):
                    found_error = self.analyzeWaveHeader(full_path)
                    if found_error:
                        full_destination_path = os.path.join(destination_path, file)
                        if self.repairWaveFileHeader(full_path, full_destination_path, sample_rate, bits_per_sample, num_channels):
                            num_repaired_wave_files += 1
                    print("---------------------------------------------------------------")
        print("Total Number of Repaired Wave Files:", num_repaired_wave_files)
    
    def repairWaveFileHeader(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels):
        
        if os.path.exists(destination_path):
            print_error("Destination file {} already exists. Canceling before anything is lost...".format(destination_path))
            return
        
        num_bytes = os.path.getsize(source_path)
        
        print("Repairing wave header in source file {}, storing result file in {}".format(source_path, destination_path))
        print("Writing wave file header with sample rate {} Hz, {} bits per sample, {} audio channels...".format(sample_rate, bits_per_sample, num_channels))
        
        chunk_size = num_bytes-8
        data_chunk_size = num_bytes-44
        
        print("Computed chunk size: {} bytes, data chunk size: {} bytes".format(chunk_size, data_chunk_size))
        
        try:
            with open(destination_path, "wb") as waveFile:
                waveFile.write(b"RIFF")
                waveFile.write(struct.pack("<I", chunk_size)) # chunk size = total byte size - 8
                waveFile.write(b"WAVE")
                waveFile.write(b"fmt ")
                waveFile.write(struct.pack("<I", 16)) # subchunk 1 size
                waveFile.write(struct.pack("<H", 1)) # audio format
                waveFile.write(struct.pack("<H", num_channels)) # number of channels
                waveFile.write(struct.pack("<I", sample_rate)) # sample rate
                block_align = int(num_channels * bits_per_sample / 8)
                byte_rate = sample_rate * block_align
                waveFile.write(struct.pack("<I", byte_rate)) # byte rate
                waveFile.write(struct.pack("<H", block_align)) # block align
                waveFile.write(struct.pack("<H", bits_per_sample)) # bits per sample
                waveFile.write(b"data")
                waveFile.write(struct.pack("<I", data_chunk_size)) # data chunk size (raw audio data size)
                
                print("Wave Header written, copying audio data...")
                
                with open(source_path, "rb") as sourceWaveFile:
                    # read audio data after the header
                    sourceWaveFile.seek(44)
                    while True:
                        buffer = sourceWaveFile.read(2048)
                        if buffer:
                            waveFile.write(buffer)
                        else:
                            break
                    
        except Exception as e:
            print_error("Error while writing wave file {}: {}".format(destination_path, str(e)))
            return False
        else:
            print("Wave file {} restored successfully.".format(destination_path))
        
        return True