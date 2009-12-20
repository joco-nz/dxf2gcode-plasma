'''
Container for global variables accessible to all classes

@author: mah
'''



# logger instance, see http://docs.python.org/library/logging.html
# once set, use as logger.error("foo")
logger = None

# GlobalConfig instance
config = None


# PluginLoader, Varspace
    
plugins =  dict()   # the modules keyed by tag
modules =  dict()   # plugin instances keyed by instance name








