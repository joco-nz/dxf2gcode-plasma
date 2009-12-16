'''
globalconfig:

    place for global constants
    program arguments & options handling 
    reading dxf2gcode.cfg  .ini file and merge with options
    logging infrastructure
    exceptions for dxf2gcode
    helper functions needed in more than one place

TODO

project-directory 
modifiy spec 
    as per parameters?
    per platform?
    


Created on 13.12.2009

@author: Michael Haberler
'''



#from constants import *

import os
import sys
from time import asctime

import logging
from optparse import OptionParser
from configobj import ConfigObj,flatten_errors
from validate import Validator
from dotdictlookup import DictDotLookup

PROGRAM_VERSION  = "47.11"
PROGNAME =  'dxf2gcode'

DEFAULT_CONFIG_FILE = 'config/dxf2gcode.cfg' 
# this environment variable overrides  DEFAULT_CONFIG_FILE
DXF2GCODE_CONFIG  = 'DXF2GCODE_CFG' 


CONSOLE_LOGLEVEL = logging.ERROR
FILE_LOGLEVEL    = logging.WARNING
WINDOW_LOGLEVEL  = logging.INFO
# for debugging startup problmes log to console
# FIXME set to logging.ERROR eventually - otherwise verbose startup
STARTUP_LOGLEVEL = logging.DEBUG
DEFAULT_LOGFILE  = 'dxf2gcode.log'
#
NEWPROJ_DEFDIRS = ['config','dxf','ngc','varspace','plugins' ]


# if the config file has syntax errors, move it out
# of the way and create a new default cfg
# if this is false, there isnt much to do but exit badly

RENEW_ERRORED_CFG = True


# config file format spec
# see http://www.voidspace.org.uk/python/validate.html
# and http://www.voidspace.org.uk/python/configobj.html
# if you make any changes to config_spec
# always increment specversion default so an old .ini file
# can be detected

CONFIG_VERSION = "22"


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
    project_dir = string(default=".")
    import_dir = string(default="./dxf")
    output_dir = string(default="./ngc")

    # search here for exporter + transformer plugins
    plugin_dir = string(default=".")
    # plugin varspaces are stored here
    varspace_dir = string(default="./varspace")
    
    
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



class Log:
    '''
    handle 3 log streams:
        console
        file
        message window
    '''
    def __init__(self,tag,console_loglevel):
        self.file_handler = None
        self.window_handler = None
        self.logger = logging.getLogger(tag)
        self.logger.setLevel(logging.DEBUG)

        # always log to the console window
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s:%(funcName)s:%(lineno)d - %(message)s"))
        self.console_handler.setLevel(self._cvtlevel(console_loglevel))
        self.logger.addHandler(self.console_handler)

    # allow  'INFO' or logging.INFO  args
    def _cvtlevel(self,level):
        if isinstance(level,basestring):
            return logging._levelNames[level]
        else:
            return level

    # logging to file + window - explicitely enabled
    def add_file_logger(self,logfile=DEFAULT_LOGFILE,log_level=FILE_LOGLEVEL):
        
        self.file_handler = logging.FileHandler(logfile)
        self.file_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s:%(funcName)s:%(lineno)d  - %(message)s"))
        self.file_handler.setLevel(self._cvtlevel(log_level))
        self.logger.addHandler(self.file_handler)
    
    def add_window_logger(self, log_level=WINDOW_LOGLEVEL):
        
        self.window_handler = logging.StreamHandler()
        self.window_handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        self.window_handler.setLevel(self._cvtlevel(log_level))
        self.logger.addHandler(self.window_handler)
        
    def set_window_logstream(self,stream=sys.stderr):
        if self.window_handler:
            self.window_handler.stream = stream
        
    def set_window_loglevel(self,log_level):
        if self.window_handler:
            self.window_handler.setLevel(self._cvtlevel(log_level))
    
    def set_file_loglevel(self,log_level):
        if self.file_handler:
            self.file_handler.setLevel(self._cvtlevel(log_level))
                      
    def set_console_loglevel(self,log_level):
        if self.console_handler:
            self.console_handler.setLevel(self._cvtlevel(log_level))
   
