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
import logging
import glob

import globals as g
import constants as c


class PluginLoader:
    
    
    
#    def __init__(self,plugin_directory,varspaces_directory,frame):
    def __init__(self,frame):
        """
        import all valid plugins from a plugin_directory
        """ 
#        self.modules = dict()       # the modules keyed by tag
#        self.plugins = dict()       # plugin instances keyed by instance name
        
        self.frame = frame          # notebook frame where panes are hooked to
        
        self.import_plugins(g.config.config.Paths.plugin_dir,g.config.config.Paths.varspaces_dir)


    
    def add_instance(self,module):
    
        p = module.Plugin() 
        tag = p.plugin_tag()
        varspace_subdir = os.path.join(g.config.config.Paths.varspaces_dir,tag)        
        
        instance_name = self.valid_instance(p.plugin_tag(), varspace_subdir)
        vs_path = os.path.join(varspace_subdir,instance_name + c.CONFIG_EXTENSION)                                    
        self.startup_plugin(p, instance_name,module,vs_path)
        g.plugins[instance_name] = p 
    
    def delete_instance(self,instance_name):
        #del(g.plugins[instance_name].vs)
        p = g.plugins[instance_name]
        p.cleanup()
        del(g.plugins[instance_name])
    
    def rename_instance(self,old_instancename, new_instancename):
        p = g.plugins[old_instancename]
        del(g.plugins[old_instancename])
        g.plugins[new_instancename] = p
        self.frame.rebuild_menu()
        
        print "pl: rename_instance %s -> %s" % (old_instancename, new_instancename)
        pass
    
    def import_plugins(self,directory,varspaces_dir):
        """ 
        Find and validate all plugins in <directory>
        for each saved varspace in <varspaces_dir>/<handle>/<instancename>.cfg:
            create an instance of the <handle> plugin with <instancename>.cfg loaded
        if <varspaces_dir>/<handle> is empty:
            create a new  <default-instancename>.cfg
            return a <handler> instance with <default-instancename>.cfg varspace loaded
        """
        if os.path.isdir(directory):
            sys.path.append(directory)
            d = os.path.abspath(directory)
            names = sorted(os.listdir(d))
            #FXIME handle OSError
            if len(names) > 0:
                for f in names:       
                    handle, ext = os.path.splitext(f) # Handles no-extension files, etc.
                    if ext == '.py':
                        module = self.load_module(handle)
                        if module:
                            p = self.validate_plugin(module)
                            if p: # looking good
                                tag = p.plugin_tag()
                                varspace_subdir = os.path.join(varspaces_dir,tag) 
                                if not os.path.isdir(varspace_subdir):
                                    try:
                                        os.makedirs(varspace_subdir)
                                    except OSError, e:
                                        g.logger.logger.error("can't create directory %s: %s" % (varspace_subdir,e.strerror))
                                        raise
                                
                                vs_files = glob.glob(os.path.join(varspace_subdir,'*' + c.CONFIG_EXTENSION))
                                if len(vs_files) > 0:
                                    n = 0
                                    # derive instance name from filename
                                    for vs in vs_files:
                                        instance_name,ext = os.path.splitext(os.path.basename(vs))
                                        if n > 0: # finalize test instance and initialize
                                            p = module.Plugin()
                                        n += 1
                                        self.startup_plugin(p, instance_name,module,vs)
                                        g.plugins[instance_name]  = p
                                else:
                                    # finalize test instance and initialize
                                    instance_name = self.valid_instance(tag, varspace_subdir)
                                    vs_path = os.path.join(varspace_subdir,instance_name + c.CONFIG_EXTENSION)                                    
                                    self.startup_plugin(p, instance_name,module,vs_path)
                                    g.plugins[instance_name]  = p

                                g.modules[tag] = module

            else:
                g.logger.logger.warning("no files found in plugin dir %s" %(directory))
        else:
            g.logger.logger.error("plugin_dir %s - not a directory",directory)            
        
    def load_module(self,handle):
        try:
            module = __import__(handle)
        except ImportError,msg:
            g.logger.logger.warning("skipping %s - %s",handle,msg)
            return None
        else:
            g.logger.logger.debug("module %s imported OK",handle)
            return module
    
    def valid_instance(self,tag,directory):
        
        for i in range(100):
            fn = "%s-%d" % (tag,i)
            afn=  os.path.join(directory,fn + c.CONFIG_EXTENSION)
            if not os.path.isfile(afn):
                return fn
        return None
    
    def startup_plugin(self,p,instance_name,module,varspace_path):   
        
        # TODO handle initialize execeptions and dont add if any         
        p.initialize(self.frame.nbook, varspace_path,instance_name,self)
        g.logger.logger.info("module %s instance '%s' started, tag='%s'" % (module.__name__,instance_name,p.plugin_tag()))

        
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
                if hasattr(p,c.TRANSFORMER):
                    n += 1

                if n != 1:
                    raise NameError, "module '%s': must have either a %s() or a %s() method" %(module.__name__,c.EXPORTER,c.TRANSFORMER)
                
                          
            except NameError,msg:
                g.logger.logger.warning(msg)
            else:
                g.logger.logger.debug("module '%s' v='%s' tag='%s' validated" % (module.__name__,p.version(),p.plugin_tag()))
                return p
        return None
       

