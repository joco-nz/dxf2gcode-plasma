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
    
    
    def __init__(self,frame):
        """
        import all valid plugins from a plugin_directory
        for each plugin:
            if plugin varspace(s) files available:
                for each varspace.cfg
                    create plugin instance with varspace loaded
            else
                create a plugin instance with default varspace
        """ 
        self.loaded_modules = dict()
        """ key: module basename, value: loaded module"""
            
        self.frame = frame          # notebook frame where panes are hooked to
        
        self.import_all_plugins(g.config.config.Paths.plugin_dir,
                            g.config.config.Paths.varspaces_dir)

    def add_instance(self,module):
        """
        create a plugin instance with default varspace and auto-generated
        instance name
        """
        p = module.Plugin() 
        p.is_default = False 


        varspace_subdir = os.path.join(g.config.config.Paths.varspaces_dir,p.TAG)        
        instance_name = self.generate_valid_instance_name(p.TAG, varspace_subdir)
        
        vs_path = os.path.join(varspace_subdir,instance_name + c.CONFIG_EXTENSION)                                    
        if self.startup_plugin(p, instance_name,vs_path):
            g.plugins[instance_name] = p 
            g.logger.logger.debug("plugin %s module %s new instance %s created" % (p.TAG,module.__name__,instance_name))
        else:
            g.logger.logger.warning("skipping plugin %s module %s instance %s: initialize() failed" 
                                    % (p.TAG,module.__name__,instance_name))

    def close_instance(self,instance_name):
        """
        close the plugin and save to corresponding varspace file
        """        
        p = g.plugins[instance_name]
        p.vs.cleanup(save=True)
        p.cleanup()
        del(g.plugins[instance_name])
        g.logger.logger.debug("plugin %s instance %s saved" % (p.TAG, instance_name))
 
    def delete_instance(self,instance_name):
        """
        close the plugin and delete corresponding varspace file
        """
        p = g.plugins[instance_name]
        p.vs.cleanup(remove=True)

        p.cleanup()
        del(g.plugins[instance_name])
        g.logger.logger.debug("plugin %s instance %s deleted" % (p.TAG, instance_name))
  
    def rename_instance(self,old_instancename, new_instancename):
        """ 
        this is a hook called by varspace if the user renamed the instance
        do necessary UI updates like change menu entries
        """
        
        p = g.plugins[old_instancename]
        del(g.plugins[old_instancename])
        g.plugins[new_instancename] = p
        self.frame.rebuild_menu()
        g.logger.logger.debug("instance %s renamed to %s" % (old_instancename, new_instancename))
    
    def startup_plugin(self,p,instance_name,varspace_path,default=False):   
        """
        generate the varspace and pass to initialize()
        """
        
        _vs = VarSpace(p.SPECNAME, varspace_path, instance_name,
                       frame=self.frame.nbook,
                       specversion=p.SPECVERSION,
                       rename_hook=self.rename_instance,default=default,plugin=p)
        _result = p.initialize( _vs)

        if not _result and _vs.default_config:
            # we auto-generated a varspace and initialize failed
            # so remove that varspace
            _vs.cleanup(save=False,remove=True)
            del(_vs)
            g.logger.logger.debug("cleanup default varspace %s after failed initialize()",instance_name) 
        else:
            p.varspace = _vs    # make sure it's associated with the instance     

        return _result

    def import_module(self,module):
        """ 
        try to import module and fail nicely
        """
        
        try:
            module = __import__(module)
        except ImportError,msg:
            g.logger.logger.warning("skipping %s - %s",module,msg)
            return None
        else:
            g.logger.logger.debug("module %s imported OK",module.__name__)
            return module
        
    def import_plugin(self,plugin_dir, file_name):
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
            if not self.loaded_modules.has_key(_module_name):
                if plugin_dir not in sys.path:
                    sys.path.append(plugin_dir)
                _module = self.import_module(_module_name)
            else:
                _module = self.loaded_modules[_module_name]
                
            _instance = self.instantiate_and_validate_plugin(_module)
            return (_module,_instance,True)
        return (None,None,False)
    
    def import_all_plugins(self,plugin_dir,varspaces_dir):
        """ 
        Find and validate all plugins in <plugin_dir>
        for each saved varspace in <varspaces_dir>/<p.TAG>/<instancename>.cfg:
            create an instance of the <module> plugin 
            with <instancename>.cfg varspace loaded in startup_plugin
        if <varspaces_dir>/<module> is empty:
            create a new  <default-instancename>.cfg
            return a <plugin> instance with <default-instancename>.cfg varspace loaded
        """

        try:
            #_file_names = sorted(os.listdir(os.path.abspath(plugin_dir)))
            _file_names = sorted(glob.glob(os.path.join(plugin_dir,'*' + c.PY_EXTENSION)))
            
        except OSError, e:
            g.logger.logger.error("can't read plugin_dir %s: %s" % 
                                                  (plugin_dir,e.strerror))
        if len(_file_names) > 0:
            for _plugin_path in _file_names:  
                (_dir,file_name) = os.path.split(_plugin_path)    
                # first, create the default instance.
                (_module,_instance,_success) = self.import_plugin(plugin_dir, file_name)
                if _success:
                    # at this point we have a plugin instance.
                    # first, make sure varspace_path exists
                    varspaces_subdir = os.path.join(varspaces_dir,_instance.TAG) 

                    if not os.path.isdir(varspaces_subdir):
                        try:
                            os.makedirs(varspaces_subdir)
                        except OSError, e:
                            g.logger.logger.error("can't create varspace dir %s: %s" % 
                                                  (varspaces_subdir,e.strerror))
                            raise
                    # re-use that test instance as default:
                    # load or create a default varsapce named <tag>.cfg.
                    _default_config = _instance.TAG + c.CONFIG_EXTENSION
                    if self.startup_plugin(_instance,_instance.TAG,
                                           os.path.join(varspaces_subdir,_default_config),default=True):
                        
                        # remember it's a default - control sensible UI actions
 #                       _instance.varspace.is_default = True
                        # _instance.varspace.default_config tells us it was created from the spec    
                        g.plugins[_instance.TAG] = _instance
                        g.modules[_instance.TAG] = _module
   
                    # now load all stored instances.
                    vs_files = glob.glob(os.path.join(varspaces_subdir,'*' + c.CONFIG_EXTENSION))
                    # remove default instance name since we just created/loaded that 
                    if len(vs_files) > 0:
                        vs_files.remove(os.path.join(varspaces_subdir,_default_config))
                    
                    # derive instance name from filename
                    for vs in vs_files:
                        instance_name,ext = os.path.splitext(os.path.basename(vs))
                        _instance = _module.Plugin()
                        if self.startup_plugin(_instance, instance_name,vs,default=False):
                            #_instance.varspace.is_default = False 
                            g.plugins[instance_name]  = _instance
                        else:
                            g.logger.logger.warning("skipping plugin %s module %s instance %s: initialize() failed" 
                                                    % (_instance.TAG,_module,instance_name))   
        else:
            g.logger.logger.warning("no plugins found in %s" %(plugin_dir))                
    
    def generate_valid_instance_name(self,tag,directory):
        """
        search for next unused instance name in directory
        ugly, but works
        """
        for i in range(100):
            fn = "%s-%d" % (tag,i)
            afn=  os.path.join(directory,fn + c.CONFIG_EXTENSION)
            if not os.path.isfile(afn):
                return fn
        return None
    

        
    def instantiate_and_validate_plugin(self,module):   
        """
        instantiate plugin and check for required attributes 
        return instance or None if failed
        """
        # see wether we can instantiate the Plugin() class
        try:
            p = module.Plugin()
        except Exception,msg:
            g.logger.logger.warning("module '%s' disabled - missing Plugin() class - %s" %(module.__name__,msg))
        else: 


            # now check wether all required methods are defined on Plugin()

            try:
                for m in c.REQUIRED:
                    if not hasattr(p,m):
                        raise NameError, "module '%s' missing required '%s' method" %(module.__name__,m)
                
#                # and exactly one of these:
#                n = 0
#                if hasattr(p,c.EXPORTER):
#                    n += 1
#                    if not hasattr(p,c.EXPORT_MENU_ENTRY):
#                        raise NameError, "module '%s' missing required '%s' class variable" %(module.__name__,c.EXPORT_MENU_ENTRY)
#
#                if hasattr(p,c.TRANSFORMER):
#                    n += 1
#                    if not hasattr(p,c.TRANSFORM_MENU_ENTRY):
#                        raise NameError, "module '%s' missing required '%s' class variable" %(module.__name__,c.TRANSFORM_MENU_ENTRY)
#                if n is 0:
#                    raise NameError, "module '%s': must have at least a %s() or a %s() method" %(module.__name__,c.EXPORTER,c.TRANSFORMER)
#                
                          
            except NameError,msg:
                g.logger.logger.warning(msg)
            else:
                g.logger.logger.debug("module '%s' v='%s' tag='%s' validated" % (module.__name__,p.VERSION,p.TAG))
                return p
        return None
       

