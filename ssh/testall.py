'''

integration test setup
    GlobalConfig+Logger
    PluginLoader
    Varspace
    various plugins
    a primitve window setup without working canvas

    
Created on 13.12.2009

@author: mah
'''

from Tkinter import *
import pprint 


from notebook import *
from globalconfig import *
from pluginloader import PluginLoader
from simplecallback import SimpleCallback

import globals as g
import constants as c

from logger import Log

platform = 'mac'




#
class CanvasClass:
    def __init__(self, master = None,text=None):
        
        self.master=master
        self.Content=[]

        #Erstellen der Standardwerte
        self.lastevent=[]
        self.sel_rect_hdl=[]
        self.dir_var = IntVar()
        self.dx=0.0
        self.dy=0.0
        self.scale=1.0

        #Wird momentan nicht benoetigt, eventuell fuer Beschreibung von Aktionen im Textfeld #self.text=text

        #Erstellen des Labels am Unteren Rand fuer Status Leiste        
        self.label=Label(self.master, text="Curser Coordinates: X=0.0, Y=0.0, Scale: 1.00",bg="white",anchor="w")
        self.label.grid(row=1,column=0,sticky=E+W)

        #Canvas Erstellen und Fenster ausfuellen        
        self.canvas=Canvas(self.master,width=650,height=500, bg = "white")
        self.canvas.grid(row=0,column=0,sticky=N+E+S+W)
        self.master.columnconfigure(0,weight=1)
        self.master.rowconfigure(0,weight=1)


        #Binding fuer die Bewegung des Mousezeigers
        self.canvas.bind("<Motion>", self.moving)

        #Bindings fuer Selektieren
        self.canvas.bind("<Button-1>", self.select_cont)
        
        #Eventuell mit Abfrage probieren???????????????????????????????????????????
        self.canvas.bind("<Shift-Button-1>", self.multiselect_cont)
        self.canvas.bind("<B1-Motion>", self.select_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.select_release)

        #Binding fuer Contextmenu
 #FIXME       self.canvas.bind("<Button-3>", self.make_contextmenu)
#
#        #Bindings fuer Zoom und Bewegen des Bilds        
#        self.canvas.bind("<Control-Button-1>", self.mouse_move)
#        self.canvas.bind("<Control-B1-Motion>", self.mouse_move_motion)
#        self.canvas.bind("<Control-ButtonRelease-1>", self.mouse_move_release)
#        
#        self.canvas.bind("<Control-Button-3>", self.mouse_zoom)
#        self.canvas.bind("<Control-B3-Motion>", self.mouse_zoom_motion)
#        self.canvas.bind("<Control-ButtonRelease-3>", self.mouse_zoom_release)  
#        if True: # platform in ("mac"):
#            # for macs with three button mice  Button-3  actually is reported as Button-2
#            self.canvas.bind("<Button-2>", self.make_contextmenu)
#            # and if that isnt available, the following does the trick (one-eyed mice)
#            self.canvas.bind("<Option-Button-1>", self.make_contextmenu)
#            self.canvas.bind("<Command-ButtonRelease-1>", self.mouse_zoom_release)   
#            self.canvas.bind("<Command-Button-1>", self.mouse_zoom)
#            self.canvas.bind("<Command-B1-Motion>", self.mouse_zoom_motion)          

    #Callback fuer das Bewegen der Mouse mit Darstellung in untere Leiste
    def moving(self,event):
        x=self.dx+(event.x/self.scale)
        y=self.dy+(self.canvas.winfo_height()-event.y)/self.scale

        if self.scale<1:
            self.label['text']=(_("Curser Coordinates: X= %5.0f Y= %5.0f , Scale: %5.3f") \
                                %(x,y,self.scale))
            
        elif (self.scale>=1)and(self.scale<10):      
            self.label['text']=(_("Curser Coordinates: X= %5.1f Y= %5.1f , Scale: %5.2f") \
                                %(x,y,self.scale))
        elif self.scale>=10:      
            self.label['text']=(_("Curser Coordinates: X= %5.2f Y= %5.2f , Scale: %5.1f") \
                                %(x,y,self.scale))
        
    def select_cont(self,event):
        self.schliesse_contextmenu()
        
        self.moving(event)
        self.Content.deselect()
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def multiselect_cont(self,event):
        self.schliesse_contextmenu()
        
        self.sel_rect_hdl=Rectangle(self.canvas,event.x,event.y,event.x,event.y,outline="grey") 
        self.lastevent=event

    def select_rectangle(self,event):
        self.moving(event)
        self.canvas.coords(self.sel_rect_hdl,self.lastevent.x,self.lastevent.y,\
                           event.x,event.y)

    def select_release(self,event):
        self.master.textbox.prt("Release %s %s" %(event.x,event.y))