class GlobalConfig:
    '''
    setup logging
    parse command line options
        options are available 'flattened', e.g. self.option.debug  
    read config file, generating a default if needed
        config file values are available 'flattened' like self.config.section.variable  

    '''
    def __init__(self):
        self.n_errors = 0
        
        self.log = Log(sys.argv[0],console_loglevel=STARTUP_LOGLEVEL)
        logger = self.log.logger

        self.current_directory = os.getcwd()  
        
        self.platform = ""  
        if os.name == "posix" and sys.platform == "darwin":
            self.platform = "mac"
        # Fixme - windows test
        # fixme - linux test

    
        parser = OptionParser()

        parser.add_option("-d", "--debug",
                          action="count", dest="debug", default=0,
                          help="increase debug level - repeat option for more output")
        parser.add_option("-v", "--version",
                          action="store_true", dest="printversion", default=False,
                          help="display program version")
        
        parser.add_option("-c", "--config-file",
                          action="store", metavar="FILE", dest="config_file", default=None,
                          help="use FILE as global config file, create default config if none found")        

        parser.add_option("-p", "--project-directory",
                          action="store", metavar="DIR", dest="project_directory", default=None,
                          help="use DIR as place for dxf,ngc,config,varspace,plugin directoryies")    
        parser.add_option("-P", "--plugin-directory",
                          action="store", metavar="DIR", dest="plugin_directory", default=None,
                          help="search DIR for plugins")        
        parser.add_option("-I", "--import-directory",
                          action="store", metavar="DIR", dest="import_directory", default=None,
                          help="use DIR for DXF input")  
        parser.add_option("-O", "--output-directory",
                          action="store", metavar="DIR", dest="output_directory", default=None,
                          help="use DIR for export output (like G-code)")         
        parser.add_option("-e", "--exporter-directory",
                          action="store", metavar="DIR", dest="exporter_directory", default=None,
                          help="look for/store exporter parameter files in DIR")     
        parser.add_option("-V", "--varspace-directory",
                          action="store", dest="varspace_directory", default=False,
                          help="verbose output to message window") 
        
        
        
        parser.add_option("-C", "--create-project-directory",metavar="DIR",
                          action="store", dest="new_project_dir", default=None,
                          help= "initialize DIR as a project and use like --project-directory DIR. \
                          create subdirectory config and default config/dxf2gcode.cfg with the current \
                          option setting (-I,-O,-e)")
        parser.add_option("-L", "--logfile",
                          action="store", dest="logfile", default=None,metavar="FILE",
                          help="log to FILE")

        (self.options, self.args) = parser.parse_args()
     
        if self.options.new_project_dir:
            path = os.path.abspath(self.options.new_project_dir)
            if os.path.isdir(path):
                logger.error("create project directory: %s already exists" % path)
                raise OSError
            else:
                try:
                    os.makedirs(path)
                except OSError as (error,strerror,filename):
                    logger.error("can't create directory %s: %s" % (path,strerror))
                    raise
                logger.debug("created project directory %s" % (path))
                for d in NEWPROJ_DEFDIRS:
                    os.mkdir(os.path.join(path, d))
                    logger.debug("created %s subdirectory %s" % (d))
                self.config_file = os.path.join(path,DEFAULT_CONFIG_FILE)

     
        if self.options.logfile:
            self.log.add_file_logger(self,logfile=self.options.logfile)  
             
        # merge in options from config file
        # program arguments override

        # pecking order for config file:
        # 1. explicit -C <configfile>
        # 2. Use environment
        # 3. Use built-indefault 
        if self.options.config_file:
            self.config_file = self.options.config_file
        else:
            self.config_file = os.getenv(DXF2GCODE_CONFIG, DEFAULT_CONFIG_FILE)
 
        # try hard to read a config file
