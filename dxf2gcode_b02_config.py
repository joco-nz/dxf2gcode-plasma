#!/usr/bin/python
# -*- coding: cp1252 -*-
#
#dxf2gcode_b02_config.py
#Programmers:   Christian Kohloeffel
#               Vinzenz Schulz
#
#Distributed under the terms of the GPL (GNU Public License)
#
#dxf2gcode is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#About Dialog
#First Version of dxf2gcode Hopefully all works as it should
#Compiled with --onefile --noconsole --upx --tk dxf2gcode_b02.py

#Loeschen aller Module aus dem Speicher
import sys, os, string
import ConfigParser
import time

from tkMessageBox import showwarning, showerror
from Tkconstants import END
from Tkinter import DoubleVar, IntVar

from math import degrees

from dxf2gcode_b02_point import PointClass

class ConfigClass:
    def __init__(self,textbox,FOLDER,APPNAME):
        self.folder=os.path.join(FOLDER,'config')
        self.appname=APPNAME
        # Das Standard App Verzeichniss fuer das Betriebssystem abfragen
        self.make_settings_folder()

        # eine ConfigParser Instanz oeffnen und evt. vorhandenes Config File Laden        
        self.parser = ConfigParser.ConfigParser()
        self.cfg_file_name=self.appname+'_config.cfg'
        self.parser.read(os.path.join(self.folder,self.cfg_file_name))

        # Falls kein Config File vorhanden ist oder File leer ist neue File anlegen und neu laden
        if len(self.parser.sections())==0:
            self.make_new_Config_file()
            self.parser.read(os.path.join(self.folder,self.cfg_file_name))
            textbox.prt((_('\nNo config file found generated new on at: %s') \
                             %os.path.join(self.folder,self.cfg_file_name)))
        else:
            textbox.prt((_('\nLoading config file:%s') \
                             %os.path.join(self.folder,self.cfg_file_name)))

        #Tkinter Variablen erstellen zur späteren Verwendung in den Eingabefeldern        
        self.get_all_vars()

        #DEBUG INFORMATIONEN
        #Übergeben des geladenen Debug Level
        textbox.set_debuglevel(DEBUG=self.debug)
        textbox.prt(_('\nDebug Level: %i') %(self.debug),1)
        textbox.prt(str(self),1)

    def make_settings_folder(self): 
        # create settings folder if necessary 
        try: 
            os.mkdir(self.folder) 
        except OSError: 
            pass 

    def make_new_Config_file(self):
        
        #Generelle Einstellungen für Export
        self.parser.add_section('General')
        self.parser.set('General', 'write_to_stdout', 0)
        
        self.parser.add_section('Paths') 
        self.parser.set('Paths', 'load_path', 'C:\Users\Christian Kohloeffel\Documents\DXF2GCODE\trunk\dxf')
        self.parser.set('Paths', 'save_path', 'C:\Users\Christian Kohloeffel\Documents')

        self.parser.add_section('Import Parameters') 
        self.parser.set('Import Parameters', 'point_tolerance', 0.01)
        self.parser.set('Import Parameters', 'fitting_tolerance', 0.01)   
        self.parser.set('Import Parameters', 'spline_check',1)  
                   
        self.parser.add_section('Tool Parameters') 
        self.parser.set('Tool Parameters', 'diameter', 2.0)
        self.parser.set('Tool Parameters', 'start_radius', 0.2)

        self.parser.add_section('Plane Coordinates') 
        self.parser.set('Plane Coordinates', 'axis1_start_end', 0)
        self.parser.set('Plane Coordinates', 'axis2_start_end', 0)

        self.parser.add_section('Depth Coordinates') 
        self.parser.set('Depth Coordinates', 'axis3_retract', 15)
        self.parser.set('Depth Coordinates', 'axis3_safe_margin', 3.0)
        self.parser.set('Depth Coordinates', 'axis3_mill_depth', -3.0)
        self.parser.set('Depth Coordinates', 'axis3_slice_depth', -1.5)

        self.parser.add_section('Feed Rates')
        self.parser.set('Feed Rates', 'f_g1_depth', 150)
        self.parser.set('Feed Rates', 'f_g1_plane', 400)

        self.parser.add_section('Axis letters')
        self.parser.set('Axis letters', 'ax1_letter', 'X')
        self.parser.set('Axis letters', 'ax2_letter', 'Y')
        self.parser.set('Axis letters', 'ax3_letter', 'Z')                  

        self.parser.add_section('Route Optimisation')
        self.parser.set('Route Optimisation', 'Begin art','heurestic')
        self.parser.set('Route Optimisation', 'Max. population', 20)
        self.parser.set('Route Optimisation', 'Max. iterations', 300)  
        self.parser.set('Route Optimisation', 'Mutation Rate', 0.95)

        self.parser.add_section('Filters')
        self.parser.set('Filters', 'pstoedit_cmd','C:\Program Files (x86)\pstoedit\pstoedit')
        self.parser.set('Filters', 'pstoedit_opt', ['-f','dxf','-mm'])
                     
        self.parser.add_section('Debug')
        self.parser.set('Debug', 'global_debug_level', 0)         
                
        open_file = open(os.path.join(self.folder,self.cfg_file_name), "w") 
        self.parser.write(open_file) 
        open_file.close()
            
    def get_all_vars(self):
        #try:   
        self.write_to_stdout=int(self.parser.get('General', 'write_to_stdout'))
        

        self.tool_dia=DoubleVar()
        self.tool_dia.set(float(self.parser.get('Tool Parameters','diameter')))

        self.start_rad=DoubleVar()
        self.start_rad.set(float(self.parser.get('Tool Parameters','start_radius')))        
       
        self.axis1_st_en=DoubleVar()
        self.axis1_st_en.set(float(self.parser.get('Plane Coordinates','axis1_start_end')))

        self.axis2_st_en=DoubleVar()
        self.axis2_st_en.set(float(self.parser.get('Plane Coordinates','axis2_start_end')))        
        
        self.axis3_retract=DoubleVar()
        self.axis3_retract.set(float(self.parser.get('Depth Coordinates','axis3_retract')))
        
        self.axis3_safe_margin=DoubleVar()
        self.axis3_safe_margin.set(float(self.parser.get('Depth Coordinates','axis3_safe_margin')))

        self.axis3_slice_depth=DoubleVar()
        self.axis3_slice_depth.set(float(self.parser.get('Depth Coordinates','axis3_slice_depth')))        

        self.axis3_mill_depth=DoubleVar()
        self.axis3_mill_depth.set(float(self.parser.get('Depth Coordinates','axis3_mill_depth')))        
        
        self.F_G1_Depth=DoubleVar()
        self.F_G1_Depth.set(float(self.parser.get('Feed Rates','f_g1_depth')))

        self.F_G1_Plane=DoubleVar()
        self.F_G1_Plane.set(float(self.parser.get('Feed Rates','f_g1_plane')))

        self.points_tolerance=DoubleVar()
        self.points_tolerance.set(float(self.parser.get('Import Parameters','point_tolerance')))

        self.fitting_tolerance=DoubleVar()
        self.fitting_tolerance.set(float(self.parser.get('Import Parameters','fitting_tolerance')))
        self.spline_check=int(self.parser.get('Import Parameters', 'spline_check')  )

        #Zuweisen der Werte fuer die TSP Optimierung
        self.begin_art=self.parser.get('Route Optimisation', 'Begin art')
        self.max_population=int((int(self.parser.get('Route Optimisation', 'Max. population'))/4)*4)
        self.max_iterations=int(self.parser.get('Route Optimisation', 'Max. iterations'))  
        self.mutate_rate=float(self.parser.get('Route Optimisation', 'Mutation Rate', 0.95))

        #Zuweisen der Axis Letters
        self.ax1_letter=self.parser.get('Axis letters', 'ax1_letter')
        self.ax2_letter=self.parser.get('Axis letters', 'ax2_letter')
        self.ax3_letter=self.parser.get('Axis letters', 'ax3_letter')

        #Holen der restlichen Variablen
        #Verzeichnisse
        self.load_path=self.parser.get('Paths','load_path')
        self.save_path=self.parser.get('Paths','save_path')

        #Holen der Commandos fuer pstoedit
        self.pstoedit_cmd=self.parser.get('Filters','pstoedit_cmd')
        self.pstoedit_opt=self.parser.get('Filters','pstoedit_opt')

        #Setzen des Globalen Debug Levels
        self.debug=int(self.parser.get('Debug', 'global_debug_level'))
        
        
