'''
Created on 31.12.2009

@author: mah
'''
from Tkinter import *
import Pmw
from TreeBrowser import TreeBrowser

loremipsum = '''
Lorem ipsum nec labore docendi sententiae at, cu his integre ceteros definiebas. Per choro expetenda voluptatum ad, cu dolorem scaevola deterruisset vel, nec et sonet dictas legendos. Ponderum consequat eloquentiam ex vel, doctus feugait ex eam. Indoctum maiestatis vim ne, assum admodum noluisse pri ei. Has te tale vitae audiam, modo vide suscipiantur ne est, placerat singulis ut eos.
An sumo3 ferri ceteros pri, pri ad nullam mentitum pertinax. Pro dicunt nominavi voluptatibus eu, veritus noluisse scriptorem ea nam. Alia deserunt reformidans cu sit. Ei vel magna blandit, ut nec quem laudem persecuti. Ullum clita option sea in. Id nec eius iisque definitiones, ut perfecto hendrerit suscipiantur qui.
In ius quas mutat everti. Ut idque nostrud tractatos vix, est in persius scripserit sadipscing, has cu cibo assum numquam. Ei delenit phaedrum gloriatur eum, omnes moderatius no nam, cum te falli impedit fastidii. Eu sea legere docendi liberavisse. Error partiendo eu vel, ei duo aliquid molestiae, delectus oporteat elaboraret ea vix. Ut pertinax corrumpit mediocritatem eos, tota fugit atomorum et vim, dolor commodo nostrum sea ea.
Eos debet tincidunt no, pri vitae vivendo liberavisse ad, ut modo tamquam explicari usu. Vim cu sapientem facilisis vituperata, te sea ancillae vivendum deseruisse. Id mei cibo accumsan mediocritatem, ut nobis veritus ocurreret pro, quo no aliquip tibique. Cum aperiam ocurreret consetetur id, eos congue iisque mandamus ea. Has quidam offendit referrentur ne, nam ludus causae argumentum in, vix eu minim contentiones. At cum agam vero legimus, alienum offendit aliquando ex vel, vim solet sadipscing reformidans ad.
Aliquid corpora cotidieque ea nec, cu decore consectetuer sea, eu his verterem reformidans. Sea enim hinc utinam no, est ne cibo fugit graece, te eam laudem inciderint. Puto idque vocibus ex mei, et pri nisl utamur singulis. Vix falli diceret facilisis eu, eu enim delicata maluisset eos.
Eos te quem quis veri, ex salutandi persequeris eum, an sea odio error prompta. Labore maiestatis no est, in mei esse dicit constituam. In qui oratio fierent oporteat, nec simul sanctus copiosae ne, pro an regione sensibus rationibus. Duo dico novum eleifend ei, has ex mucius referrentur vituperatoribus. Copiosae invidunt patrioque ea sit, nisl numquam eum te. Sint lucilius pro ei, at nonumy nostrud periculis eam, tale homero contentiones mea an.
Nostrud quaeque consulatu ne vel. Mandamus scripserit eu per, eu duo tamquam delicata. Has magna oporteat at, augue graecis complectitur cum eu. In labores iudicabit dignissim nec, ex albucius verterem complectitur sit, ut nibh quidam sed. Nam cu latine dolorum deserunt, timeam sadipscing ut eum.
Te nominavi appareat invidunt per, vel amet reformidans ad. Sapientem contentiones delicatissimi sit et, ea cum odio oratio nonumy. Ad sea vidit atomorum accommodare, sea ne sadipscing accommodare comprehensam. Sed inimicus voluptatibus vituperatoribus te, ad vim populo eirmod consequuntur. Ea qualisque adipiscing constituam qui, ei sea mutat nominavi delicata. Et tale decore postea est, ex ipsum vituperata has.
Eligendi principes complectitur id cum, iriure impetus sapientem an ius, ea vix habemus electram gubergren. Everti scripta vituperatoribus id sea, no solet voluptua philosophia mei. Et exerci molestiae sea, cu usu nisl dolore vituperata, epicuri suscipit te cum. Elit minimum expetendis usu ex, consul persius insolens et cum. Detracto probatus et eos, et vel labore pertinax vulputate. Ea commodo prodesset nam, vis lorem partem perpetua et, quis latine gubergren pro no. Cum probo habeo quidam ne, id putent feugait civibus mel.
Mei cu quod quaestio, mel vero aliquam inciderint eu, sea no tritani aliquyam. Admodum detracto prodesset eum ut, an vix affert scaevola electram. Te suas tempor ornatus eum, atqui dicam legere est id, per id unum utinam legere. Duo ex sanctus philosophia, kasd audiam adipiscing no vis. In est movet omnes platonem, id docendi detracto posidonium sed, te malis perfecto corrumpit mel. Ut vis paulo ridens repudiare, puto iusto noluisse quo ea, in mei nonumy nonummy efficiantur.

'''
         


root = Tk()
#root.option_readfile('optionDB')
root.title('PanedWidget')
Pmw.initialise()

