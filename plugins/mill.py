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
    Example dxf2gcode export plugin

    Michael Haberler  20.12.2009
'''
import sys

from varspace import  VarSpace
import globals as g
import constants as c


class Plugin(VarSpace):
    """
    Template for a dxf2gcode plugin
    
    Required Plugin() class variables - leave the names untouched, fill in the values
    as needed. Make sure I{tag} does not collide with another plugin's tag value. 
     
        - EXPORT_MENU_ENTRY - description for menu item
        - DESCRIPTION -  verbose plugin description  (for user interface 'About)
        - VERSION - plugin version
        - SPECVERSION - running version number of the cfg file format - increment this
        any time you change a non-comment field in SPECNAME
        - SPECNAME  - variable and UI description.
    
    This module uses I{ConfigObj} and I{Validate} 
        - for ConfigObj see U{http://www.voidspace.org.uk/python/configobj.html} 
        - for Validate see U{http://www.voidspace.org.uk/python/validate.html}
    """
    

    def __init__(self):
        """
        FIXME
                required for plugin syntax validation but should not do anything exotic -
        real initialization happens through I{initialize(self,...)} which is 
        called once the plugin is syntactically validated
        """
        self.shapeset_handlers = {
                'export'    :  { 'menu_entry' : 'mill shape', 'method':self.export},
                'transform' :  { 'menu_entry' : 'pocket shape', 'method':self.transform},
 #               'xyzzy'     :  { 'menu_entry' : 'random plugin method','method':self.xyzzy}
            }
        """
        dictionary of function names and corresponding menu entries
        
        only methods actually defined in this plugin may be added
        """

        self.DESCRIPTION = 'mill export'
        self.VERSION = '0.02'
        self.CLONABLE = True
        self.VISIBLE_AT_STARTUP = True
      
        self.SPECVERSION = 27        # increment this whenever you edit SPECNAME
        self.SPECNAME = str('''
        # do not edit the following section name:
            [Version]
        
            # do not edit the following value:
            specversion = integer(default=''' + \
            str(self.SPECVERSION) + ')\n' + 
        '''
            
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
            
            ax1_letter = string(default="X")
            ax2_letter = string(default="Y")
            ax3_letter = string(default="Z")
                  
           
                     
            [''' + c.UI_VARIABLES + 
            ''']
            # Variables listed here are displayed in the UI and are editable
            # the string value is the descriptive text displayed in a Label
            # variables from the Variables section can be interpolated into
            # e.g. Label names

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
                
        
        ''').splitlines()  
    
    def cleanup(self):
        """
        called when closing a plugin instance
        
        add any plugin-specific cleanup actions here as needed.

        @return: None.
        """
        g.logger.info("cleanup plugin %s" % (self.instance_name))

    def initialize(self):
        """
        FIXME
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
        
            The plugin instance name is available as C{self.vs.instance_name} .
        
        @type varspace: an instance of VarSpace
              
        @return: True if initialization went OK, False otherwise. 

            Returning True will cause this Plugin() instance to be added to the list of
            active plugins.

        """        
        # create parameter pane with instance edit, save button
        # parent is the notebook widget
        self.create_pane()
        # layout variables as per INI file
        self.add_config_items()
        # manually add buttons at bottom
        #self.add_button("",_("Show variables"), self._show_params)
        # and display as notebook screen
        self.display_pane(self.instance_name)
        
        return True

    def export(self, Content):
        """
        export a shapeset for your purpose - for instance, G-Code.
        
        A plugin may contain an C{export} or a C{transform} method, or both. The export method is selected
        by choosing the EXPORT_MENU_ENTRY option in the context menu. 
        
        @param shapes: The list of shapes selected for output
            when the export() function was called.

        @type shapes: an instance of ShapeSet.
        
        @return: None.
        """

        g.logger.info("%s.%s()  called" % (self.instance_name, sys._getframe(0).f_code.co_name))

        for shape_nr in range(len(Content.Shapes)):
            shape = Content.Shapes[shape_nr]
            if not(shape.nr in Content.Disabled):
                
                g.logger.info("%s.%s()  shape %s " % (self.instance_name,
                                                    sys._getframe(0).f_code.co_name,
                                                    shape))

#                self.shapes_to_write.append(shape)
#                shapes_st_en_points.append(shape.get_st_en_points())
        
        
#        #Bei 1 starten da 0 der Startpunkt ist
#        for nr in range(1, len(self.TSP.opt_route)):
#            shape = self.shapes_to_write[self.TSP.opt_route[nr]]
#            g.logger.debug(_("Writing Shape: %s") % shape)
#                
#            #Drucken falls die Shape nicht disabled ist
#            if not(shape.nr in self.CanvasContent.Disabled):
##                #Falls sich die Fräserkorrektur verändert hat diese in File schreiben
##                stat = shape.Write_GCode(config, postpro)
##                status = status * stat
#                g.logger.debug("  Shape: %s" % ( shape))

    def transform(self, shapes):
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

        g.logger.info("%s.%s()  called" % (self.instance_name, sys._getframe(0).f_code.co_name))

        return self.my_transform(shapes)


    def xyzzy(self, shapes):

        g.logger.info("%s.%s()  called" % (self.instance_name, sys._getframe(0).f_code.co_name))
        
# ---- opional user defined functions
    def my_transform(self, shapes):
        """
        here's your transformation function
        """
        return shapes
    
    def _show_params(self, name):
        """ 
        demonstrate a button callback 
        """
        self.print_vars()
                 
