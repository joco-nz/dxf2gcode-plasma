'''

global constants
    
    see http://code.activestate.com/recipes/65207/
    
Created on 14.12.2009

@author: mah
'''


import const
import logging

# user "configurable"

const.answer = 42

PROGRAM_VERSION  = "47.11"
PROGNAME =  'dxf2gcode'

CONFIG_EXTENSION = '.cfg'
DEFAULT_CONFIG_FILE = 'config/dxf2gcode' + CONFIG_EXTENSION

# this environment variable overrides  DEFAULT_CONFIG_FILE
DXF2GCODE_CONFIG  = 'DXF2GCODE_CFG' 


# log related
DEFAULT_LOGFILE  = 'dxf2gcode.log'
STARTUP_LOGLEVEL = logging.DEBUG

CONSOLE_LOGLEVEL = logging.ERROR
FILE_LOGLEVEL    = logging.WARNING
WINDOW_LOGLEVEL  = logging.INFO

# plugin related
# these methods must exist
REQUIRED = ['__init__', 'plugin_tag', 'describe','menu_entry', 'version', 'cleanup']
# one of these must exist, otherwise it's pretty useless
EXPORTER = 'export'
TRANSFORMER = 'transform'



# do not touch below

