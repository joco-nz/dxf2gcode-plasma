#!/usr/bin/env python
"""
pluginloader.py - From a directory name:

1: append the directory to the sys.path
2: find all modules within that directory
3: import all modules with .py extension within that directory
4: ignore modules with syntax errors or missing Plugin() class 
5: test-instantiate the Plugin() class for each module
    6: check wether all required_methods are defined 
    7: check that either 'transformer' or 'exporter' method is present
    8: throw away test instance
    9: for all varspaces in varspaces_dir/handle/<name>.cfg:
        instantiate Plugin(varspace)
        add to transformer/exporter instances
    10: if varspaces dir was empty or not existent:
        generate a new varspace instance tag name
        instantiate Plugin(new_varspace_name) which will
        cause a default varspace to be generated and saved



self.plugins : key = handle, value = module instances
self.exporters : key = instance-tag, value = instance object
self.transformers : key = instance-tag, value = instance object

an instance-tag rename causes:
    new-tag varspace.cfg written
    old-tag varspace.cfg deleted
    exporters/transformers entry changed from old-tag to new-tag
    update_menu_entry trigger called so menu entries can be updated

handle = basename of plugin name (without .py extension)
tag: default is <handle>-serial, overriden by user choice

Michael Haberler 12/2009

based on code from http://code.activestate.com/recipes/436873/ 
Copyright 2005 Jesse Noller <jnoller@gmail.com>

"""

import os
import sys
import glob

import globals as g
import constants as c

from varspace import VarSpace
from d2gexceptions import PluginError



class PluginLoader(object):
    
    
    def __init__(self,window):
        """
        import all valid plugins from a plugin_directory
        for each plugin:
            if plugin varspace(s) files available:
                for each varspace.cfg
                    create plugin instance with varspace loaded
            else
                create a plugin instance with default varspace
        """ 
        self.modules = dict()
        """ key: module basename, value: loaded module"""

        self._import_all_plugins(g.config.config.Paths.plugin_dir,
                            g.config.config.Paths.varspaces_dir,window)

        

    
    def _import_all_plugins(self,plugin_dir,varspaces_dir,window):
        """ 
        Find, load and validate all *.py files in <plugin_dir> which are
        expected to contain a class Plugin(VarSpace). Validation is really
        just a cursory check if certain required attributes are set.
        
        read <instance-name>.cfg in <varspaces_dir>/<p.TAG>/*
        
        if list is empty
            create a default instance of the <p.TAG> plugin 
            with <p.TAG>.cfg varspace loaded in startup_plugin()
        else
            foreach <instance-name>.cfg 
                create a <plugin> instance with <default-instancename>.cfg varspace loaded
        """

        try:
            _file_names = sorted(glob.glob(os.path.join(plugin_dir,'*' + c.PY_EXTENSION)))
            
        except OSError, e:
            g.logger.logger.error("can't read plugin_dir %s: %s" % (plugin_dir,e.strerror))
            
        if len(_file_names) > 0:
            for _plugin_path in _file_names:  
                (_dir,file_name) = os.path.split(_plugin_path)    
                # create the default Plugin() instance.
                (_module,_instance,_success) = self._import_plugin(plugin_dir, file_name)
                
                if _success:
                    # at this point we have a valid Plugin() instance and know the tag.
                    # first, make sure varspace_path exists
                    
                    varspaces_subdir = os.path.join(varspaces_dir,_instance.TAG) 

                    if not os.path.isdir(varspaces_subdir):
                        try:
                            os.makedirs(varspaces_subdir)
                        except OSError, e:
                            g.logger.logger.error("can't create varspace dir %s: %s" % 
                                                  (varspaces_subdir,e.strerror))
                            raise
                        
                    # The first instance will become the default (instance_name = p.TAG)
                    # so load the (or create a) default varsapce named <tag>.cfg.
                    _default_config = _instance.TAG + c.CONFIG_EXTENSION
                    _instance.instance_name = _instance.TAG
                    _instance.module = _module
                    _instance.window = window
                    _instance.nbook = window.nbook
                    _instance.is_default = True 

                    # startup_plugin is a Plugin superclass method (in VarSpace)
                    if _instance.startup_plugin(os.path.join(varspaces_subdir,_default_config)):
                        g.plugins[_instance.TAG] = _instance
                        self.modules[_instance.TAG] = _module
                    else:
                        del(_instance)
                    # now load all stored instances.
                    vs_files = glob.glob(os.path.join(varspaces_subdir,'*' + c.CONFIG_EXTENSION))
                    # after p.startup_plugin() a <tag>/<tag>.cfg file exists 
                    # so remove that from list of non-default instances 
                    if len(vs_files) > 0:
                        vs_files.remove(os.path.join(varspaces_subdir,_default_config))
                    
                    # derive instance name from filename
                    for vs in vs_files:
                        instance_name,ext = os.path.splitext(os.path.basename(vs))
                        _instance = _module.Plugin()
                        _instance.instance_name = instance_name
                        _instance.module = _module
                        _instance.window = window
                        _instance.nbook = window.nbook
                        _instance.is_default = False 

                        if _instance.startup_plugin(vs):
                            g.plugins[instance_name]  = _instance
                        else:
                            g.logger.logger.warning("skipping plugin %s module %s instance %s: initialize() failed" 
                                                    % (_instance.TAG,_module,instance_name))   
                            del(_instance)
        else:
            g.logger.logger.warning("no plugins found in %s" %(plugin_dir))                
    
    def _import_plugin(self,plugin_dir, file_name):
        """
        import and validate a single plugin in plugin_dir if the
        module wasnt loaded yet.
        
        Return module, instance and success/failure.
        
        @param plugin_dir: directory where  plugin.py files live
        @type plugin_dir: String.
        
        @param file_name: plugin filename like 'foo.py' 
        @type file_name: String.
             
        @return: tuple(module, instance, success).
        """
        _module_name, ext = os.path.splitext(file_name) # Handles no-extension files, etc.

        if ext != c.PY_EXTENSION:
            g.logger.logger.warning("plugin %s - not a .py file" % (file_name))
        else:
            if not self.modules.has_key(_module_name):
                if plugin_dir not in sys.path:
                    sys.path.append(plugin_dir)
                _module = self._import_module(_module_name)
            else:
                _module = self.modules[_module_name]
                
            _instance = self._instantiate_and_validate_plugin(_module)
            return (_module,_instance,True)
        return (None,None,False)



    def _import_module(self,module):
        """ 
        try to import module and fail nicely
        """
        
        try:
            module = __import__(module)
        except ImportError,msg:
            g.logger.logger.warning("modile '%s' skipped - import error: %s",module,msg)
            return None
        else:
            g.logger.logger.debug("module '%s' imported OK",module.__name__)
            return module
        
    def _instantiate_and_validate_plugin(self,module):   
        """
        instantiate plugin and check for required attributes 
        return instance or None if failed
        """
        errors = 0
        # see wether we can instantiate the Plugin() class
        try:
            p = module.Plugin()
        except Exception,msg:
            g.logger.logger.warning("module '%s' skipped - missing Plugin() class - %s" %(module.__name__,msg))
            return None
        else: 
            # now check wether all required methods/attributes are defined on Plugin()
            for m in c.REQUIRED:
                if not hasattr(p,m):
                    errors += 1
                    g.logger.logger.error( "module '%s' missing required '%s' method" %(module.__name__,m))
                
            if errors > 0:
                return None
            else:
                g.logger.logger.debug("module '%s' v='%s' tag='%s' validated" % (module.__name__,p.VERSION,p.TAG))
                return p       