#        dx=self.lastevent.x-event.x
#        dy=self.lastevent.y-event.y
#        self.canvas.delete(self.sel_rect_hdl)
        
        #self.Content.delete_opt_path()   
        
        #Wenn mehr als 6 Pixel gezogen wurde Enclosed        
        if (abs(dx)+abs(dy))>6:
            items=self.canvas.find_overlapping(event.x,event.y,event.x+dx,event.y+dy)
            mode='multi'
        else:
            #items=self.canvas.find_closest(event.x, event.y)
            items=self.canvas.find_overlapping(event.x-3,event.y-3,event.x+3,event.y+3)
            mode='single'
            
        self.Content.addselection(items,mode)


class LogText(Text):
    def write(self,charstr):
        "write text to  window"
        self.insert(END,charstr)
        self.yview(END)
        
    def flush(self):
        pass
        
class TextboxClass:
    def __init__(self,frame=None,master=None,DEBUG=0):
            
        self.DEBUG=DEBUG
        self.master=master
        self.text = LogText(frame,height=7)
        
        self.textscr = Scrollbar(frame)
        self.text.grid(row=0,column=0,pady=4,sticky=E+W)
        self.textscr.grid(row=0,column=1,pady=4,sticky=N+S)
        frame.columnconfigure(0,weight=1)
        frame.columnconfigure(1,weight=0)

        
        #Binding fuer Contextmenu
        self.text.bind("<Button-3>", self.text_contextmenu)
        # Mac OS x has right mouse button mapped to  Button-2
        if platform in ("mac"):
            self.text.bind("<Button-2>", self.text_contextmenu)
            # for single-button macs..
            self.text.bind("<Option-Button-1>", self.text_contextmenu)

        #Anfangstext einfuegen
        self.textscr.config(command=self.text.yview)
        self.text.config(yscrollcommand=self.textscr.set)

    
    def set_debuglevel(self,DEBUG=0):
        self.DEBUG=DEBUG
        if DEBUG:
            self.text.config(height=15)

    def prt(self,txt='',DEBUGLEVEL=0):

        if self.DEBUG>=DEBUGLEVEL:
            self.text.insert(END,txt)
            self.text.yview(END)
#            self.master.update_idletasks()
            

    #Contextmenu Text mit Bindings beim Rechtsklick
    def text_contextmenu(self,event):

        #Contextmenu erstellen zu der Geometrie        
        popup = Menu(self.text,tearoff=0)        
        popup.add_command(label='Delete text entries',command=self.text_delete_entries)
        popup.post(event.x_root, event.y_root)
        
    def text_delete_entries(self):
        self.text.delete(2.0,END) #7.0,END)
        self.text.yview(END)           
        
        

class Windoof:
    def __init__(self,master):
        
        self.pp = pprint.PrettyPrinter(indent=4)
        self.counter = 0
        self.entries = ['good','bad','ugly']
        self.apply_menu = None
        self.create_menu = None
        self.instances = []
        
        self.master = master