pane = Pmw.PanedWidget(root, hull_width=900, hull_height=600,orient=HORIZONTAL)
#pane = Pmw.PanedWidget(root,orient=HORIZONTAL)
pane.add('left', size=240)
pane.add('right',size=650)


leftpane = Pmw.PanedWidget(pane.pane('left'), orient=VERTICAL)
ltop = leftpane.add("lefttop",min=200)
lbot = leftpane.add("leftbottom",min=200)


ltnb = Pmw.NoteBook(ltop)
options = ltnb.add('Options')
machine = ltnb.add('Machine')
mill = ltnb.add('Mill')
alu = ltnb.add('alu')
ltnb.pack(padx=5, pady=5, fill=BOTH, expand=1)
ltnb.setnaturalsize()

balloon = Pmw.Balloon(root)

noval = Pmw.EntryField(options, labelpos=W, label_text='No validation',
        validate = None)
real  = Pmw.EntryField(options, labelpos=W,    value = '98.4',
        label_text = 'Real (96.0 to 107.0):',
        validate = {'validator' : 'real',
            'min' : 96, 'max' : 107, 'minstrict' : 0})
int   = Pmw.EntryField(options, labelpos=W, label_text = 'Integer (5 to 42):',
        validate = {'validator' : 'numeric',
            'min' : 5, 'max' : 42, 'minstrict' : 0},    
        value = '12')
date = Pmw.EntryField(options, labelpos=W,    label_text = 'Date (in 2000):',
        value = '2000/1/1', validate = {'validator' : 'date',
            'min' : '2000/1/1', 'max' : '2000/12/31',
            'minstrict' : 0, 'maxstrict' : 0,
            'format' : 'ymd'})
balloon.bind(noval, 'Random explanations', 'Enter your name')


widgets = (noval, real, int, date)

for widget in widgets:
    widget.pack(fill=X, expand=1, padx=10, pady=5)
Pmw.alignlabels(widgets)
real.component('entry').focus_set()

lbnb = Pmw.NoteBook(lbot)
exp = lbnb.add('Export set')
#exp1 = lbnb.add('Export set 2')
layers =    lbnb.add('Layers')
entitites = lbnb.add('Entities')
lbnb.pack(padx=5, pady=5, fill=BOTH, expand=1)
lbnb.setnaturalsize()

box = None

def selectionCommand():
    sels = box.getcurselection()
    if len(sels) == 0:
        print 'No selection'
    else:
        print 'Selection:', sels[0]

box = Pmw.ScrolledListBox(exp, listbox_selectmode=MULTIPLE,
              items=('John Cleese', 'Eric Idle', 'Graham Chapman',
                     'Terry Jones', 'Michael Palin', 'Terry Gilliam',
                     'Terry Jones', 'Michael Palin', 'Terry Gilliam',
                     'Terry Jones', 'Michael Palin', 'Terry Gilliam'),
              labelpos=NW, label_text='Cast Members',
              listbox_height=5, vscrollmode='dynamic',hscrollmode='dynamic',
              selectioncommand=selectionCommand,
          dblclickcommand=selectionCommand ) #,
 #         usehullsize=1, hull_width=200, hull_height=200,)

box.pack(fill=BOTH, expand=1, padx=5, pady=5)

# Create the hierarchical tree browser widget
treeBrowser = TreeBrowser(layers,
                                      #selectbackground = "darkgreen",
                                      #selectforeground = 'lightgreen',
                                      #background = 'green',
                                      #indent = 10,
                                      )


def printselected(node):
    selection = treeBrowser.curselection()
    if selection != None:
        print "Selected node name:", selection[1], "   label:", selection[2]


def printdeselected(node):
    selection = treeBrowser.curselection()
    if selection != None:
        print "Deselected node name:", selection[1], "   label:", selection[2]

def printexpanded(node):
    print "Expanded node name:", node.getname(), "   label:", node.getlabel()

def printcollapsed(node):
    print "Collapsed node name:", node.getname(), "   label:", node.getlabel()



for i in range(3):
    # Add a tree node to the top level
    treeNodeLevel1 = treeBrowser.addbranch(label = 'TreeNode %d'%i,
                                           selectcommand = printselected,
                                           deselectcommand = printdeselected,
                                           expandcommand = printexpanded,
                                           collapsecommand = printcollapsed,
                                           )
    for j in range(3):
        # Add a tree node to the second level
        treeNodeLevel2 = treeNodeLevel1.addbranch(label = 'TreeNode %d.%d'%(i,j),
                                                  #selectforeground = 'yellow',
                                                  selectcommand = printselected,
                                                  deselectcommand = printdeselected,
                                                  expandcommand = printexpanded,
                                                  collapsecommand = printcollapsed,
                                                  )
        if i == 0 and j == 1:
            dynamicTreeRootNode = treeNodeLevel1
            dynamicTreePosNode = treeNodeLevel2
            
        for item in range((i+1)*(j+1)):
            # Add a leaf node to the third level
            leaf = treeNodeLevel2.addleaf(label = "Item %c"%(item+65),
                                          #selectbackground = 'blue',
                                          selectcommand = printselected,
                                          deselectcommand = printdeselected)
    for item in range(i+1):
        # Add a leaf node to the top level
        leaf = treeNodeLevel1.addleaf(label = "Item %c"%(item+65),
                                      selectcommand = printselected,
                                      deselectcommand = printdeselected)


