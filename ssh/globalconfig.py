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
"""

 
 
    # config file format spec
    # see http://www.voidspace.org.uk/python/validate.html
    # and http://www.voidspace.org.uk/python/configobj.html
    # if you make any changes to config_spec
    # always increment specversion default so an old .ini file
    # can be detected

@newfield purpose: Purpose
@newfield sideeffect: Side effect, Side effects
@purpose:  program arguments & options handling, read the config file
@author: Michael Haberler 
@since:  21.12.2009
@license: GPL
"""

import os
import sys
import logging
from optparse import OptionParser
from configobj import ConfigObj,flatten_errors
from validate import Validator

import constants as c
import globals as g
from d2gexceptions import *
from dotdictlookup import DictDotLookup




DEFDIR_DICT = {'config' : None,
               'dxf' : 'import_dir',
               'ngc' : 'output_dir' ,
               'varspaces' : 'varspaces_dir',
               'plugins' : 'plugin_dir' }
"""project subdirectories and their corresponding config variable names"""



RENEW_ERRORED_CFG = True
""" 
if the config file has syntax errors, move it out
of the way and create a new default cfg
if this is false, there isnt much to do but exit badly
"""




CONFIG_VERSION = "29"
"""
version tag - increment this each time you edit CONFIG_SPEC

compared to version number in config file so
old versions are recognized and skipped"
"""
    
CONFIG_SPEC = str('''
#  Section and variable names must be valid Python identifiers
#      do not use whitespace in names 

# do not edit the following section name:
    [Version]

    # do not edit the following value:
    config_version = string(default="'''  + \
    str(CONFIG_VERSION) + '")\n' + \
'''
    [Paths]
    # 
    # look here for DXF files
    import_dir = string(default="dxf")
    
    # store gcode output here 
    output_dir = string(default="ngc")

    # search here for exporter + transformer plugins
    plugin_dir = string(default="plugins")
    
    # plugin varspaces are stored here
    varspaces_dir = string(default="varspaces")
    
    
    [Depth_Coordinates]
    axis3_retract = float(default= 15.0)
    axis3_slice_depth = float(default= -1.5)
    axis3_safe_margin = float(default= 3.0)
    axis3_mill_depth = float(default= -3.0)
    
    [Axis_letters]
    ax1_letter = string(default="X")
    ax2_letter = string(default="Y")
    ax3_letter = string(default="Z")
    
    [Plane_Coordinates]
    axis1_start_end = float(default= 0)
    axis2_start_end = float(default= 0)
    
    [General]
    write_to_stdout = boolean(default=False)
    
    # wether to save a plugin's varspace if the 
    # instance is deleted
    save_on_instance_delete = boolean(default=True)
    
    [Route_Optimisation]
    mutation rate = float(default= 0.95)
    max. population = float(default= 20)
    max. iterations = float(default= 300)
    begin art = string(default="heurestic")
    
    [Import_Parameters]
    point_tolerance = float(default= 0.01)
    spline_check = boolean(default=True)
    fitting_tolerance = float(default= 0.01)
    
    [Tool_Parameters]
    diameter = float(default= 2.0)
    start_radius = float(default= 0.2)
    
    [Filters]
    pstoedit_cmd = string(default="/opt/local/bin/pstoedit")
    pstoedit_opt = list(default=list('-f', 'dxf', '-mm'))

    [Logging]
    
    # set this to 'logfile = <pathname>' to turn on file logging
    # or give the '-L logfile' program option
    logfile = string(default="")
    
    # log levels are one in increasing importance:
    #      DEBUG INFO WARNING  ERROR CRITICAL
    # log events with importance >= loglevel are logged to the
    # corresponding output
    
    # this really goes to stderr
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='DEBUG')
  
    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='DEBUG')
    
    # logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='INFO')
    
    # backwards compatibility
    global_debug_level = integer(min=0,max=5,default=3)


    [Feed_Rates]
    f_g1_plane = float(default=400)
    f_g1_depth = float(default=150)

''').splitlines()  
""" format, type and default value specification of the global config file"""
    

