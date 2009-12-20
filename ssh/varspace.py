'''

VarSpace implements:

- a persistent, typed  variable store (self.var_dict) using ConfigObj 
    (including automatic type conversion when reading from INI file)
    plus some basic type and range checking on the INI file 
- a method to create a default INI file from the specifification
- a user interface abstraction so ShapeSetHandler may remain UI-agnostic
     this is a minimal interface to create parameter entry fields & buttons for
     Tkinter, driven by config file contents
     

Created on 07.12.2009

@author: Michael Haberler
'''

import os
import logging

from Tkconstants import  N, S, E, W, GROOVE
from Tkinter import OptionMenu, Frame, Checkbutton, Button, Label, Entry,LabelFrame
from Tkinter import StringVar, DoubleVar, IntVar,BooleanVar
from configobj import ConfigObj, flatten_errors
from validate import Validator

from dotdictlookup import DictDotLookup
import globals as g
import constants as c


class VarSpace:
    def __init__(self, specname, pathname, instance_name,specversion=None,pluginloader=None):

        self.var_dict = dict()
        self.tkVars = dict()
        self.groupcount = 0
        self.spec = ConfigObj(specname, interpolation=False, list_values=False, _inspec=True)
        self.pathname = pathname
        self.instance_name = instance_name
        self.pluginloader = pluginloader
        self._initialize(specversion)

    def cleanup(self):
        '''
        delete a varspace instance
        remove parameter pane from window
        '''
        g.logger.logger.info( 'cleanup varspace %s "' %(self.instance_name))

        if g.config.config.General.save_on_instance_delete:
            self.save_varspace()
        self.tab_button.destroy()
        #self.param_frame.destroy()
        
    def _initialize(self,specversion):

        if os.path.isfile(self.pathname):

            # file exists, read & validate it
            self.var_dict = ConfigObj(self.pathname, configspec=self.spec, interpolation=False)
            _vdt = Validator()
            result = self.var_dict.validate(_vdt, preserve_errors=True)
            validate_errors = flatten_errors(self.var_dict, result)
            if validate_errors:
                g.logger.logger.error("errors reading %s:" % (self.pathname))
            for entry in validate_errors:
                # each entry is a tuple
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
                # print "Errors reading %(path)s - delete file to recreate defaults" % (self.__dict__)
                
            # check config file version against internal version
            if specversion:
                fileversion = self.var_dict['Version']['specversion']
                if fileversion != specversion:
                    print 
                    g.logger.logger.error( 'config file vesions do not match - internal: "%(specversion)s", config file "%(fileversion)s"' %(locals()))
                    raise BadConfigFileError      
            g.logger.logger.debug("read existing varspace '%s'" %(self.pathname))
        else:
            self.create_default_varspace()
            g.logger.logger.debug("created default varspace '%s'" %(self.pathname))

        # convenience - flatten nested config dict to access it via self.config.sectionname.varname
        self.var_dict.main.interpolation = False # avoid ConfigObj getting too clever
        self.vars = DictDotLookup(self.var_dict) # FIXME
            
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
        for frame,content in self.var_dict['UI'].items():
            #print " frame=%(frame)s" %(locals())
            for varname,text in content.items():
                value  = self.var_dict['Variables'][varname]
                print "%(varname)s = %(value)s" %(locals())

    def _scalarChanged(self,varname,name,index,mode):
        try:
            value = self.tkVars[varname].get()
        except ValueError:
            pass
        else:
            g.logger.logger.debug(  "%s changed from %s to %s" %(varname,self.var_dict['Variables'][varname],value))
            self.var_dict['Variables'][varname] = value

    def save_callback(self):
        if self.tk_instance_name.get() != self.instance_name:
            
            old_instance = self.instance_name
            old_path = self.pathname
            self.instance_name = self.tk_instance_name.get()

            self.pathname = os.path.join(os.path.dirname(old_path),self.instance_name+c.CONFIG_EXTENSION)
            self.save_varspace()
            # FIXME robustify + log
            os.remove(old_path)
            self.tab_button.tv.set(self.instance_name)
            # call hook to fix menu entries
            
            if self.pluginloader:
                self.pluginloader.rename_instance(old_instance,self.instance_name)
            
        else:
            self.save_varspace()
    
    def make_instancemenu(self,foo):
        print "make_instancemenu"
        
    def create_pane(self,nbook):
        self.nbook_frame = nbook()
        self.param_frame = Frame(self.nbook_frame)
        self.groupcount = 0
        
        self.param_frame.bind("<Button-3>", self.make_instancemenu)
        self.param_frame.bind("<Button-2>", self.make_instancemenu)
  #      self.param_frame.bind("<Enter>", self.make_instancemenu)
        
        
        
        current_frame = Frame(self.param_frame,bd = 0)
        current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E)
 #       current_frame.columnconfigure(0, weight=1)
        
        label = Label(current_frame, text='Instance name')
        label.grid(row=0, column=0, sticky= W, padx=4) 
        
        self.tk_instance_name = StringVar()
        self.tk_instance_name.set(self.instance_name)
 
        entry = Entry(current_frame, width=15, textvariable=self.tk_instance_name)
        entry.grid(row=0, column=1, sticky=W,padx=4)

        button = Button(current_frame,text='Save',command=self.save_callback)
        button.grid(row=0, column=2, sticky=E)
