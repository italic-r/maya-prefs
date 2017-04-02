#nm_python_softIK_UI
import maya.cmds as cmds

def softIK_UI():
	#check to see if our window exists
	if cmds.window("softIK_UI", exists = True):
		cmds.deleteUI("softIK_UI")
		
#=============================================================================================================================#     

	#create our window
	window = cmds.window("softIK_UI", title = "Soft IK Creator", w = 425, h = 280, mnb = False, mxb = False, sizeable = False)
	
	#create a main layout
	mainLayout = cmds.columnLayout(w = 425, h = 280)
	
#-----------------------------------------------------------------------------------------------------------------------------#    
	#add columns
	cmds.separator (h = 5)
	rowColumnLayout = cmds.rowColumnLayout(nc = 3, cw = [(1, 300) , (2, 30) , (3, 95)], columnOffset = [(1, "both", 5), (2, "left", 5), (3, "both", 5)])
#-----------------------------------------------------------------------------------------------------------------------------#	
	#name input text field and stretch option
	cmds.text(label = "Name:", align = "left")
	

	cmds.separator (h = 6, style = 'none')
	cmds.separator (h = 6, style = 'none')
	
	name = cmds.textField("name", w = 200, h = 30)
	cmds.text(label = "<--")
	stretch = cmds.checkBox( "stretch", label = 'Add Stretch' )
#-----------------------------------------------------------------------------------------------------------------------------#   
	cmds.separator (h = 6, style = 'none')
	cmds.separator (h = 6, style = 'none')
	cmds.separator (h = 6, style = 'none')
#-----------------------------------------------------------------------------------------------------------------------------# 
	#ctrlName input text field
	cmds.text(label = "Control:", align = "left")

	cmds.separator (h = 6, style = 'none')
	cmds.separator (h = 6, style = 'none')
	
	ctrlName = cmds.textField("ctrlName", w = 200)
	cmds.text(label = "<--")
	addSelectedButton_1 = cmds.button('addSelected_1', l = '...', w = 30, h = 30, c = loadToctrlName)
#-----------------------------------------------------------------------------------------------------------------------------#
	cmds.separator (h = 6, style = 'none')
	cmds.separator (h = 6, style = 'none')
	cmds.separator (h = 6, style = 'none')
#-----------------------------------------------------------------------------------------------------------------------------#
	#ikhName input text field
	cmds.text(label = "IK Handle:", align = "left")

	cmds.separator (h = 3, style = 'none')
	cmds.separator (h = 3, style = 'none')
	
	ikhName = cmds.textField("ikhName", w = 200)
	cmds.text(label = "<--")
	addSelectedButton_2 = cmds.button('addSelected_2', l = '...', w = 30, h = 30, c = loadToikhName)

#-----------------------------------------------------------------------------------------------------------------------------#
	#create the axis options
	cmds.columnLayout(w = 425, h = 132)
	cmds.separator (h = 5)
	rowColumnLayout2 = cmds.rowColumnLayout(nc = 2, cw = [(1, 412) , (2, 5)], columnOffset = [(1, "both", 0), (2, "left", 5)])
	cmds.separator (h = 3, style = 'in' )
	cmds.separator (h = 7, style = 'none' )
	
	#upAxis
	cmds.text(label = "Up Axis:", h = 20, al = 'left')
	cmds.separator (h = 1, style = 'none' )
	upAxis = cmds.radioButtonGrp( "upAxis", la3 = ['X', 'Y', 'Z'], nrb = 3, sl = 1 )
	cmds.separator (h = 3, style = 'none' )
	
	#primaryAxis
	cmds.text(label = "Primary Joint Axis:", h = 20, al = 'left')
	cmds.separator (h = 3, style = 'none' )
	primaryAxis = cmds.radioButtonGrp( "primaryAxis", la3 = ['X', 'Y', 'Z'], nrb = 3, sl = 1, h = 25 )
	cmds.separator (h = 5)
	
#-----------------------------------------------------------------------------------------------------------------------------#
	#create the build and close button
	rowColumnLayout3 = cmds.rowColumnLayout(nc = 2, cw = [(1, 200) , (2, 200)], columnOffset = [(1, "both", 0), (2, "left", 5)])
	b1 = cmds.button(label = "GO!", w = 205, h = 30, c = 'nm_python_softIK_proc.softIK_proc()' )
	b2 = cmds.button(label = "Nevermind.", w = 205, h = 30, c = 'cmds.deleteUI("softIK_UI")' )
	
#=============================================================================================================================#       
	#show window
	cmds.showWindow(window)
#=============================================================================================================================#   



#load selected for the ctrlName textField
def loadToctrlName(*args):
	sel = cmds.ls( sl=True )
	if len( sel ):
		cmds.textField( 'ctrlName', e = True, tx = sel[0] )
#load selected for the ikhName textField
def loadToikhName(*args):
	sel = cmds.ls( sl=True )
	if len( sel ):
		cmds.textField( 'ikhName', e = True, tx = sel[0] )