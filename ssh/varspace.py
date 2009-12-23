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
import logging

from Tkconstants import  N, S, E, W, GROOVE
from Tkinter import OptionMenu, Frame, Checkbutton, Button, Label, Entry,LabelFrame
from Tkinter import StringVar, DoubleVar, IntVar,BooleanVar
from configobj import ConfigObj, flatten_errors
from validate import Validator

from dotdictlookup import DictDotLookup
from simplecallback import SimpleCallback
from exceptions import *
import globals as g
import constants as c

class VarSpace:
    def __init__(self, specname, pathname, instance_name,frame=None,specversion=None,rename_hook=None,default=False,plugin=None):

        self.var_dict = dict()
        self.tkVars = dict()
        self.groupcount = 0
        self.spec = ConfigObj(specname, interpolation=False, list_values=False, _inspec=True)
        self.pathname = pathname
        self.nbook = frame
        self.instance_name = instance_name
        self.tk_instance_name = None
        self.rename_hook = rename_hook
        self.tab_button = None
        self.default_config = False # wether a new name was generated
        self.load_varspace(specversion)
        self.is_default = default
        self.plugin = plugin
        
    def cleanup(self,save=True,remove=False):
        """
        close a varspace instance
        optionally save/remove persistence file
        remove parameter pane from window
        """
        if save:
            self.save_varspace()
            g.logger.logger.debug( 'varspace %s saved' %(self.instance_name))
        if remove:
            os.remove(self.pathname)
            g.logger.logger.info( 'varspace %s deleted' %(self.instance_name))

        if self.tab_button:
            self.tab_button.destroy()
        
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
                    raise BadConfigFileError 
                    
                # check config file version against internal version
                if specversion:
                    fileversion = self.var_dict['Version']['specversion'] # this could raise KeyError
                    if fileversion != specversion:
                        print 
                        g.logger.logger.error( 'config file vesions do not match - internal: "%(specversion)s", config file "%(fileversion)s"' %(locals()))
                        raise BadConfigFileError
                    
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
    
    def save_varspace(self):
        self.var_dict.filename = self.pathname
        self.var_dict.write()   
    
    def print_vars(self):
        print "Variables:"
        for k,v in self.var_dict['Variables'].items():
            print k," = ",v


    def tkvar_changed_callback(self,varname,vdict,name,index,mode):
        try:
            value = self.tkVars[varname].get()
        except ValueError:
            # g.logger.logger.debug("VALUE ERROR %s " %(varname))
            # reset to default value if funny keys are pressed
            self.tkVars[varname].set(vdict[varname])
            pass
        else:
            #g.logger.logger.debug("%s changed from %s to %s" %(varname,vdict[varname],value))
            vdict[varname] = value

    def save_callback(self):
        if self.is_default:
            self.save_varspace()
            g.logger.logger.debug("varspace %s (default) saved" %(self.instance_name))  
        else:         
            if self.tk_instance_name.get() != self.instance_name:
                
                old_instance = self.instance_name
                old_path = self.pathname
                self.instance_name = self.tk_instance_name.get()
    
                self.pathname = os.path.join(os.path.dirname(old_path),self.instance_name+c.CONFIG_EXTENSION)
                self.save_varspace()
                # TODO robustify + log
                os.remove(old_path)
                self.tab_button.tv.set(self.instance_name)
                self.tab_button['width'] = len(self.instance_name)
                
                # call hook to fixup menu entries
                if self.rename_hook:
                    self.rename_hook(old_instance,self.instance_name)
                
            else:
                self.save_varspace()
                g.logger.logger.debug("varspace %s saved" %(self.instance_name))

        
    def create_pane(self):
        self.param_frame = Frame(self.nbook())
        self.groupcount = 0

        current_frame = Frame(self.param_frame,bd = 0)
        current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E)
        self.groupcount += 1

        if self.is_default:
            label = Label(current_frame, text=self.plugin.DESCRIPTION)
            label.grid(row=0, column=0, sticky= W, padx=4) 
            
            button = Button(current_frame,text=_('Save as default'),command=self.save_callback)
            button.grid(row=0, column=1, sticky=E)        
        else:
            label = Label(current_frame, text=_('Instance name'))
            label.grid(row=0, column=0, sticky= W, padx=4) 
            
            self.tk_instance_name = StringVar()
            self.tk_instance_name.set(self.instance_name)
     
            entry = Entry(current_frame, width=15, textvariable=self.tk_instance_name)
            entry.grid(row=0, column=1, sticky=W,padx=4)
    
            button = Button(current_frame,text=_('Save'),command=self.save_callback)
            button.grid(row=0, column=2, sticky=E)
        
        
    def display_pane(self,tab_name):
        self.tab_button = self.nbook.add_screen(self.param_frame,tab_name)

    def add_item(self,frame,name,value,text,line,vdict):
                
        #print "    line %d add %s default %s label %s " %(line,name,value,labeltext)
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

        current_frame = None

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


        