class GlobalConfig(object):

    def __init__(self, plugin_loader):        
        """
        setup logging
        parse command line options
        read config file, generating a default if needed
            - config file values are available 'flattened' like self.config.section.variable  
        raise an Exception if options,permissions etc are really badly screwed
        
        result (fine if self.n_errors = 0)
            - all config file variables have been merged with overriding
            cmd line options into self.config 
        
        options are available 'flattened', e.g. self.option.debug  

        
        self.config may differ from the config file if there were command
        line options - to save the current state, self.write_current_config(self.config_dir)
        
        @sideeffect:
        sets global.config to instance variable
            - global.config.options - command line options (dictionary)
            - gobal.config.varrs - the config file flattened as attribute hierarchy
                
                            
                Example: the variable specified in the config file fragment as per SPECNAME above::
                    [Paths]
                    import_dir = /home/mah/dxf
                    
                may be referred to in the plugin as::
                
                    self.vs.vars.Paths.import_dir
                            
        """
        self.n_errors = 0
        self.log = g.logger
        logger = self.log.logger



        parser = OptionParser()

        parser.add_option("-d", "--debug",
                          action="count", dest="debug", default=0,
                          help="increase debug level - repeat option for more output")
        parser.add_option("-v", "--version",
                          action="store_true", dest="printversion", default=False,
                          help="display program version")
        
        parser.add_option("-c", "--config-directory",
                          action="store", metavar="DIR", dest="config_dir", default=None,
                          help="use DIR to search for config.cfg and machine.cfg")        

        parser.add_option("-p", "--project-directory",
                          action="store", metavar="DIR", dest="project_dir", default=None,
                          help="use DIR as place for dxf,ngc,config,varspaces,plugin directoryies")    
        parser.add_option("-P", "--plugin-directory",
                          action="store", metavar="DIR", dest="plugin_dir", default=None,
                          help="search DIR for plugins")        
        parser.add_option("-I", "--import-directory",
                          action="store", metavar="DIR", dest="import_dir", default=None,
                          help="use DIR for DXF input")  
        parser.add_option("-O", "--output-directory",
                          action="store", metavar="DIR", dest="output_dir", default=None,
                          help="use DIR for export output (like G-code)")         
        parser.add_option("-V", "--varspaces-directory",
                          action="store", dest="varspaces_dir", default=False,
                          help="look for/store exporter parameter files in DIR")     
        parser.add_option("-C", "--create-project-directory",metavar="DIR",
                          action="store", dest="create_project_dir", default=None,
                          help= "initialize DIR as a project and use like --project-directory DIR. \
                          create subdirectory config and default config/dxf2gcode.cfg with the current \
                          option setting (-I,-O,-e)")
        parser.add_option("-D", "--default-config",
                          action="store", dest="default_config", default=False,
                          help= "create a default config when doing a --create-project-directory"
                                "instead of writing the current config")        
        parser.add_option("-L", "--logfile",
                          action="store", dest="logfile", default=None,metavar="FILE",
                          help="log to FILE")

        (self.options, self.args) = parser.parse_args()
        opt = self.options # shorthand
    
        if opt.project_dir and opt.create_project_dir:
            logger.error("--create-project-directory and --project-directory"
                          " options are mutually exclusive")
            raise OptionError

        # pecking order for config dir:
        # 1. explicit -C <configdir>
        # 2. if projectdir, user projectdir/config/config.cfg
        # 3. Use environment
        # 4. Use built-in default config/config.cfg
        if opt.config_dir:
            self.config_dir = opt.config_dir
        else:
            if opt.project_dir:
                self.config_dir = os.path.join(opt.project_dir,c.DEFAULT_CONFIG_DIR)
            else:
                # backwards compatibility: default config/dxf2gcode.cfg under program dir
                _def = os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
                _def = os.path.join(_def, c.DEFAULT_CONFIG_DIR)
                self.config_dir = os.getenv(c.DXF2GCODE_CONFIG_DIR, _def)
        logger.debug("using config directory %s" % (self.config_dir))


        # pseudo-plugins in program directory proper: config.py, machine.py
        _name = "config"
        self.config_plugin =  plugin_loader.activate(None,_name,os.path.join(self.config_dir,_name + c.CONFIG_EXTENSION))
        _name = "machine"
        self.machine_plugin = plugin_loader.activate(None,_name,os.path.join(self.config_dir,_name + c.CONFIG_EXTENSION))

#
#        # try hard to read a config file
#        self.n_errors = self.get_config(self.config_dir)
   
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.config = self.config_plugin.vars.Variables
        self.machine = self.machine_plugin.vars.Variables
        cfg = self.config #  shorthand

        # adjust to value from config 
        self.log.set_console_loglevel(log_level=cfg.console_loglevel)   
                              
        # merge options into config, program arguments override
        cfg.import_dir = opt.import_dir if opt.import_dir else cfg.import_dir
        cfg.output_dir = opt.output_dir if opt.output_dir else cfg.output_dir
        cfg.plugin_dir = opt.plugin_dir if opt.plugin_dir else cfg.plugin_dir
        cfg.varspaces_dir = opt.varspaces_dir if opt.varspaces_dir else cfg.varspaces_dir
        
        if opt.logfile:
            cfg.Logging.logfile = opt.logfile
            self.log.add_file_logger(self,logfile=opt.logfile)  
        else:
            if len(cfg.logfile) > 0:  # FIXME check for iswhite!!!
                self.log.add_file_logger(logfile=cfg.logfile)
                self.log.set_file_loglevel(cfg.file_loglevel)
   
        self.current_directory = os.getcwd()  
        self.app_directory = os.getcwd()  
        FOLDER=os.path.dirname(os.path.abspath(sys.argv[0])).replace("\\", "/")
        #Das momentane Verzeichnis herausfinden
        local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
     
        
        if opt.create_project_dir:
            path = os.path.abspath(opt.create_project_dir)
            if os.path.isdir(path):
                logger.error("create project directory: %s already exists" % path)
                raise OptionError
            else:
                try:
                    os.makedirs(path)
                except OSError, e:
                    logger.error("can't create directory %s: %s" % (path,e.strerror))
                    raise
                logger.debug("created project directory %s" % (path))
                if opt.default_config:
                    self.create_default_config(CONFIG_SPEC)
                for d in DEFDIR_DICT:
                    v = DEFDIR_DICT[d]
                    _dir = os.path.join(path, d)
                    os.mkdir(_dir)
                    logger.debug("created dir %s" % (_dir))
                    # adjust paths
                    if v:
                        self.config_dict['Paths'][v] = _dir
                        
                self.config_dir = os.path.join(path,c.DEFAULT_CONFIG_DIR)
                self.write_current_config(self.config_dir)
                if opt.default_config:
                    logger.debug("created default config in %s" % (self.config_dir))
                else:
                    logger.debug("created current config in %s" % (self.config_dir))

 
        # CK: execute this code once the logging window is established
        if False:
            self.log.add_window_logger(log_level=cfg.window_loglevelconfig)
            self.log.set_window_logstream(stream=sys.stderr) # set to window file handle
            # change window loglevel like so:
            #self.log.set_window_loglevel(self,log_level)
            
            
        if self.n_errors:
            logger.warning("%d error(s) reading '%s'" % (self.n_errors,self.config_dir))
        else:
            logger.info("config read sucessfully: %s",self.config_dir )
          
            


        