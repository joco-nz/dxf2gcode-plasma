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



from constants import *

import os
import sys
from time import asctime

import logging
from optparse import OptionParser
from configobj import ConfigObj,flatten_errors
from validate import Validator

# all defaults in upper case

PROGNAME =  'dxf2gcode'
CONSOLE_LOGLEVEL = logging.ERROR
FILE_LOGLEVEL    = logging.WARNING
WINDOW_LOGLEVEL  = logging.INFO
DEFAULT_LOGFILE  = 'dxf2gcode.log'

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

CONFIG_VERSION = "13"


#    [Paths]
#    save_path = /Users/mah/Documents/workspace/dxf2gcode-tkinter-haberler-gc/ngc
#    load_path = /Users/mah/Documents/workspace/dxf2gcode-tkinter-haberler-gc/dxf
#    pstoedit_opt = list(default=list('-f', 'dxf', '-mm'))



CONFIG_SPEC = str('''
# do not edit the following section name:
    [Version]

    # do not edit the following value:
    config_version = string(default="'''  + \
    str(CONFIG_VERSION) + '")\n' + \
'''

    
    [Depth Coordinates]
    axis3_retract = float(default= 15.0)
    axis3_slice_depth = float(default= -1.5)
    axis3_safe_margin = float(default= 3.0)
    axis3_mill_depth = float(default= -3.0)
    
    [Axis letters]
    ax1_letter = string(default="X")
    ax2_letter = string(default="Y")
    ax3_letter = string(default="Z")
    
    [Plane Coordinates]
    axis1_start_end = float(default= 0)
    axis2_start_end = float(default= 0)
    
    [General]
    write_to_stdout = boolean(default=False)
    
    [Route Optimisation]
    mutation rate = float(default= 0.95)
    max. population = float(default= 20)
    max. iterations = float(default= 300)
    begin art = string(default="heurestic")
    
    [Import Parameters]
    point_tolerance = float(default= 0.01)
    spline_check = boolean(default=True)
    fitting_tolerance = float(default= 0.01)
    
    [Tool Parameters]
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
    console_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='ERROR')
  
    file_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='DEBUG')
    
    # logging level for the message window
    window_loglevel = option('DEBUG', 'INFO', 'WARNING', 'ERROR','CRITICAL', default='DEBUG')
    
    # backwards compatibility
    global_debug_level = integer(min=0,max=5,default=3)

    
    [Feed Rates]
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
    def __init__(self,prog_name):
        self.console_handler = None
        self.file_handler = None
        # always log to the message window
        self.logger = logging.getLogger(prog_name)
        self.logger.setLevel(logging.DEBUG)

        self.window_handler = logging.StreamHandler()
        self.window_handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        self.window_handler.setLevel(WINDOW_LOGLEVEL)

        self.logger.addHandler(self.window_handler)

    # allow strings like 'INFO' or logging.INFO type args
    def _cvtlevel(self,level):
        if isinstance(level,basestring):
            return logging._levelNames[level]
        else:
            return level

    # logging to file & console - explicitely enabled
    def add_file_logger(self,logfile=DEFAULT_LOGFILE,log_level=FILE_LOGLEVEL):
        
        self.file_handler = logging.FileHandler(logfile)
        self.file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.file_handler.setLevel(self._cvtlevel(log_level))
        self.logger.addHandler(self.file_handler)
    
    def add_console_logger(self, log_level=CONSOLE_LOGLEVEL):
        self.console_handler = logging.StreamHandler()
        self.console_handler.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
        self.console_handler.setLevel(self._cvtlevel(log_level))
        self.logger.addHandler(self.console_handler)


    def set_window_loglevel(self,log_level):
        self.window_handler.setLevel(self._cvtlevel(log_level))
    
    def set_window_logstream(self,stream=sys.stderr):
        self.window_handler.stream = stream
    
    def set_file_loglevel(self,log_level):
        self.file_handler.setLevel(self._cvtlevel(log_level))
                      
    def set_console_loglevel(self,log_level):
        self.console_handler.setLevel(self._cvtlevel(log_level))
   
                
def cleanup_and_exit(obj,returncode, msg=None):
    if msg:
        print msg
    # add any sensible cleanup actions here

    sys.exit(returncode)


class GlobalConfig:
    
    def __init__(self):
        self.configvars = dict()
        self.n_config_errors = 0

        self.current_directory = os.getcwd()  
        
        self.platform = ""  
        if os.name == "posix" and sys.platform == "darwin":
            self.platform = "mac"
        # Fixme - windows test
        # fixme - linux test
        
        self.config_suffix = '.cfg'

        self.config_subdir = 'config'
        self.config_basename = 'dxf2gcode'
        
        # default to current directory
        self.config_dir = os.path.join(self.current_directory,self.config_subdir)
        self.config_file = os.path.join(self.config_dir,self.config_basename + self.config_suffix)

        self.log = Log(PROGNAME)
        logger = self.log.logger    # shorthand
        
        #self.log.set_window_loglevel('DEBUG') # works
        
    
        parser = OptionParser()
        parser.add_option("-V", "--verbose",
                          action="store_true", dest="verbose", default=False,
                          help="verbose output to message window")
        parser.add_option("-d", "--debug",
                          action="count", dest="debug", default=0,
                          help="increase debug level - repeat option for more output")
        parser.add_option("-v", "--version",
                          action="store_true", dest="printversion", default=False,
                          help="display program version")
        parser.add_option("-c", "--config-file",
                          action="store", metavar="FILE", dest="config_file", default=self.config_file,
                          help="use FILE as global config file, create default config if none found")   
        parser.add_option("-p", "--project-directory",
                          action="store", metavar="DIR", dest="project_directory", default=None,
                          help="use DIR for DXF input, export output and parameter storage")    
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
        parser.add_option("-C", "--create-project-directory",metavar="DIR",
                          action="store_true", dest="create_projectdir", default=False,
                          help= "initialize DIR as a project - for later use with --project-directory DIR. \
                          create subdirectory config and default config/dxf2gcode.cfg with the current \
                          option setting (-I,-O,-e)")
        parser.add_option("-L", "--logfile",
                          action="store", dest="logfile", default=None,metavar="FILE",
                          help="log to FILE")

        (self.options, self.args) = parser.parse_args()
        
        # merge in options from config file
        # program arguments override

        # override config file path
        if self.options.config_file:
            self.config_file = self.options.config_file
            self.config_dir = os.path.dirname(self.config_file)        
        
        # try hard to read a config file
        self._get_config()
        
        if self.options.logfile:
            self.log.add_file_logger(logfile=self.options.logfile)
        else:
            if len(self.configvars['Logging']['logfile']) > 0:
                self.log.add_file_logger(logfile=self.configvars['Logging']['logfile'],
                                       log_level=self.configvars['Logging']['file_loglevel'])
        
        self.log.add_console_logger(log_level=self.configvars['Logging']['console_loglevel'])        
        self.log.set_window_loglevel(log_level=self.configvars['Logging']['window_loglevel'])

        
        
        if self.n_config_errors:
            logger.warning("%d error(s) reading '%s'" % (self.n_config_errors,self.config_file))
        else:
            logger.info("config read sucessfully")
          
            
        # special-case abspath arg (emc2)


        print "options = ", self.options
        print "args = ",self.args
    
    def _get_config(self):
        '''
        try to arrive at, and read a valid config file
            if the config dir doesnt exist, create it
            if the file doesnt exist, create a default config derived from CONFIG_SPEC
            at this point, a config file does exist - new or old
            read it
            if the version number mismatches or the config file doesnt
            validate, rename the bad config file by adding a time stamp, re-create a
            default file and read that
        '''

        logger = self.log.logger    # shorthand

        # create config subdir and default config if needed
        if not os.path.isfile(self.config_file):
            if not os.path.isdir(self.config_dir):
                if os.mkdir(self.config_dir):
                    logger.error("can't create directory %s" % (self.config_dir))
                    cleanup_and_exit(self, -1)
                else:
                    logger.info("created config directory %s" % (self.config_dir))

            # we have a directory, create default config
            try:
                self._write_default_config_file(self.config_file,CONFIG_SPEC)
            except Exception as inst:
                logger.error(inst)
                logger.error("unexpected error creating default config %s" % (self.config_file))
                cleanup_and_exit(self, -2)
            else:
                logger.info("created default config file %s" % (self.config_file))
        # we have a default config file
        keep_trying = True
        while keep_trying:
            try:
                self.n_config_errors = 0
                (self.configvars,result) = self._read_config_file(self.config_file, CONFIG_SPEC)
                error_dict = flatten_errors(self.configvars,result)
                self.n_config_errors = len(error_dict)
                if self.n_config_errors:
                    logger.warning("%d error(s) reading %s :" %(self.n_config_errors,self.config_file))

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

                fileversion = self.configvars['Version']['config_version']
                if fileversion != CONFIG_VERSION:
                    logger.warning('config file versions do not match - internal: "%s", config file "%s"' %(CONFIG_VERSION,fileversion))       
                else:
                    logger.debug("config file version ok: '%s'" % (fileversion))

                # giive up on this cfg file?
                if (fileversion != CONFIG_VERSION) or (RENEW_ERRORED_CFG and (self.n_config_errors > 0)):
                    # This config file wont work.
                    # we move the file out of the way, create
                    # a new default and retry.
                    tag = asctime()
                    badfilename = self.config_file + '.' + tag.replace(' ','-')
                    logger.debug("trying to rename bad cfg %s to %s" % (self.config_file,badfilename))
                    try:
                        os.rename(self.config_file,badfilename)
            
                    except OSError  as (e,msg):
                        logger.error("rename(%s,%s) failed: %s - %s" % (self.config_file,badfilename,e,msg))
                        # Canthappen. Yeah, right.
                        self.n_config_errors += 1
                        keep_trying = False 
                    else:
                        logger.info("renamed bad config to %s" % (badfilename))
                        # create a fresh default cfg
                        (self.configvars,result) = self._write_default_config_file(self.config_file,CONFIG_SPEC)
                        # a new file exists, read it once more so we 
                        logger.info("created default cfg %s" % (self.config_file))
                        keep_trying = True                              
                else:
                    keep_trying = False # it's either this or that way                                    
                
            except IOError as (e,msg):
                logger.error("cant read %s: %s %s " % (self.config_file,e,msg))
                self.n_config_errors += 1
                keep_trying = False 
    
        
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
    