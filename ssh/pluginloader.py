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

class PluginLoader:
    
    
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
        
        self.frame = frame          # notebook frame where panes are hooked to
        
        self.import_plugins(g.config.config.Paths.plugin_dir,
                            g.config.config.Paths.varspaces_dir)

    def add_instance(self,module):
        """
        create a plugin instance with default varspace and auto-generated
        instance name
        """
        p = module.Plugin() 
        varspace_subdir = os.path.join(g.config.config.Paths.varspaces_dir,p.TAG)        
        instance_name = self.generate_valid_instance_name(p.TAG, varspace_subdir)
        vs_path = os.path.join(varspace_subdir,instance_name + c.CONFIG_EXTENSION)                                    
        if self.startup_plugin(p, instance_name,module,vs_path):
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
    
    def import_plugins(self,directory,varspaces_dir):
        """ 
        Find and validate all plugins in <directory>
        for each saved varspace in <varspaces_dir>/<module>/<instancename>.cfg:
            create an instance of the <module> plugin 
            with <instancename>.cfg varspace loaded in startup_plugin
        if <varspaces_dir>/<module> is empty:
            create a new  <default-instancename>.cfg
            return a <plugin> instance with <default-instancename>.cfg varspace loaded
        """
        if os.path.isdir(directory):
            sys.path.append(directory)
            d = os.path.abspath(directory)
            names = sorted(os.listdir(d))
            #FXIME module OSError
            if len(names) > 0:
                for f in names:       
                    module, ext = os.path.splitext(f) # Handles no-extension files, etc.
                    if ext == '.py':
                        m = self.load_module(module)
                        if m:
                            p = self.validate_plugin(m)
                            if p: # looking good
                                varspace_subdir = os.path.join(varspaces_dir,p.TAG) 
                                if not os.path.isdir(varspace_subdir):
                                    try:
                                        os.makedirs(varspace_subdir)
                                    except OSError, e:
                                        g.logger.logger.error("can't create directory %s: %s" % 
                                                              (varspace_subdir,e.strerror))
                                        raise
                                
                                vs_files = glob.glob(os.path.join(varspace_subdir,'*' + c.CONFIG_EXTENSION))
                                if len(vs_files) > 0:
                                    n = 0
                                    # derive instance name from filename
                                    for vs in vs_files:
                                        instance_name,ext = os.path.splitext(os.path.basename(vs))
                                        if n > 0: # finalize test instance and initialize
                                            p = m.Plugin()
                                        n += 1
                                        if self.startup_plugin(p, instance_name,m,vs):
                                            g.plugins[instance_name]  = p
                                        else:
                                            g.logger.logger.warning("skipping plugin %s module %s instance %s: initialize() failed" 
                                                                    % (p.TAG,module,instance_name))
                                else:
                                    # finalize test instance and initialize
                                    instance_name = self.generate_valid_instance_name(p.TAG, varspace_subdir)
                                    vs_path = os.path.join(varspace_subdir,instance_name + c.CONFIG_EXTENSION)                                    
                                    if self.startup_plugin(p, instance_name,m,vs_path):
                                        g.plugins[instance_name]  = p
                                    else:
                                        g.logger.logger.warning("skipping plugin %s module %s instance %s: initialize() failed" 
                                                                % (p.TAG,module,instance_name))

                                g.modules[p.TAG] = m

            else:
                g.logger.logger.warning("no files found in plugin dir %s" %(directory))
        else:
            g.logger.logger.error("plugin_dir %s - not a directory",directory)            
        
    def load_module(self,module):
        """ 
        try to import module and fail nicely
        """
        
        try:
            module = __import__(module)
        except ImportError,msg:
            g.logger.logger.warning("skipping %s - %s",module.__name__,msg)
            return None
        else:
            g.logger.logger.debug("module %s imported OK",module.__name__)
            return module
    
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
    
    def startup_plugin(self,p,instance_name,module,varspace_path):   
        """
        generate the varspace and pass to initialize()
        """
        _vs = VarSpace(p.SPECNAME, varspace_path, instance_name,
                       frame=self.frame.nbook,
                       specversion=p.SPECVERSION,
                       rename_hook=self.rename_instance)
        _result = p.initialize( _vs)
        if not _result and _vs.default_config:
            # we auto-generated a varspace and initialize failed
            # so remove that varspace
            _vs.cleanup(save=False,remove=True)
            del(_vs)
            g.logger.logger.debug("cleanup default varspace %s after failed initialize()",instance_name)            
        return _result
        
    def validate_plugin(self,module):   
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
                
                # and exactly one of these:
                n = 0
                if hasattr(p,c.EXPORTER):
                    n += 1
                    if not hasattr(p,c.EXPORT_MENU_ENTRY):
                        raise NameError, "module '%s' missing required '%s' class variable" %(module.__name__,c.EXPORT_MENU_ENTRY)

                if hasattr(p,c.TRANSFORMER):
                    n += 1
                    if not hasattr(p,c.TRANSFORM_MENU_ENTRY):
                        raise NameError, "module '%s' missing required '%s' class variable" %(module.__name__,c.TRANSFORM_MENU_ENTRY)
                if n is 0:
                    raise NameError, "module '%s': must have at least a %s() or a %s() method" %(module.__name__,c.EXPORTER,c.TRANSFORMER)
                
                          
            except NameError,msg:
                g.logger.logger.warning(msg)
            else:
                g.logger.logger.debug("module '%s' v='%s' tag='%s' validated" % (module.__name__,p.VERSION,p.TAG))
                return p
        return None
       

