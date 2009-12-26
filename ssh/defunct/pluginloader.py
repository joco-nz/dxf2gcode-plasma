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
from d2gexceptions import *

    #  p = PluginLoader()
    #  p.activate("config",program_dir,config_cfg, window)
    #  p.activate("machine",program_dir,machine_cfg,window)
    # fixup paths 
    #  p.activate_all(plugin_dir,varspace_dir, window)

class PluginLoader(object):
    
    
    def __init__(self):
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

    def activate(self,plugin_dir,base_name,cfg_path,window):
        """
        import and validate a plugin from <plugin_dir>/<file_name>
        load varspace from <config_path> if it exists and is syntactically valid
        else create and save a default varspace in <config_path>
        create directories along <config_path> as needed
        pass window parameter to plugin so it can properly display the paramter pane
        add {instancename:instance} to global plugins dictionary
        
        may raise PluginError with associated message, or OSError
        
        @param plugin_dir: directory where  plugin.py files lives
        @type plugin_dir: String.
        
        @param file_name: plugin file basename without '.py' extension 
        @type file_name: String.
 
        @param cfg_path: varspace pathname like 'dirname/foo.cfg'
        @type cfg_path: String.
                    
        @return: Return plugin instance
        """ 
        if self.modules.has_key(base_name):
            g.logger.logger.debug( "module %s already loaded" % (base_name))
            _module = self.modules[base_name]
            _instance = _module.Plugin()
        else:
            (_module,_instance) = self._import_plugin(plugin_dir, base_name)           
    
        # at this point we have a valid Plugin() instance and know the tag.
        # first, make sure varspace_path exists
        
        (cfg_dir,cfg_file) = os.path.split(cfg_path) 
        (instance_name,cfg_ext) = os.path.splitext(cfg_file)
        
        if g.plugins.has_key(instance_name):
            g.logger.logger.error( "plugin instance %s already exists" % (instance_name))
        
        if not os.path.isdir(cfg_dir):
            os.makedirs(cfg_dir)

        # decorate any required member attributes here.
        _instance.instance_name = instance_name
        _instance.module = _module
        _instance.window = window
        _instance.nbook = window.nbook
        _instance.is_default = instance_name == _module.__name__

        # startup_plugin is a Plugin superclass method (in VarSpace)
        _instance.startup_plugin(cfg_path)
        
        g.plugins[instance_name] = _instance
        self.modules[instance_name] = _module
        return _instance



    def activate_all(self,plugin_dir,varspaces_dir,window):
        
        # actvate all plugins with default varspace
        # then for each plugin 
        #    iterate other varspaces

        _file_names = sorted(glob.glob(os.path.join(plugin_dir,'*' + c.PY_EXTENSION)))
        
        if len(_file_names) > 0:
            for _plugin_path in _file_names:  
                
                # FIXME check plugin existance
                (_dir,_file_name) = os.path.split(_plugin_path) 
                (_basename,_cfg_ext) = os.path.splitext(_file_name)
   
                # load default instance
                _default_config = os.path.join(varspaces_dir,_basename,_basename + c.CONFIG_EXTENSION)
                _instance = self.activate(plugin_dir, _basename, _default_config,window)
                    
                varspaces_subdir = os.path.join(varspaces_dir,_instance.instance_name) # of the default instance 
                
                if not os.path.isdir(varspaces_subdir):
                    os.makedirs(varspaces_subdir)
                
                vs_files = glob.glob(os.path.join(varspaces_subdir,'*' + c.CONFIG_EXTENSION))
                # remove default instance from list
                if len(vs_files) > 0:
                    vs_files.remove(_default_config)
                    
                # derive instance name from filename
                for vs in vs_files:
                    instance_name,ext = os.path.splitext(os.path.basename(vs))
                    
                    _instance = self.activate(plugin_dir,_basename,vs,window)
   
                    g.plugins[instance_name]  = _instance
                    
        else:
            g.logger.logger.warning("no plugins found in %s" %(plugin_dir))      

    
    def _import_plugin(self,plugin_dir, base_name):
        """
        import a single plugin in plugin_dir if the
        module wasnt loaded yet.
        
        instantiate plugin and check for required attributes 
        
        Return module, instance on success
        Raise PluginError on failure
        
        @param plugin_dir: directory where  plugin.py files live
        @type plugin_dir: String.
        
        @param base_name: plugin filename without '.py' extension
        @type base_name: String.
             
        @return: tuple(module, instance, success).
        """

        if not self.modules.has_key(base_name):
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)

            try:
                _module = __import__(base_name)
            except ImportError,_msg:
                raise PluginError, "module '%s' skipped - import error: %s" %(base_name,_msg)
            else:
                g.logger.logger.debug("module '%s' imported OK",_module.__name__)
        else:
            _module = self.modules[base_name]
        
        try:
            _instance = _module.Plugin()
        except Exception,_msg:
            raise PluginError, "module '%s' skipped - cant instantiate %s.Plugin() class - %s" % (_module.__name__,_module.__name__,_msg)
        else: 
            # now check wether all required methods/attributes are defined on Plugin()
            for _m in c.REQUIRED:
                if not hasattr(_instance,_m):
                    raise PluginError, "module '%s' missing required '%s' method or attribute" %(_module.__name__,_m)
            else:
                g.logger.logger.debug("module '%s' v='%s' validated" % (_module.__name__,_instance.VERSION))
                            
        return (_module,_instance)
        

