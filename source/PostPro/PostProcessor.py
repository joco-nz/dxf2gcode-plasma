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

import os

import Core.constants as c
import Core.Globals as g
#from d2gexceptions import *

import logging
logger = logging.getLogger("PostPro.PostProcessor") 

from PostPro.PostProcessorConfig import MyPostProConfig


class MyPostProcessor:
    def __init__(self):

        #Get the List of all PostProcessor Config Files in the Postprocessor
        # Config Directory
           
        try:
            lfiles = os.listdir(os.path.join(g.folder, c.DEFAULT_POSTPRO_DIR))
        except:
    
            #If no Postprocessor File was found on folder create one
            logger.debug("created default varspace")
            PostProConfig=MyPostProConfig()
            PostProConfig.create_default_config()
            PostProConfig.default_config = True

            
            lfiles = os.listdir(PostProConfig.folder)
            
        #Only files with the ending *.cfg will be accepted.
        self.postprocessor_files = []
        for lfile in lfiles:
            if os.path.splitext(lfile)[1] == '.cfg':
                self.postprocessor_files.append(lfile)
                
        #Laden der Dateiformate und Texte aus den Config Files
        self.get_output_vars()
        
      
    def get_output_vars(self):
        self.output_format = []
        self.output_text = []
        for postprocessor_file in self.postprocessor_files:
            
            PostProConfig=MyPostProConfig(filename=postprocessor_file)
            PostProConfig.load_config()
            
            self.output_format.append(PostProConfig.vars.General['output_format'])
            self.output_text.append(PostProConfig.vars.General['output_text'])

