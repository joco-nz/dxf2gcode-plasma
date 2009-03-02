import wx
 
BORDER=5

class VarDlg(wx.Dialog):
 
    def __init__(self, parent, id, title,Caption, String):
        wx.Dialog.__init__(self, parent, id, title)
        
        print Caption
        print String
        #if not(len(Caption)==len(String)):
        #    raise Exception, "Number of labels different to number of values"
        
        self.label=[]
        self.inputTxt=[]
        
        # Add a panel so it looks correct on all platforms
        self.panel = wx.Panel(self, wx.ID_ANY) 
        self.Sbox=wx.StaticBox(self.panel, wx.ID_ANY,'',(BORDER,BORDER))
        
        topSizer        = wx.BoxSizer(wx.VERTICAL)
        sboxSizer       = wx.StaticBoxSizer(self.Sbox, wx.VERTICAL)
        gridSizer       = wx.FlexGridSizer(rows=len(Caption), cols=2, hgap=BORDER, vgap=BORDER)
        btnSizer        = wx.BoxSizer(wx.HORIZONTAL)

        for i in range(len(Caption)):
            self.label.append(wx.StaticText(self.panel, wx.ID_ANY, Caption[i],size=(-1,-1)))
            self.inputTxt.append(wx.TextCtrl(self.panel, wx.ID_ANY, String[i],size=(60,-1)))
            
            gridSizer.Add(self.label[-1], 0, wx.EXPAND)
            gridSizer.Add(self.inputTxt[-1], 0, wx.EXPAND|wx.ALIGN_LEFT)
        
        
        okBtn = wx.Button(self.panel, wx.ID_OK)
        cancelBtn = wx.Button(self.panel, wx.ID_CANCEL)

        btnSizer.Add(okBtn, 0, wx.ALL, BORDER)
        btnSizer.Add(cancelBtn, 0, wx.ALL, BORDER)
 

        sboxSizer.Add(gridSizer, 0, wx.ALL|wx.EXPAND, BORDER)
     
        topSizer.Add(sboxSizer,0, wx.ALL|wx.CENTER,BORDER)
        topSizer.Add(btnSizer, 0, wx.ALL|wx.CENTER, BORDER)
 
        self.panel.SetSizer(topSizer)
        topSizer.Fit(self)
 
    def GetValue(self):
        value=[]
        for inputTxt in self.inputTxt:
            value.append(inputTxt.GetValue())
        return value


 
# Run the program
if __name__ == '__main__':
    app = wx.PySimpleApp()
    chform = VarDlg(None, -1, 'Eingabefeld',('Input 1 sd fas','Input 2'),('323.234','233.2'))
    chform.ShowModal()
    if chform.ReturnCode==wx.ID_CANCEL:
        print "Cancel"
    elif chform.ReturnCode==wx.ID_OK:
        print "OK"
        print chform.GetValue()
        
    chform.Destroy()
    app.MainLoop()