#        except:
#            showerror(_("Error during reading config file"), _("Please delete or correct\n %s")\
#                      %(os.path.join(self.folder,self.cfg_file_name)))
#            raise Exception, _("Problem during import from INI File") 
#            
    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str

class PostprocessorClass:
    def __init__(self,config=None,textbox=None,FOLDER='',APPNAME='',VERSION='',DATE=''):
        self.folder=os.path.join(FOLDER,'postprocessor')
        self.appname=APPNAME
        self.version=VERSION
        self.date=DATE
        self.string=''
        self.textbox=textbox
        self.config=config
        
        # eine ConfigParser Instanz oeffnen und evt. vorhandenes Config File Laden        
        self.parser = ConfigParser.ConfigParser()
        
        #Leser der Files im Config Verzeichniss für Postprocessor
        try:
            lfiles = os.listdir(self.folder)
        except:
           # Das Standard App Verzeichniss fuer das Betriebssystem abfragen
            self.make_settings_folder() 
            self.postpro_file_name=self.appname+'_postprocessor.cfg'
            
            self.make_new_postpro_file()
            self.parser.read(os.path.join(self.folder,self.postpro_file_name))
            textbox.prt((_('\nNo postprocessor file found generated new on at: %s') \
                             %os.path.join(self.folder,self.postpro_file_name)))
            
            lfiles = os.listdir(self.folder)
        
        #Es werden nur Dateien mit der Endung CFG akzeptiert
        self.postprocessor_files=[]
        for lfile in lfiles:
            if os.path.splitext(lfile)[1]=='.cfg':
                self.postprocessor_files.append(lfile)
                
        #Laden der Dateiformate und Texte aus den Config Files
        self.get_output_vars()
        
      