#        self.pluginloader = None
        
        # param
        self.frame_l=Frame(master) 
        self.frame_l.grid(row=0,column=0,rowspan=2,padx=4,pady=4,sticky=N+E+W)
    #        add_param_nb(self.frame_l)
        #self.nbook = NotebookClass(self.frame_l,TOP)
        self.nbook = NotebookClass(self.frame_l,height=200,width=240)

        #Erstellen des Canvas Rahmens
        self.frame_c=Frame(master,relief = RIDGE,bd = 2)
        self.frame_c.grid(row=0,column=1,padx=4,pady=4,sticky=N+E+S+W)
        
        #Unterer Rahmen erstellen mit der Lisbox + Scrollbar zur Darstellung der Ereignisse.
        self.frame_u=Frame(master) 
        self.frame_u.grid(row=1,column=1,padx=4,sticky=N+E+W+S)
        #Erstellen des Statusfenster
        self.textbox=TextboxClass(frame=self.frame_u,master=self.master)

        #Voreininstellungen fuer das Programm laden
        # self.config=ConfigClass(self.textbox,FOLDER,APPNAME)

        #PostprocessorClass initialisieren (Voreinstellungen aus Config)
        #self.postpro=PostprocessorClass(self.config,self.textbox,FOLDER,APPNAME,VERSION,DATE)

        self.master.columnconfigure(0,weight=0)
        self.master.columnconfigure(1,weight=1)
        self.master.rowconfigure(0,weight=1)
        self.master.rowconfigure(1,weight=0)
        
        #self.ExportParas =ExportParasClass(self.frame_l,self.config,self.postpro)
        self.Canvas =CanvasClass(self.frame_c,self)
        
        self.menu = Menu(self.master,tearoff=0)
        self.master.config(menu=self.menu)


#        list_menu = Menu(self.menu,tearoff=0) 
#        list_menu.add_command(label="show instances",command=SimpleCallback(self.dump,1))
#        self.menu.add_cascade(label="Dump", menu=list_menu)
    
        self.create_menu = Menu(self.menu,tearoff=0) 
        self.menu.add_cascade(label="Defaults",menu=self.create_menu)    

        self.apply_menu = Menu(self.menu,tearoff=0) 
        self.menu.add_cascade(label="Instance",menu=self.apply_menu)    
        
#        print "dump index ",self.menu.index("Dump")
#        print "create index ",self.menu.index("Create")
#        print "apply index ",self.menu.index("Apply")



    def apply_close(self,inst):
        p = g.plugins[inst]
        p.close_instance(inst)
        self.rebuild_apply_menu()
        

    def apply_delete(self,inst):
        p = g.plugins[inst]
        p.delete_instance(inst)
        self.rebuild_apply_menu()
        

    def add_instance(self,tag):
        p = g.plugins[tag]
        if p.clone_instance():
            self.rebuild_apply_menu()
    
    def save_all(self):
        # caveat - instance name changes are done as well - migth fail
        for tag,plugin in g.plugins.items():
            plugin.save_callback() # save_varspace()

    def toggle_vis(self,inst):
        if inst.hidden:
            self.nbook.display(inst.param_frame)
        else:
            self.nbook.hide(inst.param_frame)
        inst.hidden = not inst.hidden
        self.rebuild_create_menu()
 
    def hide_defaults(self):
        for k,v in g.plugins.items():
            if  v.is_default and not v.hidden:
                self.toggle_vis(v)
        self.rebuild_create_menu()
    
    def show_defaults(self):
        for k,v in g.plugins.items():
            if  v.is_default and v.hidden:
                self.toggle_vis(v)
        self.rebuild_create_menu()



    def rebuild_create_menu(self):#,pluginloader=None):

        if self.create_menu:
            self.create_menu.destroy()
        self.create_menu = Menu(self.menu,tearoff=0)
        
        for k,v in g.plugins.items():
            if  v.is_default and v.CLONABLE:
                sm= Menu(self.create_menu,tearoff=0)
                sm.add_command(label = "Clone '%s'" %(k),command=lambda p=k:self.add_instance(p))    #SimpleCallback(self.add_instance,k))

