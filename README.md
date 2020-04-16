# Wave Recovery Tool

Tool to display WAVE/AIFF file header information and to restore corrupted WAVE/AIFF file headers.

This program was originally developed to recover damaged audio files which were destroyed due to a bug in the audio application _Logic_. See [this blog post](http://www.davehofmann.de/when-logic-destroys-your-audio-files/) for more details.

## License

Wave Recovery Tool is licensed under the terms of the GNU General Public License Version 3.

## Author

Wave Recovery Tool is developed by David Hofmann &lt;dev@davehofmann.de&gt;

## Prerequisites

To use the wave recovery tool, a [Python 3](https://www.python.org/downloads/) installation is required.

This tool is capable of reconstructing damaged WAVE and AIFF headers. This will only work if the raw audio data is still in the file, i.e. the file has a reasonable file size in respect to the duration of the recorded audio material (usually several megabytes). In a typical scenario where recovery is possible, one of the following things happen when you try to play the audio file:

* Logic displays the error `One or more audio files changed in length.`
* Audio players (like VLC, Audacity, Windows Media Player, QuickTime, iTunes) display errors
* You hear noise
* You simply hear nothing

## Step by Step Instructions

1. Download [Python 3](https://www.python.org/downloads/)
2. Install Python 3. If the installation provides an option to add Python 3 to your environment variables (especially the `PATH` variable), then enable it. You might have to look for "customized" or "advanced" options for that. Remember the location where Python 3 was installed.
3. On the [github page of Wave Recovery Tool](https://github.com/davehofmann/wave-recovery-tool), click the green **Clone or download** at the top right corner of the page, then click **Download ZIP** and save the ZIP file to your Desktop.
4. Extract the downloaded ZIP file. This should result in a folder named `wave-recovery-tool-master` containing the program on your Desktop.
5. Locate the damaged audio files. If you used Logic, these will be located near your project file in a folder named `Media/Audio Files`. If you saved your project to a `.logicx` container, the contents can be shown in Finder by right-clicking the `.logicx` file and choosing _Show Package Contents_.
6. Create a folder named `audio` on your Desktop and copy the damaged audio files into that folder. 
7. Open a terminal application. Depending on your operating system, it is called **Command Line**, **Terminal** or similar.
8. Each terminal has a so called **working directory**, which is the file system context for executed programs. Typically, the terminal starts in your user directory. On Windows, this might be something like `C:\Users\homersimpson`, on Unix-based/Mac systems it is something like `/Users/homersimpson`. This directory is sometimes abbreviated as `~`. When a terminal is started, the current working directory is usually your user directory. Enter the command `cd Desktop` and hit enter to make `Desktop` your working directory. Hint: you can usually use the TAB key to auto-complete the folder names.
9. Analyze the audio files in your `audio` folder by entering one of the following commands:
    * On Windows, enter: `python wave-recovery-tool-master\waverecovery.py audio`
    * On Unix-based/Mac systems, enter: `python3 wave-recovery-tool-master/waverecovery.py audio`
10. If it works, you see header information for the files in your audio folder. If you get an error like `command not found` or similar, try replacing `python` with `python3` and vice versa. If you still get the same error, refer to section *Locating Python 3* below.
11. In case you see any header errors (prefixed with [ERROR]) in the output of step 9, you can try to fix the files. For that, you simply have to add `-r` before `audio` and add a destination folder (we will call it `restored`) after audio. The resulting command lines look like this:
    * Windows: `python wave-recovery-tool-master\waverecovery.py -r audio restored`
    * Unix/Mac: `python3 wave-recovery-tool-master/waverecovery.py -r audio restored`
12. The command from step 11 will create a folder named `restored` on your Desktop and try to restore the audio files from the folder `audio` into the `restored` folder. Check if the folder was created and whether it contains files.
13. Check the results in the `restored` folder on your Desktop. **Start playback with low loudness levels**.
14. If the sound is distorted or you hear nothing, you have to repeat from step 11, but this time add other parameters (namely the sample rate, number of channels and/or bit rate you used during recording). Examples:
    * If the files were recorded with a bit depth of 24 bits then you have to add `-b 24` before `audio`.
    * If you used a sample rate of 48 kHz, you have to add `-s 48000` before `audio`.
    * If the files have two channels (i.e. stereo instead of mono), then you have to add `-c 2` before `audio`.
    * See section _Restoring Damaged WAVE/AIFF File Headers_ for more details.

### Locating Python 3
 
In case you get an error message like `command not found` in step 9, you have to replace `python` or `python3` with the absolute path to your python executable. On Windows, the command line looks like this:

```
"C:\Program Files\Python\Python37-32\python" waverecovery.py audio
```

Note that you have to add quotes around the python path if it contains spaces (like in `Program Files`). On Unix systems, the command like looks like:

```
/usr/local/bin/python3 waverecovery.py audio
```

Of course, you have to replace the python executable paths with the actual paths on your system where Python3 was installed (the path you remembered in step 1 of the step-by-step instructions).

## Usage

The tool provides two functionalities:

1. Displaying WAVE/AIFF file header information
2. Restoring corrupted WAVE/AIFF file headers

For all commands below, `python3` is assumed to be in the system's executable `PATH`. If your system reports that `python3` can not be found, its containing directory must either be added to the `PATH` variable or `python3` must be replaced with the absolute path to the Python 3 interpreter. The command `python3` must be replaced with `python` on some Windows systems. Also refer to the previous section *Locating Python 3* if you encounter problems.

### Displaying Header File Information

To display header information for a specific audio file, invoke the tool as follows:

```
python3 waverecovery.py /path/to/file.wav
```

The tool can also display audio header information for all files contained in a directory:

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

### Restoring Damaged WAVE/AIFF File Headers

This tool is capable of restoring damaged WAVE/AIFF files under the following conditions:

- The audio file header is damaged or contains errors
- The raw audio data is still stored in the file after the damaged header 

The tool will write a valid WAVE/AIFF file header and append the available raw audio data.
To restore damaged wave files, supply the `--restore` (short: `-r`) option along with a source and destination path. Source and destination path can either be:

- A source file and a destination file or
- A source directory and a destination directory

In the second case, the source directory will be scanned for audio files and the restored versions of the files will be saved in the destination folder.

If no further parameters are supplied, the following defaults are assumed:

- Sample Rate: 44,100 Hz
- Bits per Sample: 16
- Number of channels: 1 (Mono)

These values can be changed with the following parameters:

- Sample Rate: `-s` or `--sample_rate` 
- Bits per Sample: `-b` or `--bits_per_sample`
- Number of Channels: `-c` or `--channels`


Examples are provided below.

## Examples

Restore audio files with

- 44 kHz sample rate
- 16 bits per sample
- 1 channel (Mono)

```
python3 waverecovery.py -r audio restored
```

Restore audio files with

- 44 kHz sample rate
- 24 bits per sample
- 1 channel (Mono)

```
python3 waverecovery.py -r -b 24 audio restored
```

Restore audio files with

- 96 kHz sample rate
- 24 bits per sample
- 1 channel (Mono)


```
python3 waverecovery.py -r -s 96000 -b 24 audio restored
```

Restore audio files with

- 96 kHz sample rate
- 24 bits per sample
- 2 channels (Stereo)


```
python3 waverecovery.py -r -s 96000 -b 24 -c 2 audio restored
```

## Donations

If this wave recovery tool helped you to restore your damaged audio files, I would appreciate a donation at <https://www.paypal.me/davehofmanndev>. Thank you very much! 