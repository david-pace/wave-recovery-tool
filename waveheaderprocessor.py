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
from utils import print_error, print_warning, byte_string_to_hex,\
    print_with_condition, error_with_condition, warning_with_condition,\
    print_separator

__date__ = '2019-03-25'
__updated__ = '2019-09-27'

class WaveHeaderProcessor():
            
    def displayHeaderInfos(self, path):
        
        if os.path.isdir(path):
            self.displayHeaderInfosDirectory(path)
        elif os.path.isfile(path):
            if self.isWaveFile(path):
                self.analyzeWaveHeader(path)
            elif self.isAIFFFile(path):
                self.analyzeAIFFHeader(path)
            else:
                print_error("File is neither a WAVE nor an AIFF file: {}".format(path))
        else:
            print_error("Given path is neither a file nor a directory: {}".format(path))
    
    def displayHeaderInfosDirectory(self, path):
        print("Scanning directory {}...".format(path))
        num_audio_files = 0
        for current_dir, subdirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(current_dir, file)
                if self.isWaveFile(full_path):
                    self.analyzeWaveHeader(full_path)
                    print_separator()
                    num_audio_files += 1
                elif self.isAIFFFile(full_path):
                    self.analyzeAIFFHeader(full_path)
                    print_separator()
                    num_audio_files += 1
        print("Total Number of Audio Files:", num_audio_files)
                    
    def isWaveFile(self, file):
        extension = os.path.splitext(file)[-1].lower()
        return extension == ".wav" or extension == ".wave"
    
    def isAIFFFile(self, file):
        extension = os.path.splitext(file)[-1].lower()
        return extension == ".aif" or extension == ".aiff"
    
    """
    Displays information about the wave file header of the given file.
    Returns a boolean indicating whether the header has errors.
    
    Args:
        path: path to the wave file to analyze
        display: flag indicating whether analysis output should be displayed (True) or whether the method is just used for analysis (False)
    """
    def analyzeWaveHeader(self, path, display=True):
        
        found_error = False
        
        file_name = os.path.basename(path)
        num_bytes = os.path.getsize(path)
        
        print_with_condition(display, "Displaying Wave File Header Data for File {}".format(file_name))
        print_with_condition(display, "Number of Bytes: {}".format(num_bytes))
        
        if num_bytes < 44:
            print_with_condition(display, "File is only {} bytes long and therefore can not contain a complete wave file header.".format(num_bytes))
            found_error = True
        
        print_with_condition(display, "Reading Wave Header...")
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
    Displays information about the wave file header of the given file.
    Returns a boolean indicating whether the header has errors.
    
    Args:
        path: path to the wave file to analyze
        display: flag indicating whether analysis output should be displayed (True) or whether the method is just used for analysis (False)
    """
    def analyzeAIFFHeader(self, path, display=True):
        
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
                chunk_size_bytes = chunk_header[4:8]
                chunk_size = struct.unpack(">I", chunk_size_bytes)[0]
                
                current_position = aiff_file.tell()
                
                if self.processAIFFChunk(chunk_name_bytes, chunk_size, aiff_file, display):
                    found_error = True
                    
                if aiff_file.tell() == current_position:
                    print_error("No bytes consumed while processing chunk.")
                    break
                
        return found_error
    
    def processAIFFChunk(self, chunk_name_bytes, chunk_size, aiff_file, display):
        if chunk_name_bytes == b'COMM':
            return self.processCOMMChunk(chunk_size, aiff_file, display)
        elif chunk_name_bytes == b'SSND':
            return self.processSSNDChunk(chunk_size, aiff_file, display)
        else:
            print_with_condition(display, "Skipping {} chunk.".format(chunk_name_bytes.decode("utf-8")))
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
    def decode_float80(self, bytes):
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
        sign_and_exponent_bytes = bytes[:2]
        sign_and_exponent_int = int.from_bytes(sign_and_exponent_bytes, "big")
        
        # 8 bytes for the integer part (1 bit) and mantissa (63 bits)
        integer_part_and_fraction_bytes = bytes[2:]
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

    def processCOMMChunk(self, chunk_size, aiff_file, display):
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
        
    def processSSNDChunk(self, chunk_size, aiff_file, display):
        print_with_condition(display, "Reading SSND chunk.")
        offset_bytes = aiff_file.read(4)
        offset = struct.unpack(">I", offset_bytes)[0]
        print_with_condition(display, "Offset: {}".format(offset))
        
        block_size_bytes = aiff_file.read(4)
        block_size = struct.unpack(">I", block_size_bytes)[0]
        print_with_condition(display, "Block Size: {}".format(block_size))
        
        
        aiff_file.seek(chunk_size - 8, 1) # skip audio data
        return False
            
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
        print_separator()
        num_repaired_wave_files = 0
        for current_dir, subdirs, files in os.walk(source_path):
            for file in files:
                full_path = os.path.join(current_dir, file)
                if self.isWaveFile(full_path):
                    found_error = self.analyzeWaveHeader(full_path, False)
                    if found_error:
                        full_destination_path = os.path.join(destination_path, file)
                        if self.repairWaveFileHeader(full_path, full_destination_path, sample_rate, bits_per_sample, num_channels):
                            num_repaired_wave_files += 1
                        print_separator()
        print("Total Number of Repaired Wave Files:", num_repaired_wave_files)
    
    def repairWaveFileHeader(self, source_path, destination_path, sample_rate, bits_per_sample, num_channels):
        
        print("Restoring wave header in source file {}, storing result file in {}".format(source_path, destination_path))
        
        if os.path.exists(destination_path):
            print_error("Destination file {} already exists. Canceling before anything is lost...".format(destination_path))
            return False
        
        num_bytes = os.path.getsize(source_path)
        
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
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()