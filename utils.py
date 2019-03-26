#!/usr/local/bin/python3
# encoding: utf-8
'''
 -- Wave Recovery Tool Utilities
 
Utility functions for the wave recovery tool.

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

__date__ = '2019-03-25'
__updated__ = '2019-03-26'

def print_error(message):
    print("[ERROR]", message)
    
def print_warning(message):
    print("[WARNING]", message)
    
def print_with_condition(condition, message):
    if condition:
        print(message)
        
def warning_with_condition(condition, message):
    if condition:
        print_warning(message)
        
def error_with_condition(condition, message):
    if condition:
        print_error(message)

def print_separator():
    print("-"*42)
    
def byte_string_to_hex(byte_string):
    return " ".join(["%02X" % x for x in byte_string]).strip()