#                if v.hidden:
#                    sm.add_command(label = "Show '%s'" %(k),command=lambda i=v:self.toggle_vis(i))
#                else:
#                    sm.add_command(label = "Hide '%s'" %(k),command=lambda i=v:self.toggle_vis(i)) 
                self.create_menu.add_cascade(label=k,menu=sm)
                
        self.create_menu.add_separator()

        for k,v in g.plugins.items():
            if  v.is_default and not v.CLONABLE:
                sm= Menu(self.create_menu,tearoff=0)
#                if v.CLONABLE:
#                    sm.add_command(label = "Clone '%s'" %(k),command=lambda p=k:self.add_instance(p))    #SimpleCallback(self.add_instance,k))

                if v.hidden:
                    sm.add_command(label = "Show '%s'" %(k),command=lambda i=v:self.toggle_vis(i))
                else:
                    sm.add_command(label = "Hide '%s'" %(k),command=lambda i=v:self.toggle_vis(i)) 
                self.create_menu.add_cascade(label=k,menu=sm)
                
        self.create_menu.add_separator()
        self.create_menu.add_command(label="Show defaults",command=lambda:self.show_defaults())
        self.create_menu.add_command(label="Hide defaults",command=lambda:self.hide_defaults())
                
        
        self.menu.entryconfigure(self.menu.index("Defaults"), menu=self.create_menu)
        
#    def handler(self,plugin,method):
#        print "apply %s p %s" %(method,plugin)
#        print "dict" , plugin.__dict__
#        self.pp.pprint(plugin)   
#
#        
#        #plugin.__dict__[method](None)
        
    def rebuild_apply_menu(self):
        if self.apply_menu:
            self.apply_menu.destroy()
        self.apply_menu = Menu(self.menu,tearoff=0)
        self.apply_menu.add_command(label="Save all",command=lambda:self.save_all())
        self.apply_menu.add_separator()

        for k,v in g.plugins.items():
            if not v.is_default:
                sm= Menu(self.apply_menu,tearoff=0)
                if hasattr(v,c.METHOD_DICT):
                    for ssh,descr in v.shapeset_handlers.items():  
#                        for n,x in descr.items():
#                            print "%s = %s" % (n,x)
                        sm.add_command(label = descr['menu_entry'],command=SimpleCallback(descr['method'],ssh))# lambda i=v,p=ssh:i.p(p))
#                if hasattr(v,'transform'):
#                    sm.add_command(label = "transform shape with %s" %(k),command=lambda i=v,p=k:i.transform(p))     
                sm.add_separator()
                sm.add_command(label = "Close '%s'" %(k),command=lambda p=k:self.apply_close(p))
                sm.add_command(label = "Delete '%s'" %(k),command=lambda p=k:self.apply_delete(p))
                self.apply_menu.add_cascade(label=k,menu=sm)
        self.menu.entryconfigure(self.menu.index("Instance"), menu=self.apply_menu)
    
    def dump(self,arg):
        print "plugin instances:"
        self.pp.pprint(g.plugins)   

    def finalize(self,p):
        self.rebuild_create_menu() # add module names to Create menu
        self.rebuild_apply_menu() # add instances  to Apply menu
    
             
def setup_logging(window):
    # LogText window exists, setup logging
    g.logger.add_window_logger(log_level='DEBUG')
    g.logger.set_window_logstream(window.textbox.text)
    g.logger.set_window_loglevel('INFO')

if __name__ == "__main__":
    
    g.logger = Log(c.APPNAME,console_loglevel=logging.DEBUG)
    g.config = GlobalConfig()
    

    a = Tk()    
    w = Windoof(a)
    setup_logging(w)
    p = PluginLoader(w)

    w.finalize(p)
    

    
    a.mainloop()

