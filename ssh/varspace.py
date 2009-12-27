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
'''
VarSpace implements:

- a persistent, typed  variable store (self.var_dict) using ConfigObj 
    (including automatic type conversion when reading from INI file)
    plus some basic type and range checking on the INI file 
- a method to create a default INI file from the specifification
- a user interface abstraction so plugins may remain UI-agnostic
     this is a minimal interface to create parameter entry fields & buttons for
     Tkinter, driven by config file contents

Michael Haberler  20.12.2009
'''

import os
import sys
import glob

from Tkconstants import  N, E, W, GROOVE
from Tkinter import OptionMenu, Frame, Checkbutton, Button, Label, Entry,LabelFrame
from Tkinter import StringVar, DoubleVar, IntVar,BooleanVar
from configobj import ConfigObj, flatten_errors
from validate import Validator

from dotdictlookup import DictDotLookup
from simplecallback import SimpleCallback
from d2gexceptions import *
import globals as g
import constants as c

class VarSpace(object):
#    def __init__(self):
#        g.logger.logger.error( 'VARSPACE INIT CALLED!!')
#
#    def __del__self(self):
#        print "TEMPLATE __del__"

        
    def _cleanup(self,save=True,remove=False):
        """
        close a varspace instance
        optionally save/remove persistence file
        remove parameter pane from window
        """
        if save:
            self._save_varspace()
            g.logger.logger.debug( 'varspace %s saved' %(self.instance_name))
        if remove:
            os.remove(self.pathname)
            g.logger.logger.info( 'varspace %s deleted' %(self.instance_name))

        self.nbook.hide(self.param_frame)

        
    def load_varspace(self,specversion):

        if os.path.isfile(self.pathname):
            try:
                # file exists, read & validate it
                self.var_dict = ConfigObj(self.pathname, configspec=self.spec, interpolation=False)
                _vdt = Validator()
                result = self.var_dict.validate(_vdt, preserve_errors=True)
                validate_errors = flatten_errors(self.var_dict, result)
                if validate_errors:
                    g.logger.logger.error("errors reading %s:" % (self.pathname))
                for entry in validate_errors:
                    section_list, key, error = entry
                    if key is not None:
                        section_list.append(key)
                    else:
                        section_list.append('[missing section]')
                    section_string = ', '.join(section_list)
                    if error == False:
                        error = 'Missing value or section.'
                    g.logger.logger.error( section_string + ' = ' + error)       
    
                if validate_errors:
                    raise BadConfigFileError,"syntax errors in config file"
                    
                # check config file version against internal version
                if specversion:
                    fileversion = self.var_dict['Version']['specversion'] # this could raise KeyError
                    if fileversion != specversion:
                        #print 
                        #g.logger.logger.error( 
                        raise VersionMismatchError,'config file vesions do not match - internal: "%(specversion)s", config file "%(fileversion)s"' %(locals())
                    
            except Exception,inst:
                # g.logger.logger.error(inst)               
                (base,ext) = os.path.splitext(self.pathname)
                badfilename = base + c.BAD_CONFIG_EXTENSION
                g.logger.logger.debug("trying to rename bad cfg %s to %s" % (self.pathname,badfilename))
                try:
                    os.rename(self.pathname,badfilename)
                except OSError,e:
                    g.logger.logger.error("rename(%s,%s) failed: %s" % (self.pathname,badfilename,e.strerror))
                    raise
                else:
                    g.logger.logger.debug("renamed bad varspace %s to '%s'" %(self.pathname,badfilename))
                    self.create_default_varspace()
                    self.default_config = True
                    g.logger.logger.debug("created default varspace '%s'" %(self.pathname))
            else:
                self.default_config = False
                g.logger.logger.debug("read existing varspace '%s'" %(self.pathname))
        else:
            self.create_default_varspace()
            self.default_config = True
            g.logger.logger.debug("created default varspace '%s'" %(self.pathname))

        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.var_dict.main.interpolation = False # avoid ConfigObj getting too clever
        self.vars = DictDotLookup(self.var_dict) 
            
    def create_default_varspace(self):
        # derive config file with defaults from spec
        self.var_dict = ConfigObj(configspec=self.spec)
        _vdt = Validator()
        self.var_dict.validate(_vdt, copy=True)
        self.var_dict.filename = self.pathname
        self.var_dict.write()
    
    def _save_varspace(self):
        self.var_dict.filename = self.pathname
        self.var_dict.write()   
    
    def print_vars(self):
        print "Variables:"
        for k,v in self.var_dict['Variables'].items():
            print k," = ",v

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
    
    def clone_instance(self):
        """
        clone a plugin instance 
            - add default varspace
            - auto-generated instance name
            - add to g.plugins dictionary
        
        return True on success, False on failure
        """
        p = self.module.Plugin()  # clone myself
        p.is_default = False 
        p.module = self.module
        p.window = self.window
        p.nbook = self.window.nbook


        varspace_subdir = os.path.join(g.config.config.varspaces_dir,p.module.__name__)        
        p.instance_name = self.generate_valid_instance_name(p.module.__name__, varspace_subdir)
        
        if p.instance_name == None:
            g.logger.logger.warning("clone_instance() failed - couldnt generate valid instance name for '%s', vs=%s" 
                                    % (p.module.__name__,varspace_subdir))
            return False
        else:
            vs_path = os.path.join(varspace_subdir,p.instance_name + c.CONFIG_EXTENSION)                                    
            if p.startup_plugin(vs_path): #,self.window,default=False):
                g.plugins[p.instance_name] = p 
                g.logger.logger.debug("plugin %s new instance %s created" % (self.module.__name__,p.instance_name))
                return True
            else:
                g.logger.logger.warning("skipping plugin %s instance %s: initialize() failed" 
                                        % (self.module.__name__,p.instance_name))
                return False
    
    def close_instance(self,instance_name):
        """
        close the plugin and save to corresponding varspace file
        """        
        p = g.plugins[instance_name]
        p.cleanup()
        p._cleanup(save=True)

        del(g.plugins[instance_name])
        g.logger.logger.debug("plugin %s instance %s closed" % (p.module.__name__, instance_name))
 
    def delete_instance(self,instance_name):
        """
        close the plugin and delete corresponding varspace file
        """
        p = g.plugins[instance_name]
        p.cleanup()
        p._cleanup(remove=True)

        del(g.plugins[instance_name])
        g.logger.logger.debug("plugin %s instance %s deleted" % (p.module.__name__, instance_name))
  
    def rename_instance(self,old_instancename, new_instancename):
        """ 
        this is a hook called by varspace if the user renamed the instance
        do necessary UI updates like change menu entries
        """
        
        p = g.plugins[old_instancename]
        del(g.plugins[old_instancename])
        g.plugins[new_instancename] = p
        self.window.rebuild_apply_menu()
        g.logger.logger.debug("instance %s renamed to %s" % (old_instancename, new_instancename))
        
    def startup_plugin(self,varspace_path): #,window): #,default=False):   
        """
        initialize the varspace of an existing plugin instance
        init_varspace() is a superclass method of plugin
        """

        self.hidden = self.HIDDEN_AT_STARTUP
        self.default_config = False # wether a new name was generated

        self.var_dict = dict()
        self.tkVars = dict()
        self.groupcount = 0
        self.spec = ConfigObj(self.SPECNAME, interpolation=False, list_values=False, _inspec=True)
        self.pathname = varspace_path
        self.tk_instance_name = None
        try:
            self.load_varspace(self.SPECVERSION)
        except Exception,msg:
            g.logger.logger.warning("varspace %s loading failed: %s" % (self.instance_name,msg))      
            return False
            
        # startup Plugin subclass
        _result = self.initialize()       

        if not _result and self.default_config:
            # we auto-generated a varspace and initialize failed
            # so remove that varspace
            self._cleanup(save=False,remove=True)
            #del(p)
            g.logger.logger.debug("cleanup plugin %s after failed initialize()",self.instance_name)      

        return _result


    def tkvar_changed_callback(self,varname,vdict,name,index,mode):
        oldvalue = vdict[varname]
        try:
            newvalue = self.tkVars[varname].get()
        except ValueError:
            # reset to default newvalue if funny keys are pressed
            self.tkVars[varname].set(vdict[varname])
            pass
        else:
            #g.logger.logger.debug("%s changed from %s to %s" %(varname,vdict[varname],newvalue))
            vdict[varname] = newvalue

            if hasattr(self,'callbacks') and    self.callbacks.has_key(varname): # uh-oh
                self.callbacks[varname](varname,oldvalue,newvalue)
            vdict[varname] = newvalue

        
    def save_callback(self):
        if self.is_default:
            self._save_varspace()
            g.logger.logger.debug("varspace %s saved (default) " %(self.instance_name))  
        else:         
            new_name = self.tk_instance_name.get()
            if new_name != self.instance_name:
                
                if g.plugins.has_key(new_name): # uh-oh
                    g.logger.logger.error("can't save to %s - instance already exists" %(new_name))
                else:
                    old_instance = self.instance_name
                    old_path = self.pathname
                    self.instance_name = new_name
        
                    self.pathname = os.path.join(os.path.dirname(old_path),self.instance_name+c.CONFIG_EXTENSION)
                    self._save_varspace()
                    # TODO robustify + log
                    os.remove(old_path)
                    self.nbook.rename(self.param_frame,self.instance_name)
                    
                    # fixup menu entries
                    self.rename_instance(old_instance,self.instance_name)
                    
                    # name labelframe
                    self.set_frame_name()

            else:
                self._save_varspace()
                g.logger.logger.debug("varspace %s saved" %(self.instance_name))

    def set_frame_name(self):
        if self.is_default:
            self.label_frame['text'] = self.module.__name__ + ' - defaults'
        else:
            self.label_frame['text']  = self.module.__name__ + ':' +  self.instance_name
    
    def create_pane(self):
        self.param_frame = Frame(self.nbook())
        self.groupcount = 0

        self.label_frame = LabelFrame(self.param_frame,relief = GROOVE,bd = 2, labelanchor='nw')
        self.set_frame_name()

            
