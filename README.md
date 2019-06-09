# Wave Recovery Tool

Tool to display wave file header information and to restore corrupted wave file headers.

This program was originally developed to recover damaged wave files which were destroyed due to a bug in the audio application _Logic_. See [this blog post](http://www.davehofmann.de/when-logic-destroys-your-audio-files/) for more details.

## License

Wave Recovery Tool is licensed under the terms of the GNU General Public License Version 3.

## Author

Wave Recovery Tool is developed by David Hofmann &lt;dev@davehofmann.de&gt;

## Prerequisites

To use the wave recovery tool, a [Python 3](https://www.python.org/downloads/) installation is required.

Furthermore, a copy of wave recovery tool needs to be downloaded or cloned with `git` using the green **Clone or download** button on the top right corner of this page. All commands below must be executed in the cloned or downloaded and extracted directory containing the file `waverecovery.py`.

For all commands below, `python3` is assumed to be in the system's executable `PATH`. If your system reports that `python3` can not be found, its containing directory must either be added to the `PATH` variable or `python3` must be replaced with the absolute path to the Python 3 interpreter.

### Step by Step Instructions

Here are more detailed instructions in case the previous section was not clear enough:

1. Download [Python 3](https://www.python.org/downloads/)
2. Install Python 3. If the installation provides an option to add Python 3 to your environment variables (especially the `PATH` variable), then use this option. You might have to look for "customized" or "advanced" options for that. Remember the location where you installed Python 3.
3. On the [github page of Wave Recovery Tool](https://github.com/davehofmann/wave-recovery-tool), click the green **Clone or download** at the top right corner of the page, then click **Download ZIP** and save the ZIP file to a location of your choice (e.g. Desktop).
4. Extract the downloaded ZIP file. This should result in a folder named `wave-recovery-tool-master` containing the program.
5. Open a terminal application. Depending on your operating system, it is called **Command Line**, **Terminal** or similar.
6. The terminal has a so called **working directory**, which is the file system context for executed programs. Typically, the terminal starts in your user directory. On Windows, this might be something like `C:\Users\homersimpson`, on Unix-like systems it is something like `/Users/homersimpson`. This directory is sometimes abbreviated as `~`.
7. Use the command `cd` (change directory) to navigate to the extracted ZIP directory. Example: `cd Desktop\wave-recovery-tool-master` on Windows, `cd Desktop/wave-recovery-tool-master` on Unix systems. Hint: you can usually use the TAB key to auto-complete the folder names.
8. Check if you can run Python 3 and the wave recovery tool by entering one of the following commands: on Windows, use `python waverecovery.py` On Unix systems, use `python3 waverecovery.py`. If it works, you will see usage instructions for the tool similar to this:

```
usage: waverecovery.py [-h] [-r] [-s SAMPLE_RATE] [-b BITS_PER_SAMPLE]
                       [-c CHANNELS] [-v] [-V]
                       source_path [destination_path]
```

If you see this, you can continue in the next section and add parameters for your files after `waverecovery.py`.

In case you get an error message like `command not found`, you must replace `python` or `python3` with the absolute path to your python executable. On Windows, the command line looks like this:

```
"C:\Program Files\Python\Python37-32\python" waverecovery.py
```

Note that you have to add quotes around the python path if it contains spaces (like in `Program Files`). On Unix systems, the command like looks like:

```
/usr/local/bin/python3 waverecovery.py
```

Of course, you have to replace the paths with the actual paths on your system where Python3 was installed.

## Usage

The tool provides two functionalities:

1. Displaying wave file header information
2. Restoring corrupted wave file headers

### Displaying Header File Information

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

### Restoring Damaged Wave File Headers

This tool is capable of restoring damaged wave files under the following conditions:

- The wave file header (stored in the first 44 bytes of wave files) is damaged or contains errors
- The raw audio data is still stored in the file starting at byte 45 

The tool will write a valid wave file header and append the available raw audio data.
To restore damaged wave files, supply the `--restore` (short: `-r`) option along with a source and destination path. Source and destination path can either be:

- A source file and a destination file or
- A source directory and a destination directory

In the second case, the source directory will be scanned for wave files and the restored versions of the files will be saved in the destination folder.

Note that if corresponding files already exist in the destination path, these will not be overwritten for safety reasons. In case you want files to be overwritten, you have to delete the destination folder manually.

If no further parameters are supplied, the following defaults are assumed:

- Sample Rate: 44,100 Hz
- Bits per Sample: 16
- Number of channels: 1 (Mono)

These values can be changed with the following parameters:

- Sample Rate: `-s` or `--sample_rate` 
- Bits per Sample: `-b` or `--bits_per_sample`
- Number of Channels: `-c` or `--channels`


Examples are provided below:

Restore wave files with 44 kHz sample rate, 16 bits per sample, Mono:

```
python3 waverecovery.py -r /path/to/directory/containing/wavefiles /path/to/destination/directory
```

Restore wave files with 44 kHz sample rate, 24 bits per sample, Mono:

```
python3 waverecovery.py -r -b 24 /path/to/directory/containing/wavefiles /path/to/destination/directory
```

Restore wave files with 96 kHz sample rate, 24 bits per sample, Mono:

```
python3 waverecovery.py -r -s 96000 -b 24 /path/to/directory/containing/wavefiles /path/to/destination/directory
```

Restore wave files with 96 kHz sample rate, 24 bits per sample, Stereo:

```
python3 waverecovery.py -r -s 96000 -b 24 -c 2 /path/to/directory/containing/wavefiles /path/to/destination/directory
```

## Donations

If this wave recovery tool helped you to restore your damaged wave files, I would appreciate a donation at <https://www.paypal.me/davehofmanndev>. Thank you very much! 