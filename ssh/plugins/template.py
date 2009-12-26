# -*- coding: iso-8859-1 -*-
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
    template for dxf2gcode export/transform plugin

    this is always the best-maintained example for a plugin

    Michael Haberler  20.12.2009
'''
import sys

from varspace import  VarSpace
import globals as g
import constants as c

class Plugin(VarSpace):
    """
    Template for a dxf2gcode plugin
    
    Plugin() class variables as listed are required - leave the names untouched, fill in the values
    as needed. 
    
    The user interface will display an export option if the C{export} method is defined, and 
    a transform option if the C{transform} method is defined. If you dont need one of them, just
    remove the method.
    
    The persistent storage is described in C{SPECNAME} and implemented by the VarSpace class, which
    uses I{ConfigObj} and I{Validate} for reading, writing, validating and type conversion. 
    For C{SPECNAME} syntax and semantics, see:
        - for ConfigObj: U{http://www.voidspace.org.uk/python/configobj.html} 
        - for Validate: U{http://www.voidspace.org.uk/python/validate.html}
    """
   
    def __init__(self):

        """
        FIXME
        
        required for plugin syntax validation but should not do anything exotic -
        real initialization happens through I{initialize(self,...)} which is 
        called once the plugin is syntactically validated
        """
        
        self.shapeset_handlers = {
                'export'    :  { 'menu_entry' : 'demo export','method':self.export},
                'transform' :  { 'menu_entry' : 'demo pocketing','method':self.transform},
 #               'xyzzy'     :  { 'menu_entry' : 'random plugin method','method':self.xyzzy}
            }
        """
        dictionary of function names and corresponding menu entries
        
        only methods actually defined in this plugin may be added
        """
        
        self.DESCRIPTION =   'template for new plugins'
        """verbose plugin description  (for user interface 'About', hovers etc)"""
        
        self.VERSION =       '0.1'
        """plugin version number"""
        
        self.CLONABLE = True
        """ several instances of this plugin may exist"""
        
        self.HIDDEN_AT_STARTUP = False
        """ displayed at startup """
        
        self.SPECVERSION =   12      
        """running version number of the varspace .cfg file format
        
            Increment this value time you change a non-comment field in SPECNAME. 
            
            If an old varspace.cfg file is detected, it is renamed with a .bad suffix and a new
            default config file with the same instance name is generated.
            """
    
        self.SPECNAME = str('''
        # do not edit the following section name:
            [Version]
        
            # do not edit the following value:
            specversion =  integer(default='''  + 
            str(self.SPECVERSION) + ''')
    
            
            [''' + c.VARIABLES +
            
            ''']
            
    
    
            # persistent variables
            tool_dia = float(default=63.0)
            start_radius = float(default=0.0)
            axis3_safe_margin = float(default=20.0)
            axis3_slice_depth = float(default=0.5)
            axis3_mill_depth = float(default=10.0)
            f_g1_depth = float(default=50.0)
            f_g1_plane = float(default=150.0)
            # Tests
            booltrue = boolean(default=True)
            boolfalse = boolean(default=False)
            option    = string(default='bar')
        
            unframed_int = integer(default=50)
            
            ax1_letter = string(default="X")
            ax2_letter = string(default="Y")
            ax3_letter = string(default="Z")
                  
            random_text    = string(default='ver random')
           
                      
            [''' + c.UI_VARIABLES +
            ''']
            # Variables listed here are displayed in the UI and are editable
            # the string value is the descriptive text displayed in a Label
            # variables from the Variables section can be interpolated into
            # e.g. Label names
            
            [[FRAMED]]
                random_text = string(default="Random Text")
                
            [[UNFRAMED]]
                unframed_int = string(default="Edit int value:")
                
                
            #named frames:
            [[Tool Parameters]]
                tool_dia = string(default= "Tool diameter [mm]:")
                start_radius = string(default= "Start radius (for tool comp.) [mm]:")
            [[Depth Coordinates]]
                axis3_safe_margin = string(default= "%(ax3_letter)s safety margin [mm]:")
                axis3_slice_depth = string(default= "%(ax3_letter)s infeed depth [mm]:")
                axis3_mill_depth = string(default=  "%(ax3_letter)s mill depth [mm]:")
            [[Feed Rates]]
                f_g1_depth = string(default= "G1 feed %(ax3_letter)s-direction [mm/min]:")
                f_g1_plane = string(default= "G1 feed %(ax1_letter)s%(ax2_letter)s-direction [mm/min]:")
                
            [[Test]]
                # pre-set boolean variables
                booltrue = string(default = "Checked")
                boolfalse = string(default = "Unchecked")
                
                # a OptionMenu - labeltext is first element, rest is choices:
                option = string_list(default=list('Tick one of:','foo', 'bar', 'baz'))
        
        ''').splitlines()  
        """ variable and UI description"""

    
    
    def __del__self(self):
        print "TEMPLATE __del__"
        
    def cleanup(self):
        """
        called when closing a plugin instance
        
        add any plugin-specific cleanup actions here as needed.

        @return: None.
        """
        g.logger.logger.info("%s.%s()  called" %(self.instance_name,sys._getframe(0).f_code.co_name))

    def initialize(self):
        """
        
        FXIME
        @param varspace: container for persistent plugin variables
          
            This contains the variables for this plugin as described in I{SPECNAME}, 
            sections C{[Variables]} and C{[UI]}.
     
            Variables are persisent - if you change a value or change a field in parameter pane, 
            and close the plugin or exit the program, it's values will be preserved.       
            
            The variables are already read from the .cfg file (either an existing instance, or a
            new default instance) and converted to the proper type. Variable values may be 
            access in "dot notation" like member attributes through the I{vars} attribute.
            
            Example: the variable specified in the config file fragment as per SPECNAME above::
                [Variables]
                tool_dia = 63.0
                
            may be referred to in the plugin as::
            
                self.vs.vars.Variables.tool_dia
        
            The plugin instance name is available as C{self.instance_name} .
        
        @type varspace: an instance of VarSpace
              
        @return: True if initialization went OK, False otherwise. 

            Returning True will cause this Plugin() instance to be added to the list of
            active plugins.

        """
        g.logger.logger.info("%s.%s()  called" %(self.instance_name,sys._getframe(0).f_code.co_name))
        
        #self.vs = varspace  # remember my varspace
        # create parameter pane with instance edit, save button
        # parent is the notebook widget
        self.create_pane()
        # layout variables as per INI file
        self.add_config_items()
        
        # Example: manually add buttons at bottom
        self.add_button("",_("Show variables"), self._show_params)
        
        # and display as notebook screen
        self.display_pane(self.instance_name)
        
        return True

    def export(self,shapes):
        """
        export a shapeset for your purpose - for instance, G-Code.
        
        A plugin may contain an C{export} or a C{transform} method, or both. The export method is selected
        by choosing the EXPORT_MENU_ENTRY option in the context menu. 
        
        @param shapes: The list of shapes selected for output
            when the export() function was called.

        @type shapes: an instance of ShapeSet.
        
        @return: None.
        """

        g.logger.logger.info("%s.%s()  called" %(self.instance_name,sys._getframe(0).f_code.co_name))



    def transform(self,shapes):
        """
        do some transformation on shapes and
        return modified shapes
        
        A plugin may contain an C{export} or a C{transform} method, or both. The transform method is selected
        by choosing the TRANSFORM_MENU_ENTRY option in the context menu. 
        
        @param shapes: The list of shapes selected for output
            when the transform() function was called.

        @type shapes: an instance of ShapeSet .
        
        @return: a ShapeSet .
        """

        g.logger.logger.info("%s.%s()  called" %(self.instance_name,sys._getframe(0).f_code.co_name))

        return self.my_transform(shapes)


# ---- opional user defined functions
    def my_transform(self,shapes):
        """
        here's your transformation function
        """
        return shapes
    
    def _show_params(self,name):
        """ 
        demonstrate a button callback 
        """
        self.print_vars()
                 