#        textbox.prt((_('\nLoading postprocessor file: %s') \
#                             %os.path.join(self.folder,self.postpro_file_name)))

#        #Variablen erstellen zur späteren Verwendung im Postprozessor        
#        self.get_all_vars()
#        textbox.prt(str(self),1)        

    def make_settings_folder(self): 
        # create settings folder if necessary 
        try: 
            os.mkdir(self.folder) 
        except OSError: 
            pass 

    def get_output_vars(self):
        self.output_format=[]
        self.output_text=[]
        for postprocessor_file in self.postprocessor_files:
            
            self.parser.read(os.path.join(self.folder,postprocessor_file))
            
            self.output_format.append(self.parser.get('General', 'output_format'))
            self.output_text.append(self.parser.get('General','output_text'))

    def get_all_vars(self,pp_file_nr):
        self.parser.read(os.path.join(self.folder,self.postprocessor_files[pp_file_nr]))
        #try:
        self.output_type=self.parser.get('General', 'output_type')  
        self.abs_export=int(self.parser.get('General', 'abs_export'))
        self.cancel_cc_for_depth=int(self.parser.get('General', 'cancel_cc_for_depth'))
        self.export_ccw_arcs_only=int(self.parser.get('General', 'export_ccw_arcs_only')) 
        self.max_arc_radius=int(self.parser.get('General','max_arc_radius'))
        self.gcode_be=self.parser.get('General', 'code_begin')
        self.gcode_en=self.parser.get('General', 'code_end')

        self.pre_dec=int(self.parser.get('Number format','pre_decimals'))
        self.post_dec=int(self.parser.get('Number format','post_decimals'))
        self.dec_sep=self.parser.get('Number format','decimal_seperator')
        self.pre_dec_z_pad=int(self.parser.get('Number format','pre_decimal_zero_padding'))
        self.post_dec_z_pad=int(self.parser.get('Number format','post_decimal_zero_padding'))
        self.signed_val=int(self.parser.get('Number format','signed_values'))

        self.use_line_nrs=int(self.parser.get('Line numbers','use_line_nrs'))
        self.line_nrs_begin=int(self.parser.get('Line numbers','line_nrs_begin'))
        self.line_nrs_step=int(self.parser.get('Line numbers','line_nrs_step'))

        self.tool_ch_str=self.parser.get('Program','tool_change')
        self.feed_ch_str=self.parser.get('Program','feed_change')
        self.rap_pos_plane_str=self.parser.get('Program','rap_pos_plane')
        self.rap_pos_depth_str=self.parser.get('Program','rap_pos_depth')
        self.lin_mov_plane_str=self.parser.get('Program','lin_mov_plane')
        self.lin_mov_depth_str=self.parser.get('Program','lin_mov_depth')
        self.arc_int_cw=self.parser.get('Program','arc_int_cw')
        self.arc_int_ccw=self.parser.get('Program','arc_int_ccw')
        self.cut_comp_off_str=self.parser.get('Program','cutter_comp_off')
        self.cut_comp_left_str=self.parser.get('Program','cutter_comp_left')
        self.cut_comp_right_str=self.parser.get('Program','cutter_comp_right')                        
                        
        self.feed=0
        self.Pe=PointClass( x=self.config.axis1_st_en.get(),
                            y=self.config.axis2_st_en.get())

        self.Pa=PointClass(x=self.config.axis1_st_en.get(),
                            y=self.config.axis2_st_en.get())

        self.lPe=PointClass( x=self.config.axis1_st_en.get(),
                            y=self.config.axis2_st_en.get())
           
        self.IJ=PointClass( x=0.0,y=0.0)    
        self.O=PointClass( x=0.0,y=0.0)    
        self.r=0.0           
        self.a_ang=0.0      
        self.e_ang=0.0         
        self.ze=self.config.axis3_retract.get()   
        self.lz=self.ze
        self.vars={"%feed":'self.iprint(self.feed)',\
                   "%nl":'self.nlprint()',\
                   "%XE":'self.fnprint(self.Pe.x)',\
                   "%-XE":'self.fnprint(-self.Pe.x)',\
                   "%XA":'self.fnprint(self.Pa.x)',\
                   "%-XA":'self.fnprint(-self.Pa.x)',\
                   "%YE":'self.fnprint(self.Pe.y)',\
                   "%-YE":'self.fnprint(-self.Pe.y)',\
                   "%YA":'self.fnprint(self.Pa.y)',\
                   "%-YA":'self.fnprint(-self.Pa.y)',\
                   "%ZE":'self.fnprint(self.ze)',\
                   "%-ZE":'self.fnprint(-self.ze)',\
                   "%I":'self.fnprint(self.IJ.x)',\
                   "%-I":'self.fnprint(-self.IJ.x)',\
                   "%J":'self.fnprint(self.IJ.y)',\
                   "%-J":'self.fnprint(-self.IJ.y)',\
                   "%XO":'self.fnprint(self.O.x)',\
                   "%-XO":'self.fnprint(-self.O.x)',\
                   "%YO":'self.fnprint(self.O.y)',\
                   "%-YO":'self.fnprint(-self.O.y)',\
                   "%R":'self.fnprint(self.r)',\
                   "%AngA":'self.fnprint(degrees(self.a_ang))',\
                   "%-AngA":'self.fnprint(degrees(-self.a_ang))',\
                   "%AngE":'self.fnprint(degrees(self.e_ang))',\
                   "%-AngE":'self.fnprint(degrees(-self.e_ang))'}
