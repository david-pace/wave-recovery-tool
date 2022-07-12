#!/usr/bin/env python3
# encoding: utf-8
'''
 -- Wave Recovery Tool

Command line interface for Wave Recovery Tool.

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
along with this program.  If not, see <https://www.gnu.org/licenses/>.

@author:     David Pace

@license:    GNU General Public License Version 3

@contact:    dev@davidpace.de

@deffield    updated: Updated
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

from waveheaderprocessor import WaveHeaderProcessor

__all__ = []
__version__ = '1.0.0'
__date__ = '2019-03-25'
__updated__ = '2022-07-13'

DEBUG = 0
TESTRUN = 0
PROFILE = 0

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by David Pace on %s.
  Copyright 2019 David Pace. All rights reserved.

  Licensed under the GNU General Public License Version 3
  https://www.gnu.org/licenses/lgpl-3.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-r", "--restore", dest="restore", action="store_true", help="restores corrupted wave file headers. Scans the given source path for wave files and writes the file(s) with restored headers to the given destination file or directory. [default: %(default)s]")
        parser.add_argument("-s", "--sample_rate", dest="sample_rate", type=int, help="sample rate to write in the wave file header [default: %(default)s]", default=44100)
        parser.add_argument("-b", "--bits_per_sample", dest="bits_per_sample", type=int, help="bits per sample (e.g. 8, 16 or 24 bit) used to record/write the damaged audio file(s) [default: %(default)s]", default=16)
        parser.add_argument("-c", "--channels", dest="channels", type=int, help="number of audio channels (1=Mono, 2=Stereo) in the damaged audio file(s) [default: %(default)s]", default=1)
        parser.add_argument("-f", "--force", dest="force", action="store_true", help="restores file headers even if no errors were found [default: %(default)s]")
        parser.add_argument("-a", "--application", dest="application", help="specifies which application encoded the damaged audio file. Possible values: logic (Apple Logic Pro), live (Ableton Live) [default: %(default)s]", default="logic")
        
        parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="activate verbose output [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        
        parser.add_argument(dest="source_path", help="path to source wave file or directory containing wave files [default: %(default)s]", metavar="source_path", default=os.getcwd())
        parser.add_argument(dest="destination_path", help="path to directory in which restored wave files should be saved [default: %(default)s]", metavar="destination_path", nargs='?')

        # Process arguments
        args = parser.parse_args()
        
        restore = args.restore

        source_path = args.source_path
        destination_path = args.destination_path
        
        verbose = args.verbose
        
        application = args.application
        
        sample_rate = args.sample_rate
        bits_per_sample = args.bits_per_sample
        num_channels = args.channels
        
        force = args.force
        
        if verbose:
            print("Verbose mode on")
            print("Restore mode: {}".format(restore))
            print("Force flag: {}".format(force))
            
            print("Application: {}".format(application))
            
            print("Sample rate: {}".format(sample_rate))
            print("Bits per sample: {}".format(bits_per_sample))
            print("Number of channels: {}".format(num_channels))
            
            print("Source path: {}".format(source_path))
            print("Destination path: {}".format(destination_path))
            
        if restore:
            if destination_path is None:
                raise CLIError("Destination path is required for the restore operation.")
            
            processor = WaveHeaderProcessor()
            processor.repair_audio_file_headers(source_path, destination_path, sample_rate, bits_per_sample, num_channels, verbose, force, application)
            
        else:
            processor = WaveHeaderProcessor()
            processor.display_header_infos(source_path)
            
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-v")
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = '_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())