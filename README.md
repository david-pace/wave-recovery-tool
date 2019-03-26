# Wave Recovery Tool

Tool to display wave file header information and to restore corrupted wave file headers.

This program was originally developed to recover damaged wave files destroyed due to a bug in the audio application _Logic_.

# License

Wave Recovery Tool is licensed under the terms of the GNU General Public License Version 3.

# Author

Wave Recovery Tool is developed by David Hofmann &lt;dev@davehofmann.de&gt;

# Prerequisites

To use the wave recovery tool, a [Python 3](https://www.python.org/downloads/) installation is required.

For all commands below, `python3` is assumed to be in the system's executable `PATH`. If your system reports that `python3` can not be found, its containing directory must either be added to the `PATH` variable or `python3` must be replaced with the absolute path to the Python 3 interpreter.

# Usage

The tool provides two functionalities:

1. Displaying wave file header information
2. Restoring corrupted wave file headers

## Displaying Header File Information

To display header information for a specific wave file, invoke the tool as follows:

```
python3 waverecovery.py /path/to/file.wav
```

The tool can also display wave header information for all files contained in a directory:

```
python3 waverecovery.py /path/to/directory
```

All available header fields will be shown. In case a wave file header is damaged, error messages prefixed with `[ERROR]` will be displayed. In case size headers (particularly `chunk size` and `data subchunk size`) are not consistent with the overall wave file size, warnings prefixed with `[WARNING]` will be displayed. An example output looks like this:

```
Displaying Wave File Header Data for File MyWaveFile.wav
Number of Bytes: 3435091
Reading Wave Header...
Header contains the following bytes (hexadecimal): 52 49 46 46 4B 6A 34 00 57 41 56 45 66 6D 74 20 10 00 00 00 01 00 01 00 44 AC 00 00 CC 04 02 00 03 00 18 00 64 61 74 61 15 44 34 00
Chunk Size: 3435083
Subchuck Size: 16
Audio Format: 1
Number of Channels: 1
Sample Rate: 44100
Byte Rate (number of bytes per second): 132300
Bytes per Sample in all Channels (Block Align): 3
Bits per Sample: 24
Data Subchunk Size: 3425301
[WARNING] Data subchunk size does not match file size. Should be 3435047, but is: 3425301 (difference: 9746)
```

## Restoring Damaged Wave File Headers

This tool is capable of restoring damaged wave files under the following conditions:

- The wave file header (stored in the first 44 bytes of wave files) is damaged or contains errors
- The raw audio data is still stored in the file starting at byte 45 

The tool will write a valid wave file header and append the available raw audio data.
To restore damaged wave files, supply the `--restore` (short: `-r`) option along with a source and destination path. Source and destination path can either be:

- A source file and a destination file or
- A source directory and a destination directory

In the second case, the source directory will be scanned for wave files and the restored versions of the files will be saved in the destination folder.

If no further parameters are supplied, the following defaults are assumed:

- Sample Rate: 44,100 Hz
- Bits per Sample: 16
- Number of channels: 1 (Mono)

These values can be changed with the following parameters:

- Sample Rate: `-s` or `--sample_rate` 
- Bits per Sample: `-b` or `--bits_per_sample`
- Number of Channels: `-c` or `--channels`


Examples are provided below:

Restore wave files with 44,100 Hz sample rate, 16 bits per sample, Mono:

```
python3 waverecovery.py -r /path/to/directory/containing/wavefiles /path/to/destination/directory
```

Restore wave files with 44,100 Hz sample rate, 24 bits per sample, Mono:

```
python3 waverecovery.py -r -b 24 /path/to/directory/containing/wavefiles /path/to/destination/directory
```

Restore wave files with 96,000 Hz sample rate, 24 bits per sample, Mono:

```
python3 waverecovery.py -r -s 96000 -b 24 /path/to/directory/containing/wavefiles /path/to/destination/directory
```

Restore wave files with 96,000 Hz sample rate, 24 bits per sample, Stereo:

```
python3 waverecovery.py -r -s 96000 -b 24 -c 2 /path/to/directory/containing/wavefiles /path/to/destination/directory
```

# Donations

If this wave recovery tool helped you to restore your damaged wave files, I would appreciate a donation at <https://www.paypal.me/davehofmanndev>. Thank you very much! 