#        current_frame = Frame(self.param_frame,bd = 0)
        self.label_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E)
        self.groupcount += 1

        if self.is_default:
            label = Label(self.label_frame, text=self.DESCRIPTION)
            label.grid(row=0, column=0, sticky= W, padx=4) 
            
            button = Button(self.label_frame,text=_('Save as default'),command=self.save_callback)
            button.grid(row=0, column=1, sticky=E)        
        else:
            label = Label(self.label_frame, text=_('Instance name'))
            label.grid(row=0, column=0, sticky= W, padx=4) 
            
            self.tk_instance_name = StringVar()
            self.tk_instance_name.set(self.instance_name)
     
            entry = Entry(self.label_frame, width=15, textvariable=self.tk_instance_name)
            entry.grid(row=0, column=1, sticky=W,padx=4)
    
            button = Button(self.label_frame,text=_('Save'),command=self.save_callback)
            button.grid(row=0, column=2, sticky=E)
        
        
    def display_pane(self,tab_name):
        self.nbook.add_screen(self.param_frame,tab_name) # ,highlightcolor='blue',disabledforeground='yellow')
        self.nbook.display(self.param_frame)    # switch to it

    def add_item(self,frame,name,value,text,line,vdict):
                
        # print "    line %d add %s default %s label %s " %(line,name,value,text)
        optionlist = None
        if isinstance(text, list):  # OptionMenu = 'labeltext','choice1,'choice2'....
            optionlist = text[1:]
            label = text[0]
        else:
            label = text
        


        label = label % (self.var_dict[c.VARIABLES])
                        
        label = Label(frame, text=label)
        label.grid(row=line, column=0, sticky=N + W, padx=4) 
        
        width = 7 

        if  isinstance(value, float):
            self.tkVars[name] = DoubleVar()
            self.tkVars[name].set(value)
            entry = Entry(frame, width=width, textvariable=self.tkVars[name])
            self.tkVars[name].trace_variable("w", SimpleCallback(self.tkvar_changed_callback, name,vdict ))
            
        if  isinstance(value, int):
            self.tkVars[name] = IntVar()
            self.tkVars[name].set(value)
            entry = Entry(frame, width=width, textvariable=self.tkVars[name])
            self.tkVars[name].trace_variable("w", SimpleCallback(self.tkvar_changed_callback, name,vdict ))

        if  isinstance(value, basestring):
            if len(value) > width:
                width = len(value)
            self.tkVars[name] = StringVar()
            self.tkVars[name].set(value)
            entry = Entry(frame, width=width, textvariable=self.tkVars[name])
            self.tkVars[name].trace_variable("w", SimpleCallback(self.tkvar_changed_callback, name,vdict ))

        if  isinstance(value, bool):
            self.tkVars[name] = BooleanVar()
            self.tkVars[name].set(value)
            entry = Checkbutton(frame, variable=self.tkVars[name])
            self.tkVars[name].trace_variable("w", SimpleCallback(self.tkvar_changed_callback, name,vdict ))

        if optionlist:  # OptionMenu = 'labeltext','choice1,'choice2'....
            
            self.tkVars[name] = StringVar()
            self.tkVars[name].set(value) 
            entry = OptionMenu(frame, self.tkVars[name], *optionlist)     
            self.tkVars[name].trace_variable("w", SimpleCallback(self.tkvar_changed_callback, name,vdict ))

        entry.grid(row=line, column=1, sticky=N + E)


    def add_config_items(self): 
        self._add_config_items(self.param_frame,name=c.UNFRAMED,value=self.var_dict[c.UI_VARIABLES],line = 0)
        

    def _add_config_items(self,frame,name=None,value=None,line=0):

        self.var_dict.main.interpolation = False # avoid ConfigObj getting too clever
       
        if isinstance(value,dict): 
            line = 0            
            if name == c.UNFRAMED:       # no frame
                current_frame = Frame(frame,bd = 0)
            else:
                if name == c.FRAMED:    # unnamed frame
                    current_frame = Frame(frame,relief = GROOVE,bd = 2)
                else:                   # named frame
                    current_frame = LabelFrame(frame,relief = GROOVE,bd = 2, labelanchor='nw',text = name)
            current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E,columnspan=2)
            current_frame.columnconfigure(0, weight=1)

            self.groupcount +=1
            
            for k,v in value.items():
                self._add_config_items(current_frame,name=k,value=v,line=line)  # recurse
                line += 1
        else:
            self.add_item(frame,name,self.var_dict[c.VARIABLES][name],value,line,self.var_dict[c.VARIABLES])
 


    def add_button(self, text,name, callback): 
        col = 0
        current_frame = Frame(self.param_frame,bd = 0)
        labeltext = text % (self.var_dict[c.VARIABLES])
        buttontext = name % (self.var_dict[c.VARIABLES])
        if len(text) > 0:
            label = Label(current_frame, text=labeltext)
            label.grid(row=0, column=0, sticky=N + W, padx=4) 
            col += 1   
        current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E) 
        button = Button(current_frame,text=buttontext,command=SimpleCallback(callback,name))
        button.grid(row=0, column=col, sticky=N )
        current_frame.columnconfigure(0, weight=1)
        self.groupcount += 1


class PluginLoader(object):
    """
    FIXME
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
    
    
    based on code from http://code.activestate.com/recipes/436873/ 
    Copyright 2005 Jesse Noller <jnoller@gmail.com>
    
    """    
    
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
        self.window = window

    def activate(self,plugin_dir,base_name,cfg_path):
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
        _instance.window = self.window
        _instance.nbook = self.window.nbook
        _instance.is_default = instance_name == _module.__name__

        # startup_plugin is a Plugin superclass method (in VarSpace)
        _instance.startup_plugin(cfg_path)
        
        g.plugins[instance_name] = _instance
        self.modules[instance_name] = _module
        return _instance



    def activate_all(self,plugin_dir,varspaces_dir):
        
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
                _instance = self.activate(plugin_dir, _basename, _default_config)
                    
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
                    
                    _instance = self.activate(plugin_dir,_basename,vs)
   
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
            if plugin_dir and (plugin_dir not in sys.path):
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
        
        