#        current_frame.columnconfigure(0, weight=1)

        
    def display_pane(self,parent,tab_name):
        self.tab_button = parent.add_screen(self.param_frame,tab_name)


    def add_config_items(self): #,config):
        currgroup = None
        self.groupcount = 0
        linecount = 0
        current_frame = None

        self.var_dict.main.interpolation = False # avoid ConfigObj getting too clever
        
        for group,content in self.var_dict['UI'].items():            
            for k,v in content.items():
                optionlist = None
                if isinstance(v, list):  # OptionMenu = 'labeltext','choice1,'choice2'....
                    varname = k
                    labelvar = v[0]
                    optionlist = v[1:]
                else:                   # scalars just have varname = labeltext
                    (varname,labelvar) = (k,v)
                value = self.var_dict['Variables'][varname]
                # print "    varname=%(varname)s value=%(value)s labeltext=%(labeltext)s labelvar=%(labelvar)s" %(locals())
                if group != currgroup:
                    currgroup = group
                    self.groupcount += 1
                    linecount = 0
                    if currgroup == 'UNFRAMED':       # no frame
                        current_frame = Frame(self.param_frame,bd = 0)
                    else:
                        if currgroup == 'FRAMED' :    # unnamed frame
                            current_frame = Frame(self.param_frame,relief = GROOVE,bd = 2)
                        else:                   # named frame
                            current_frame = LabelFrame(self.param_frame,relief = GROOVE,bd = 2, labelanchor='nw',text = group)
                    current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E)
                    current_frame.columnconfigure(0, weight=1)
                    
                labeltext = labelvar % (self.var_dict['Variables']) # (config.__dict__)
                label = Label(current_frame, text=labeltext)
                label.grid(row=linecount, column=0, sticky=N + W, padx=4) 
                width = 7
                # generate appropriate widget for type
                if  isinstance(value, float):
                    self.tkVars[varname] = DoubleVar()
                    self.tkVars[varname].set(value)
                    entry = Entry(current_frame, width=width, textvariable=self.tkVars[varname])
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))
                    
                if  isinstance(value, int):
                    self.tkVars[varname] = IntVar()
                    self.tkVars[varname].set(value)
                    entry = Entry(current_frame, width=width, textvariable=self.tkVars[varname])
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                if  isinstance(value, basestring):
                    if len(value) > width:
                        width = len(value)
                    self.tkVars[varname] = StringVar()
                    self.tkVars[varname].set(value)
                    entry = Entry(current_frame, width=width, textvariable=self.tkVars[varname])
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                if  isinstance(value, bool):
                    self.tkVars[varname] = BooleanVar()
                    self.tkVars[varname].set(value)
                    entry = Checkbutton(current_frame, variable=self.tkVars[varname])#, offvalue=False, onvalue=True)  
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                if  optionlist:
                    self.tkVars[varname] = StringVar()
                    self.tkVars[varname].set(value) 
                    entry = OptionMenu(current_frame, self.tkVars[varname], *optionlist)     
                    self.tkVars[varname].trace_variable("w", SimpleCallback(self._scalarChanged, varname ))

                entry.grid(row=linecount, column=1, sticky=N + E)
                linecount += 1   
            #self.groupcount
            

    def add_button(self, text,name, callback): #,config):
        self.groupcount += 1
        col = 0
        current_frame = Frame(self.param_frame,bd = 0)
        labeltext = text % (self.var_dict['Variables'])
        buttontext = name % (self.var_dict['Variables'])
        if len(text) > 0:
            label = Label(current_frame, text=labeltext)
            label.grid(row=0, column=0, sticky=N + W, padx=4) 
            col += 1   
        current_frame.grid(row=self.groupcount, column=0, padx=2, pady=2, sticky=N + W + E) 
        button = Button(current_frame,text=buttontext,command=SimpleCallback(callback,name))
        button.grid(row=0, column=col, sticky=N )
        current_frame.columnconfigure(0, weight=1)
        

# http://www.astro.washington.edu/users/rowen/TkinterSummary.html#CallbackShims
class SimpleCallback:
    """Create a callback shim. Based on code by Scott David Daniels
    (which also handles keyword arguments).
    """
    def __init__(self, callback, *firstArgs):
        self.__callback = callback
        self.__firstArgs = firstArgs
    
    def __call__(self, *args):
        return self.__callback (*(self.__firstArgs + args))


if __name__ == "__main__":
    pass