treeNodeLevel1 = treeBrowser.addbranch(label = 'Check Button Label',
                                       selectcommand = printselected,
                                       deselectcommand = printdeselected,
                                       expandcommand = printexpanded,
                                       collapsecommand = printcollapsed,
                                       )
checkButton = Checkbutton(treeNodeLevel1.interior(),
                                  text = 'Da Check Button',
                                  relief = 'ridge',
                                  command = treeNodeLevel1.select)
checkButton.pack()

treeNodeLevel1.addleaf(label = 'Labeled Leaf',
                       selectcommand = printselected,
                       deselectcommand = printdeselected)
leaf = treeNodeLevel1.addleaf(label = 'Labeled Leaf w/ Checkbutton',
                              selectcommand = printselected,
                              deselectcommand = printdeselected)
checkButton = Checkbutton(leaf.interior(),
                                  text = 'Da Check Button',
                                  relief = 'ridge',
                                  command = leaf.select)
checkButton.pack()


treeNodeLevel1 = treeBrowser.addbranch(selectcommand = printselected,
                                       deselectcommand = printdeselected,
                                       expandcommand = printexpanded,
                                       collapsecommand = printcollapsed,
                                       )
checkButton = Checkbutton(treeNodeLevel1.interior(),
                                  text = 'Check Button with no label',
                                  relief = 'ridge',
                                  command = treeNodeLevel1.select)
checkButton.pack()

treeNodeLevel1 = treeBrowser.addbranch(label = 'Label',
                                       selectcommand = printselected,
                                       deselectcommand = printdeselected,
                                       expandcommand = printexpanded,
                                       collapsecommand = printcollapsed,
                                       )

# setup dynamic tree node insertion and removal
class dynTree:
    def __init__(self):
        self.dyn = IntVar()
        self.dtree = None

        self.dLeaf = treeBrowser.addleaf(selectcommand = self.dynSelected,
                                         deselectcommand = self.dynDeselected)
        
        self.dCheckButton = Checkbutton(self.dLeaf.interior(),
                                                text = 'Enable Dynamic Tree',
                                                variable = self.dyn,
                                                command = self.ChkBtnHandler)
        self.dCheckButton.pack()

        
    def dynSelected(self, node):
        self.dCheckButton.configure(background = self.dLeaf.configure('selectbackground')[4])
        printselected(node)
            
    def dynDeselected(self, node):
        self.dCheckButton.configure(background = self.dLeaf.configure('background')[4])
        printdeselected(node)
                
    def ChkBtnHandler(self):
        self.dLeaf.select()
        if self.dyn.get() == 1:
            self.dtree = dynamicTreeRootNode.insertbranch(label = 'Dynamic Tree Node',
                                                          selectcommand = printselected,
                                                          deselectcommand = printdeselected,
                                                          expandcommand = printexpanded,
                                                          collapsecommand = printcollapsed,
                                                          before = dynamicTreePosNode)
            self.dtree.addleaf(label = 'Dynamic Leaf 1',
                               selectcommand = printselected,
                               deselectcommand = printdeselected)
            self.dtree.addleaf(label = 'Dynamic Leaf 2',
                               selectcommand = printselected,
                               deselectcommand = printdeselected)
        else:
            if self.dtree != None:
                dynamicTreeRootNode.delete(self.dtree)
                self.dtree = None


foo = dynTree()


treeBrowser.pack(expand = 1, fill='both')









rightpane = Pmw.PanedWidget(pane.pane('right'), orient=VERTICAL)
rtop = rightpane.add("righttop",size=500)
rbot = rightpane.add("rightbottom",min=20,max=200)


sc = Pmw.ScrolledCanvas(rtop, borderframe=1, labelpos=N,
                        label_text='ScrolledCanvas', usehullsize=1,
                         hull_width=650,    hull_height=500)
for i in range(20):
    x = -10 + 3*i
    y = -10
    for j in range(10):
        sc.create_rectangle('%dc'%x,'%dc'%y,'%dc'%(x+2),'%dc'%(y+2),
                            fill='cadetblue', outline='black')
        sc.create_text('%dc'%(x+1),'%dc'%(y+1),text='%d,%d'%(i,j),
                       anchor=CENTER, fill='white')
        y = y + 3
sc.pack(fill=BOTH, expand=1)
sc.resizescrollregion()

st = Pmw.ScrolledText(rbot, borderframe=1) #, labelpos=N,
#        label_text='Blackmail', #usehullsize=1,
#        hull_width=400, hull_height=300,
#        text_padx=10, text_pady=10,
#        text_wrap='none')

st.settext(loremipsum)
st.pack(fill=BOTH, expand=1, padx=5, pady=5)



pane.pack(expand=1, fill=BOTH)
leftpane.pack(expand=1, fill=BOTH)
rightpane.pack(expand=1, fill=BOTH)

root.mainloop()