#    def write_gcode_be(self, postpro, load_filename):
#        #Schreiben in einen String
#        if self.output_type == 'g-code':
#            str = "(Generated with: %s, Version: %s, Date: %s)\n" % (self.appname, self.version, self.date)
#            str += "(Time: %s)\n" % time.asctime()
#            str += "(Created from file: %s)\n" % load_filename
#        elif self.output_type == 'dxf':
#            str = ''
#            
#        self.string = (str.encode("utf-8"))
#         
#        #Daten aus dem Textfelder an string anh�ngen
#        self.string += ("%s\n" % postpro.gcode_be)
#
#    def write_gcode_en(self, postpro):
#        #Daten aus dem Textfelder an string anh�ngen   
#        self.string += postpro.gcode_en
#
#        self.make_line_numbers()        
#        
#        return self.string
#
#    def make_line_numbers(self):
#        line_format = 'N%i ' 
#        if self.use_line_nrs:
#            nr = 0
#            line_nr = self.line_nrs_begin
#            self.string = ((line_format + '%s') % (line_nr, self.string))
#            nr = self.string.find('\n', nr)
#            while not(nr == -1):
#                line_nr += self.line_nrs_step  
#                self.string = (('%s' + line_format + '%s') % (self.string[0:nr + 1], \
#                                          line_nr, \
#                                          self.string[nr + 1:len(self.string)]))
#                
#                nr = self.string.find('\n', nr + len(((line_format) % line_nr)) + 2)
#                          
#            
#            
#    def chg_feed_rate(self, feed):
#        self.feed = feed
#        self.string += self.make_print_str(self.feed_ch_str) 
#        
#    def set_cut_cor(self, cut_cor, Pe):
#        self.cut_cor = cut_cor
#
#        if not(self.abs_export):
#            self.Pe = Pe - self.lPe
#            self.lPe = Pe
#        else:
#            self.Pe = Pe
#
#        if cut_cor == 41:
#            self.string += self.make_print_str(self.cut_comp_left_str)
#        elif cut_cor == 42:
#            self.string += self.make_print_str(self.cut_comp_right_str)
#
#    def deactivate_cut_cor(self, Pe):
#        if not(self.abs_export):
#            self.Pe = Pe - self.lPe
#            self.lPe = Pe
#        else:
#            self.Pe = Pe   
#        self.string += self.make_print_str(self.cut_comp_off_str)
#            
#    def lin_pol_arc(self, dir, Pa, Pe, a_ang, e_ang, R, O, IJ):
#        self.O = O
#        
#        self.IJ = IJ
#        
#        self.a_ang = a_ang
#        self.e_ang = e_ang
#        
#        self.Pa = Pa
#        self.r = R
#        
#        if not(self.abs_export):
#            self.Pe = Pe - self.lPe
#            self.lPe = Pe
#        else:
#            self.Pe = Pe
#
#        if dir == 'cw':
#            self.string += self.make_print_str(self.arc_int_cw)
#        else:
#            self.string += self.make_print_str(self.arc_int_ccw)
#
#          
#    def rap_pos_z(self, z_pos):
#        if not(self.abs_export):
#            self.ze = z_pos - self.lz
#            self.lz = z_pos
#        else:
#            self.ze = z_pos
#
#        self.string += self.make_print_str(self.rap_pos_depth_str)           
#         
#    def rap_pos_xy(self, Pe):
#        if not(self.abs_export):
#            self.Pe = Pe - self.lPe
#            self.lPe = Pe
#        else:
#            self.Pe = Pe
#
#        self.string += self.make_print_str(self.rap_pos_plane_str)         
#    
#    def lin_pol_z(self, z_pos):
#        if not(self.abs_export):
#            self.ze = z_pos - self.lz
#            self.lz = z_pos
#        else:
#            self.ze = z_pos
#
#        self.string += self.make_print_str(self.lin_mov_depth_str)     
#        
#    def lin_pol_xy(self, Pa, Pe):
#        self.Pa = Pa
#        if not(self.abs_export):
#            self.Pe = Pe - self.lPe
#            self.lPe = Pe
#        else:
#            self.Pe = Pe
#
#        self.string += self.make_print_str(self.lin_mov_plane_str)       
#
#    def make_print_str(self, string):
#        new_string = string
#        for key_nr in range(len(self.vars.keys())):
#            new_string = new_string.replace(self.vars.keys()[key_nr], \
#                                          eval(self.vars.values()[key_nr]))
#        return new_string
#
#    #Funktion welche den Wert als formatierter integer zurueck gibt
#    def iprint(self, interger):
#        return ('%i' % interger)
#
#    #Funktion gibt den String fuer eine neue Linie zurueck
#    def nlprint(self):
#        return '\n'
#
#    #Funktion welche die Formatierte Number  zurueck gibt
#    def fnprint(self, number):
#        string = ''
#        #+ oder - Zeichen Falls noetig/erwuenscht und Leading 0er
#        if (self.signed_val)and(self.pre_dec_z_pad):
#            numstr = (('%+0' + str(self.pre_dec + self.post_dec + 1) + \
#                     '.' + str(self.post_dec) + 'f') % number)
#        elif (self.signed_val == 0)and(self.pre_dec_z_pad):
#            numstr = (('%0' + str(self.pre_dec + self.post_dec + 1) + \
#                    '.' + str(self.post_dec) + 'f') % number)
#        elif (self.signed_val)and(self.pre_dec_z_pad == 0):
#            numstr = (('%+' + str(self.pre_dec + self.post_dec + 1) + \
#                    '.' + str(self.post_dec) + 'f') % number)
#        elif (self.signed_val == 0)and(self.pre_dec_z_pad == 0):
#            numstr = (('%' + str(self.pre_dec + self.post_dec + 1) + \
#                    '.' + str(self.post_dec) + 'f') % number)
#            
#        #Setzen des zugehoerigen Dezimal Trennzeichens            
#        string += numstr[0:-(self.post_dec + 1)]
#        
#        string_end = self.dec_sep
#        string_end += numstr[-(self.post_dec):]
#
#        #Falls die 0er am Ende entfernt werden sollen
#        if self.post_dec_z_pad == 0:
#            while (len(string_end) > 0)and((string_end[-1] == '0')or(string_end[-1] == self.dec_sep)):
#                string_end = string_end[0:-1]                
#        return string + string_end
#    
#    def __str__(self):
#
#        str = ''
#        for section in self.parser.sections(): 
#            str = str + "\nSection: " + section 
#            for option in self.parser.options(section): 
#                str = str + "\n   -> %s=%s" % (option, self.parser.get(section, option))
#        return str

