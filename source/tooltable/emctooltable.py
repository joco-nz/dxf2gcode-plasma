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
"""
@newfield purpose: Purpose

@purpose:  Read EMC tool table of various shapes and forms

The following formats are handled:

"tlo_all_axes" G-code style format by Michael Gieskewiecz
mill and lathe formats as per current (2.4) developer version
mill and lathe formats post-Cradek patch bb0e922fef39923ed540c0fcaaea338d3ade061d
a fairly old Nist mill format

@author: Michael Haberler 
@since:  08.01.2010
@license: GPL
"""

import re
import os
from ConfigParser import ConfigParser


class EmcTool(object):
    """
    an EMC tool table entry
    
    attributes may be accessed either as self.values[<code>] as per 
    tlo_all_axes or as attributes (read-only):
     
    self.tool_number
    self.fms
    self.pocket
    self.diameter
    self.offset_{x,y,z,a,,b,c,u,v,w}
    self.frontangle
    self.backangle
    self.orientation
    """
    
    tt_codes = 'TPDXYZABCUVWIJQF'
    tt_types = 'IIFFFFFFFFFFFFII'
    intfmt = "%d"
    floatfmt = "%+4.4f"

    def __init__(self,typus=None):
        self.values = dict()
        self.comment = None
        self.typus = typus

    def typeof(self,letter):
        return  EmcTool.tt_types[EmcTool.tt_codes.index(letter)]
 
    @property
    def tool_number(self):
        return self.values['T']
        
    @property
    def pocket(self):
        return self.values['P']

    @property
    def fms(self):
        return self.values['F']
        
    @property
    def diameter(self):
        return self.values['D']
    
    @property
    def offset_x(self):
        return self.values['X']
    
    @property
    def offset_y(self):
        return self.values['Y']
    
    @property
    def offset_z(self):
        return self.values['Z']
    
    @property
    def offset_a(self):
        return self.values['A']
    
    @property
    def offset_b(self):
        return self.values['B']
    
    @property
    def offset_c(self):
        return self.values['C']
    
    @property
    def offset_u(self):
        return self.values['U']
    
    @property
    def offset_v(self):
        return self.values['V']
    
    @property
    def offset_w(self):
        return self.values['W']
    
    @property
    def frontangle(self):
        return self.values['I']
    
    @property
    def backangle(self):
        return self.values['J']
    
    @property
    def orientation(self):
        return self.values['Q']
    
   
    def __str__(self):
        """ 
        return the tooltable entry in tlo_all_axes format,
        ignoring the FMS field
        """
        s = ""
        for k in self.tt_codes:
            # skip FMS field
            if k == 'F':
                continue
            if self.values.has_key(k):
                if self.typeof(k) == 'I':
                    s += k + EmcTool.intfmt % (self.values[k]) + " "
                if self.typeof(k) == 'F':
                    s += k + EmcTool.floatfmt % (self.values[k]) + " "
        if self.comment:
            s += "; " + self.comment
        return s
    