#        (self.configvars,n_errors) = self._get_config(self.config_file)
        (self.config_dict,n_errors) = self._get_config(self.config_file)
   
        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.config = DictDotLookup(self.config_dict)
        
        # determine project directory
        if self.options.project_directory:  # cmd line -P
            self.project_directory = self.options.project_directory 
        else:
            if self.config.Paths.project_dir: # take from .cfg
                self.project_directory = self.config.Paths.project_dir
        
        
        # special-case abspath arg (emc2) : use dirname() as project_directory
        #    if os.path.abspath(dirname(arg)

        if not self.options.logfile:
            if len(self.config.Logging.logfile) > 0: 
                self.log.add_file_logger(logfile=self.config.Logging.logfile)
                self.log.set_file_loglevel(self.config.Logging.file_loglevel)

        # now adjust to values from config 
        self.log.set_console_loglevel(log_level=self.config.Logging.console_loglevel)        
 
        # CK: execute this code once the logging window is established
        if False:
            self.log.add_window_logger(log_level=self.self.config.Logging.window_loglevelconfig)
            self.log.set_window_logstream(stream=sys.stderr) # set to window file handle
            # change window loglevel like so:
            #self.log.set_window_loglevel(self,log_level)
            
            
        if self.n_errors:
            logger.warning("%d error(s) reading '%s'" % (self.n_errors,self.config_file))
        else:
            logger.info("config read sucessfully")
          
            

        #logger.error("see what happens now")
        print "options = ", self.options
        print "config = ", self.config
        print "args = ",self.args
        print "n_errors = ",n_errors
    
    def _get_config(self,config_file):
        '''
        try to arrive at, and read a valid config file
            if the config dir doesnt exist, create it
            if the file doesnt exist, create a default config derived from CONFIG_SPEC
            at this point, a config file does exist - new or old, so read it
            if the version number mismatches or the config file doesnt
            validate, rename the bad config file by adding a time stamp, re-create a
            default file and read that
        '''
        configvars = dict()
        logger = self.log.logger    # shorthand

        # create config subdir and default config if needed
        if not os.path.isfile(config_file):
            config_dir = os.path.dirname(config_file)
            if not os.path.isdir(config_dir) and (len(config_dir) > 0):
                try:
                    os.makedirs(config_dir)
                except OSError as (error,strerror,filename):
                    logger.error("can't create directory %s: %s" % (config_dir,strerror))
                    raise
                else:
                    logger.info("created config directory %s" % (config_dir))

            # we have a directory, create default config
            try:
                self._write_default_config_file(config_file,CONFIG_SPEC)
            except Exception as inst:
                logger.error(inst)
                logger.error("unexpected error creating default config %s" % (config_file))
                raise                
            else:
                logger.info("created default config file %s" % (config_file))
        # we have a default config file
        keep_trying = True
        while keep_trying:
            try:
                n_errors = 0
                (configvars,result) = self._read_config_file(config_file, CONFIG_SPEC)
                error_dict = flatten_errors(configvars,result)
                n_errors += len(error_dict)
                if n_errors:
                    logger.warning("%d error(s) reading %s :" %(n_errors,config_file))

                for entry in error_dict: 
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if error == False:
                        error = 'Missing value or section.'
                    logger.warning(section_string + ' = ' + str(error))
                    keep_trying = False 

                fileversion = configvars['Version']['config_version']
                if fileversion != CONFIG_VERSION:
                    logger.warning('config file versions do not match - internal: "%s", config file "%s"' %(CONFIG_VERSION,fileversion))       
                else:
                    logger.debug("config file version ok: '%s'" % (fileversion))

                # giive up on this cfg file?
                if (fileversion != CONFIG_VERSION) or (RENEW_ERRORED_CFG and (n_errors > 0)):
                    # This config file wont work.
                    # we move the file out of the way, create
                    # a new default and retry.
                    tag = asctime()
                    badfilename = config_file + '.' + tag.replace(' ','-')
                    logger.debug("trying to rename bad cfg %s to %s" % (config_file,badfilename))
                    try:
                        os.rename(config_file,badfilename)
            
                    except OSError  as (e,msg):
                        logger.error("rename(%s,%s) failed: %s - %s" % (config_file,badfilename,e,msg))
                        raise

                    else:
                        logger.info("renamed bad config to %s" % (badfilename))
                        # create a fresh default cfg
                        (configvars,result) = self._write_default_config_file(config_file,CONFIG_SPEC)
                        # a new file exists, read it once more so we 
                        logger.info("created default cfg %s" % (config_file))
                        keep_trying = True                              
                else:
                    keep_trying = False # it's either this or that way                                    
                
            except IOError as (e,msg):
                logger.error("cant read %s: %s %s " % (config_file,e,msg))
                n_errors += 1
                keep_trying = False 
    
        return (configvars,n_errors)
        
    def _read_config_file(self,path,spec):
        # file exists, read & validate it
        # raises IOError if path not accessible
 
        _cfg = ConfigObj(path, configspec=spec, interpolation=False,
                        file_error=True,raise_errors=False)
        vdt = Validator()
        res = _cfg.validate(vdt, preserve_errors=True)
        return (_cfg,res)
    
    def _write_default_config_file(self,path,configspec):
        # derive config file with defaults from spec
        _cfg = ConfigObj(configspec=configspec)
        vdt = Validator()
        res = _cfg.validate(vdt, copy=True)
        _cfg.filename = path
        _cfg.write()
        return (_cfg,res) 
            
        
        
if __name__ == "__main__":

    cfg = GlobalConfig()
    