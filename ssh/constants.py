# -*- coding: iso-8859-15 -*-
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

'''

global constants
    
    see http://code.activestate.com/recipes/65207/ for module const
Michael Haberler  20.12.2009
'''

import const

import logging

# user "configurable"

const.answer = 42

APP_VERSION  = "47.11"
APPNAME =  'dxf2gcode'

CONFIG_EXTENSION = '.cfg'
PY_EXTENSION = '.py'
#DEFAULT_EXTENSION = '.def'
#rename unreadable config/varspace files to .bad
BAD_CONFIG_EXTENSION = '.bad'
DEFAULT_CONFIG_DIR = 'config/' 

# this environment variable overrides  DEFAULT_CONFIG_DIR
DXF2GCODE_CONFIG_DIR  = 'DXF2GCODE_CFG' 

# config files - magic section tags
# No space in these strings - must be valid Python identifiers
VARIABLES = 'Variables'
UI_VARIABLES = 'Appearance'
FRAMED  = 'FRAMED'
UNFRAMED = 'UNFRAMED'



# log related
DEFAULT_LOGFILE  = 'dxf2gcode.log'
STARTUP_LOGLEVEL = logging.DEBUG

CONSOLE_LOGLEVEL = logging.ERROR
FILE_LOGLEVEL    = logging.WARNING
WINDOW_LOGLEVEL  = logging.INFO

# plugin related
# these methods must exist
REQUIRED = ['__init__', 'cleanup', 'initialize',
            'DESCRIPTION','VERSION','CLONABLE','HIDDEN_AT_STARTUP',
            'SPECVERSION','SPECNAME']
# all methods which can be applied to a shapeset are listed here:
METHOD_DICT = 'shapeset_handlers'