class EmcToolTable(object):
    
    def __init__(self,filename=None, emc_inifile=None,linear_units='mm',angular_units='degrees'):
        """
        read and parse an EMC tool table.
        
        If given a filename, read that. 
        
        If passed an EMC INI file, obtain the TOOL_TABLE variable from 
        the EMCIO section and use that, prepending the inifile directory
        if the tool table filename is relative. In this case, also 
        remember the linear_units entry from section TRAJ, variables 
        LINEAR_UNITS and ANGULAR_UNITS.
        
        Iterators:
            table_entries
            mill_table_entries
            lathe_table_entries
        
        """
        self.entries = []
        self.typus = None
        self.number = re.compile('([-+]?(\d+(\.\d*)?|\.\d+))')  # G-Code number
        self.linear_units = linear_units
        self.angular_units = angular_units
        
        if emc_inifile:
            config = ConfigParser()
            config.read([emc_inifile])
            self.filename = config.get('EMCIO', 'TOOL_TABLE')
            self.linear_units = config.get('TRAJ','LINEAR_UNITS')
            self.angular_units = config.get('TRAJ','ANGULAR_UNITS')
            if not os.path.isabs(self.filename):
                self.filename = os.path.join(os.path.dirname(emc_inifile),self.filename)
        else:
            self.filename = filename

        fp = open(self.filename)
        lno = 0        
        for line in fp.readlines():
            lno += 1
            if not line.startswith(';'):   
                if line.strip():
                    entry = self._parseline(lno,line.strip())
                    if entry:
                        self.entries.append(entry)

    
    def _parseline(self,lineno,line):
        """
        read a tooltable line
        if an entry was parsed successfully, return a  EmcTool() instance
        """     
        comment = None
        re.IGNORECASE = True
        
        # old Nist mill format
        # http://www.isd.mel.nist.gov/personnel/kramer/pubs/RS274NGC_3.web/RS274NGC_32a.html
        if re.match('\A\s*(POC|POCKET)\s+(FMS)\s+(TLO)\s+(DIAMETER)\s+COMMENT\s*\Z',line,re.I):
            self.typus = 'mill-nist'
            return None

        # as per current developer version manual
        if re.match('\A\s*(POC|POCKET)\s+FMS\s+(TLO|LEN)\s+(DIAM|DIAMETER)\s+COMMENT\s*\Z',
                    line,re.I):
            self.typus = 'mill-dev'
            return None

        # as per current developer version manual
        if re.match('\A\s*(POC|POCKET)\s+FMS\s+ZOFFSET\s+XOFFSET\s+DIAMETER\s+FRONTANGLE\s+BACKANGLE\s+ORIENT\s+COMMENT\s*\Z',
                    line,re.I):
            self.typus = 'lathe-dev'
            return None

        # as per http://timeguy.com/cradek-files/emc/0001-preserve-fms-values-for-nonrandom-tc-and-more.patch
        if re.match('\A\s*TOOLNO\s+POCKET\s+LENGTH\s+DIAMETER\s+COMMENT\s*\Z',
                    line,re.I):
            self.typus = 'mill-cradek'
            return None

        # http://timeguy.com/cradek-files/emc/0001-preserve-fms-values-for-nonrandom-tc-and-more.patch
        if re.match('\A\s*TOOLNO\s+POCKET\s+ZOFFSET\s+XOFFSET\s+DIAMETER\s+FRONTANGLE\s+BACKANGLE\s+ORIENT\s+COMMENT\s*\Z',
                    line,re.I):
            self.typus = 'lathe-cradek'
            return None

        # MichaelG tlo_all_axes format
        if re.match('\A\s*T\d+',line,re.I):
            semi = line.find(";")
            if semi:
                comment = line[semi+1:]
            entry = line.split(';')[0]
            tt = EmcTool()
            for field in entry.split():    
                result = re.search('(?P<opcode>[a-zA-Z])(?P<value>[+-]?\d*\.?\d*)',field)
                if result:
                    self._assign(tt, result.group('opcode').capitalize(), result.group('value'))
                else:
                    print "%s:%d  bad line: '%s' " % (self.filename, lineno, entry)
                    
                if tt.values.has_key('I') and tt.values.has_key('J'):   # has frontangle and backangle
                    tt.typus = "lathe-mg"
                else:
                    tt.typus = "mill-mg"            
            tt.comment = comment
            return tt

        if self.typus == 'mill-nist':
            tt = EmcTool(typus=self.typus)
            for n,m in enumerate(re.finditer(self.number, line)):
                self._assign(tt, 'PFZD'[n], m.group(0))
                if n == 3:
                    # set tool number == pocket (?)
                    self._assign(tt, 'T', tt.values['P'])
                    tt.comment = line[m.end():].lstrip()
                    return tt
            return None
        
        if self.typus == 'mill-dev':
            tt = EmcTool(typus=self.typus)
            for n,m in enumerate(re.finditer(self.number, line)):
                self._assign(tt, 'PFZD'[n], m.group(0))
                if n == 3:
                    tt.comment = line[m.end():].lstrip()
                    # set tool number == pocket (?)
                    self._assign(tt, 'T', tt.values['P'])
                    return tt
            return None

        if self.typus == 'mill-cradek':
            tt = EmcTool(typus=self.typus)
            for n,m in enumerate(re.finditer(self.number, line)):
                self._assign(tt, 'TPZD'[n], m.group(0))
                if n == 3:
                    tt.comment = line[m.end():].lstrip()
                    tt.values['F'] = tt.tool_number         # fake FMS
                    return tt
            return None
        
        
        if self.typus == 'lathe-dev':
            tt = EmcTool(typus=self.typus)
            for n,m in enumerate(re.finditer(self.number, line)):
                self._assign(tt, 'PFZXDIJQ'[n], m.group(0))
                if n == 7:
                    tt.comment = line[m.end():].lstrip()
                    # fake tool number from pocket
                    tt.values['T'] = tt.values['P'] 
                    return tt
        
        if self.typus == 'lathe-cradek':
            tt = EmcTool(typus=self.typus)
            for n,m in enumerate(re.finditer(self.number, line)):
                self._assign(tt, 'TPZXDIJQ'[n], m.group(0))
                if n == 7:
                    tt.comment = line[m.end():].lstrip()
                    # fake FMS field
                    tt.values['F'] = tt.tool_number         
                    return tt
                                
        print "%s:%d: unrecognized tool table entry   '%s'" % (self.filename,lineno,line)

    def _assign(self,tt_entry,opcode,value):
        
        if tt_entry.typeof(opcode) == 'I':
            tt_entry.values[opcode] = int(value)
            
        if tt_entry.typeof(opcode) == 'F':
            tt_entry.values[opcode] = float(value)        

    def table_entries(self):
        for e in self.entries:
            yield e
    
    def lathe_entries(self):
        for e  in [x for x in self.entries if x.typus == 'lathe']:
            yield e
    
    def mill_entries(self):
        for e  in [x for x in self.entries if x.typus == 'mill']:
            yield e  
            
            
    def toolbynumber(self,number):
        for t in self.entries:
            if t.tool_number == number:
                return t
        raise ValueError,"no tool %d" % (number)
              
    def toolbypocket(self,pocket):
        for t in self.entries:
            if t.pocket == pocket:
                return t
        raise ValueError,"no tool in pocket %d" % (pocket)
              
                         
if __name__ == '__main__':
    import sys
    import glob
    
    if len(sys.argv) > 1:
        tool_table = EmcToolTable(filename=sys.argv[1])
    else:
        for fn in glob.glob("tables/*.tbl"):
            print "reading " ,fn,":"
            tool_table = EmcToolTable(filename=fn)
            for tool in tool_table.table_entries():
                print "format: ",tool.typus,"  ",tool

    # reading via EMC ini file
    ini_file = 'emc.ini'
    tool_table = EmcToolTable(emc_inifile=ini_file)
    print "read %s through %s" % (tool_table.filename, ini_file)
    print "linear units: ",tool_table.linear_units
    print "angular units: ",tool_table.angular_units
    for tool in tool_table.table_entries():
        print "format: ",tool.typus,"  ",tool
        
#    print "all entries:"
#
#
#    print "mill entries:"
#    for tool in tool_table.mill_entries():
#        print tool    
#             
#    print "lathe tool angles:"
#    for tool in tool_table.lathe_entries():
#        print tool.frontangle,tool.backangle
#       
#    print "tool 3 diameter = ", tool_table.toolbynumber(3).diameter
#    
#    print "pocket 2 tool diameter = ", tool_table.toolbypocket(2).diameter