#        except:
#            showerror(_("Error during reading postprocessor file"), _("Please delete or correct\n %s")\
#                      %(os.path.join(self.folder,self.postpro_file_name)))
#            raise Exception, _("Problem during import from postprocessor File") 

    def make_new_postpro_file(self):
        self.parser.add_section('General')
        self.parser.set('General', 'output_format', '.ngc')   
        self.parser.set('General', 'output_text', 'G-Code for EMC2')   
        self.parser.set('General', 'output_type', 'g-code')   
        
        self.parser.set('General', 'abs_export', 1)
        self.parser.set('General', 'cancel_cc_for_depth', 0)
        self.parser.set('General', 'export_ccw_arcs_only',0)  
        self.parser.set('General', 'max_arc_radius', 10000)
        self.parser.set('General', 'code_begin',\
                        'G21 (Unit in mm) \nG90 (Absolute distance mode)'\
                        +'\nG64 P0.01 (Exact Path 0.001 tol.)'\
                        +'\nG17'
                        +'\nG40 (Cancel diameter comp.) \nG49 (Cancel length comp.)'\
                        +'\nT1M6 (Tool change to T1)\nM8 (Coolant flood on)'\
                        +'\nS5000M03 (Spindle 5000rpm cw)')
        self.parser.set('General', 'code_end','M9 (Coolant off)\nM5 (Spindle off)\nM2 (Prgram end)')    

        self.parser.add_section('Number format')
        self.parser.set('Number format','pre_decimals',4)
        self.parser.set('Number format','post_decimals',3)
        self.parser.set('Number format','decimal_seperator','.')
        self.parser.set('Number format','pre_decimal_zero_padding',0)
        self.parser.set('Number format','post_decimal_zero_padding',1)
        self.parser.set('Number format','signed_values',0)

        self.parser.add_section('Line numbers')
        self.parser.set('Line numbers','use_line_nrs',0)
        self.parser.set('Line numbers','line_nrs_begin',10)
        self.parser.set('Line numbers','line_nrs_step',10)

        self.parser.add_section('Program')
        self.parser.set('Program','tool_change',\
                        ('T%tool_nr M6%nl S%speed M3%nl'))
        self.parser.set('Program','feed_change',\
                        ('F%feed%nl'))
        self.parser.set('Program','rap_pos_plane',\
                        ('G0 X%XE Y%YE%nl'))
        self.parser.set('Program','rap_pos_depth',\
                        ('G0 Z%ZE %nl'))
        self.parser.set('Program','lin_mov_plane',\
                        ('G1 X%XE Y%YE%nl'))
        self.parser.set('Program','lin_mov_depth',\
                        ('G1 Z%ZE%nl'))
        self.parser.set('Program','arc_int_cw',\
                        ('G2 X%XE Y%YE I%I J%J%nl'))
        self.parser.set('Program','arc_int_ccw',\
                        ('G3 X%XE Y%YE I%I J%J%nl'))
        self.parser.set('Program','cutter_comp_off',\
                        ('G40%nl'))
        self.parser.set('Program','cutter_comp_left',\
                        ('G41%nl'))
        self.parser.set('Program','cutter_comp_right',\
                        ('G42%nl'))                      
                        
        open_file = open(os.path.join(self.folder,self.postpro_file_name), "w") 
        self.parser.write(open_file) 
        open_file.close()

    def write_gcode_be(self,postpro,load_filename):
        #Schreiben in einen String
        if self.output_type=='g-code':
            str="(Generated with: %s, Version: %s, Date: %s)\n" %(self.appname,self.version,self.date)
            str+="(Time: %s)\n" %time.asctime()
            str+="(Created from file: %s)\n" %load_filename
        elif self.output_type=='dxf':
            str=''
            
        self.string=(str.encode("utf-8"))
         
        #Daten aus dem Textfelder an string anhängen
        self.string+=("%s\n" %postpro.gcode_be)




    def write_gcode_en(self,postpro):
        #Daten aus dem Textfelder an string anhängen   
        self.string+=postpro.gcode_en

        self.make_line_numbers()        
        
        return self.string

    def make_line_numbers(self):
        line_format='N%i ' 
        if self.use_line_nrs:
            nr=0
            line_nr=self.line_nrs_begin
            self.string=((line_format+'%s') %(line_nr,self.string))
            nr=self.string.find('\n',nr)
            while not(nr==-1):
                line_nr+=self.line_nrs_step  
                self.string=(('%s'+line_format+'%s') %(self.string[0:nr+1],\
                                          line_nr,\
                                          self.string[nr+1:len(self.string)]))
                
                nr=self.string.find('\n',nr+len(((line_format) %line_nr))+2)
                          
            
            
    def chg_feed_rate(self,feed):
        self.feed=feed
        self.string+=self.make_print_str(self.feed_ch_str) 
        
    def set_cut_cor(self,cut_cor,Pe):
        self.cut_cor=cut_cor

        if not(self.abs_export):
            self.Pe=Pe-self.lPe
            self.lPe=Pe
        else:
            self.Pe=Pe

        if cut_cor==41:
            self.string+=self.make_print_str(self.cut_comp_left_str)
        elif cut_cor==42:
            self.string+=self.make_print_str(self.cut_comp_right_str)

    def deactivate_cut_cor(self,Pe):
        if not(self.abs_export):
            self.Pe=Pe-self.lPe
            self.lPe=Pe
        else:
            self.Pe=Pe   
        self.string+=self.make_print_str(self.cut_comp_off_str)
            
    def lin_pol_arc(self,dir,Pa,Pe,a_ang,e_ang,R,O,IJ):
        self.O=O
        
        self.IJ=IJ
        
        self.a_ang=a_ang
        self.e_ang=e_ang
        
        self.Pa=Pa
        self.r=R
        
        if not(self.abs_export):
            self.Pe=Pe-self.lPe
            self.lPe=Pe
        else:
            self.Pe=Pe

        if dir=='cw':
            self.string+=self.make_print_str(self.arc_int_cw)
        else:
            self.string+=self.make_print_str(self.arc_int_ccw)

          
    def rap_pos_z(self,z_pos):
        if not(self.abs_export):
            self.ze=z_pos-self.lz
            self.lz=z_pos
        else:
            self.ze=z_pos

        self.string+=self.make_print_str(self.rap_pos_depth_str)           
         
    def rap_pos_xy(self,Pe):
        if not(self.abs_export):
            self.Pe=Pe-self.lPe
            self.lPe=Pe
        else:
            self.Pe=Pe

        self.string+=self.make_print_str(self.rap_pos_plane_str)         
    
    def lin_pol_z(self,z_pos):
        if not(self.abs_export):
            self.ze=z_pos-self.lz
            self.lz=z_pos
        else:
            self.ze=z_pos

        self.string+=self.make_print_str(self.lin_mov_depth_str)     
        
    def lin_pol_xy(self,Pa,Pe):
        self.Pa=Pa
        if not(self.abs_export):
            self.Pe=Pe-self.lPe
            self.lPe=Pe
        else:
            self.Pe=Pe

        self.string+=self.make_print_str(self.lin_mov_plane_str)       

    def make_print_str(self,string):
        new_string=string
        for key_nr in range(len(self.vars.keys())):
            new_string=new_string.replace(self.vars.keys()[key_nr],\
                                          eval(self.vars.values()[key_nr]))
        return new_string

    #Funktion welche den Wert als formatierter integer zurueck gibt
    def iprint(self,interger):
        return ('%i' %interger)

    #Funktion gibt den String fuer eine neue Linie zurueck
    def nlprint(self):
        return '\n'

    #Funktion welche die Formatierte Number  zurueck gibt
    def fnprint(self,number):
        string=''
        #+ oder - Zeichen Falls noetig/erwuenscht und Leading 0er
        if (self.signed_val)and(self.pre_dec_z_pad):
            numstr=(('%+0'+str(self.pre_dec+self.post_dec+1)+\
                     '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val==0)and(self.pre_dec_z_pad):
            numstr=(('%0'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val)and(self.pre_dec_z_pad==0):
            numstr=(('%+'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
        elif (self.signed_val==0)and(self.pre_dec_z_pad==0):
            numstr=(('%'+str(self.pre_dec+self.post_dec+1)+\
                    '.'+str(self.post_dec)+'f') %number)
            
        #Setzen des zugehoerigen Dezimal Trennzeichens            
        string+=numstr[0:-(self.post_dec+1)]
        
        string_end=self.dec_sep
        string_end+=numstr[-(self.post_dec):]

        #Falls die 0er am Ende entfernt werden sollen
        if self.post_dec_z_pad==0:
            while (len(string_end)>0)and((string_end[-1]=='0')or(string_end[-1]==self.dec_sep)):
                string_end=string_end[0:-1]                
        return string+string_end
    
    def __str__(self):

        str=''
        for section in self.parser.sections(): 
            str= str +"\nSection: "+section 
            for option in self.parser.options(section): 
                str= str+ "\n   -> %s=%s" % (option, self.parser.get(section, option))
        return str

