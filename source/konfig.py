# -*- coding: iso-8859-1 -*-
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
"""
@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects

@purpose:  TBD

@author: Michael Haberler 
@since:  23.12.2009
@license: GPL
"""

import sys

from varspace import  VarSpace
import globals as g
import constants as c
from logger import Log

class Plugin(VarSpace):



    def __init__(self):       
        
        self.DESCRIPTION = 'global settings'
        self.VERSION = '0.01'
        self.CLONABLE = False
        self.VISIBLE_AT_STARTUP = False
        
#        self.shapeset_handlers = {}
#        """dictionary of function names and menu entries"""

        

        self.SPECVERSION = 32
        self.SPECNAME = str('''
            # do not edit the following section name:
                [Version]
            
                # do not edit the following value:
                specversion =  integer(default=''' + 
                str(self.SPECVERSION) + ''')
        
                
                [''' + c.VARIABLES + 
                
                ''']
                
                # look here for DXF files
                import_dir = string(default="dxf")
                
                # store gcode output here 
                output_dir = string(default="ngc")
            
                # search here for plugins
                plugin_dir = string(default="plugins")
                
                # plugin varspaces are stored here
                varspaces_dir = string(default="varspaces") 
                
                # Set to True for running under EMC       
                write_to_stdout = boolean(default=False)
                
                # wether to save a plugin's varspace if the instance is deleted
                save_on_instance_delete = boolean(default=True)
                
                point_tolerance = float(default= 0.01)
                spline_check = boolean(default=True)
                fitting_tolerance = float(default= 0.01)
                
                pscmd = string(default="/opt/local/bin/pstoedit")
                psoptions = string(default="-f dxf -mm")
                psextensions = string(default=".ps ")
        
                log2file = boolean(default=False)

                # set this to 'logfile = <pathname>' to turn on file logging
                # or give the '-L logfile' program option
                logfile = string(default="dxf2gcode.log")
                
                # log levels are one in increasing importance:
                #      DEBUG INFO WARNING  ERROR CRITICAL
                # log events with importance >= loglevel are logged to the
                # corresponding output
                
                # this really goes to stderr
                console_loglevel = string(default='DEBUG')
              
                file_loglevel = string(default='DEBUG')
                
                # logging level for the message window
                window_loglevel = string(default='INFO')
                
                # backwards compatibility
                global_debug_level = integer(min=0,max=5,default=3)
            
    
        
        [''' + c.UI_VARIABLES + 
        ''']
        
        # Variables listed here are displayed in the UI and are editable
        # the string value is the descriptive text displayed in a Label
        # variables from the Variables section can be interpolated into
        # e.g. Label names
        
        [[Import_Parameters]]
            point_tolerance =      string(default="Tolerance for common points [mm]:")
            fitting_tolerance =    string(default="Tolerance for curve fitting [mm]:")
            spline_check =         string(default="Spline check")
            
        [[Filters]]
    
            [[[PStoEdit]]]
            
                    pscmd = string(default="location:")
                    psoptions = string(default="options:")
                    psextensions = string(default="extensions:")
    
        [[Logging]]
                log2file = string(default="log to file")
                logfile = string(default="Logfile:")
                console_loglevel = string_list(default=list('Console logging:', 'DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL'))
                file_loglevel = string_list(default=list('File logging:', 'DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL'))
                window_loglevel = string_list(default=list('Window logging:', 'DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL'))
                #global_debug_level = string(default="Debug level:")
 
        ''').splitlines()
        """ format, type and default value specification of the global config file"""
    
        
    def cleanup(self):
        g.logger.debug("cleanup plugin %s" % (self.instance_name))

    def initialize(self):

        self.create_pane()
        self.add_config_items()
        self.add_callback('window_loglevel', lambda name, old, new:g.log.set_window_loglevel(new))
        
        self.add_callback('file_loglevel', lambda name, old, new:g.log.set_file_loglevel(new))
        self.add_callback('console_loglevel', lambda name, old, new:g.log.set_console_loglevel(new))
        self.add_callback('log2file', lambda name, old, new:g.log.change_file_logging(new))

        self.display_pane(self.instance_name)
        return True

        
    def varchanged_callback(self, name, oldvalue, newvalue):
        g.logger.info("%s.%s(%s %s -> %s)  called" % 
                             (self.instance_name, sys._getframe(0).f_code.co_name, name, oldvalue, newvalue))

                 
