'''
Created on 17.12.2009

@author: mah
'''
import logging
import sys

import constants as c


class Log:
    '''
    handle 3 log streams:
        console
        file
        message window
    '''
    def __init__(self, tag, console_loglevel=c.CONSOLE_LOGLEVEL):
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
    def _cvtlevel(self, level):
        if isinstance(level,basestring):
            return logging._levelNames[level]
        else:
            return level

    # logging to file + window - explicitely enabled
    def add_file_logger(self, logfile=c.DEFAULT_LOGFILE,log_level=c.FILE_LOGLEVEL):
        
        self.file_handler = logging.FileHandler(logfile)
        self.file_handler.setFormatter(logging.Formatter("%(levelname)s %(module)s:%(funcName)s:%(lineno)d  - %(message)s"))
        self.file_handler.setLevel(self._cvtlevel(log_level))
        self.logger.addHandler(self.file_handler)
    
    def add_window_logger(self, log_level=c.WINDOW_LOGLEVEL):
        
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
            
