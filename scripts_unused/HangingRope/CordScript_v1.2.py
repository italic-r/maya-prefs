######################################################
## Cord Script v 2.5                                ##
##--------------------------------------------------##
## Script Written by Lucas morgan.                  ##
## Other scripts, information,                      ##
## the most current version of this,                ##
## and my entire portfolio may be viewed at:        ##
## http://www.enviral-design.com/                   ##
##--------------------------------------------------##
## If you would like to use any part of this script ##
## in your own, or for any commercial purposes,     ##
## I would be grateful to know of it, and a small   ##
## credit somewhere would be very much appreciated. ##
## I can be contacted at:                           ##
## lucasm@enviral-design.com                        ##
######################################################

## To run this script, copy all of the text in this window into the python tab of your maya script editor.


import maya.cmds as cmds
import maya.mel as mel
import math as math
import random as rand
import string
import os

if(cmds.window('cordMaker', q=1, ex=1)):
	cmds.deleteUI('cordMaker')
if(cmds.windowPref('cordMaker', q=1, ex=1)):
	cmds.windowPref('cordMaker', r=1)

recoverySel = []
		
def recoverSel(self):
	recovRange = range(len(recoverySel))
	cmds.select(cl = 1)
	for item in recovRange:
		exec("cmds.select('" + str(recoverySel[item]) + "', add = 1)")
		
		
def makeCord():
	
	cordWeight = cmds.floatSliderButtonGrp('cordWeightGrp', q = True, v=True)
	randomWeightValue = cmds.floatSliderGrp('cordWeightRandomizeGrp', q=True, v=True)
	randomAttachValue = cmds.floatSliderGrp('cordWeightPointRandomization', q=True, v=True)

	curSel = cmds.ls(sl = 1, fl = 1)
	global recoverySel
	recoverySel = cmds.ls(sl = 1, fl = 1)
	curRange = range(len(cmds.ls(sl = 1, fl = 1)))
	ptList = []
	curveCode = ""

	for item in curRange:
		print item
		randomAttachPointX = rand.uniform(-randomAttachValue, randomAttachValue)
		randomAttachPointY = rand.uniform(-randomAttachValue, randomAttachValue)
		randomAttachPointZ = rand.uniform(-randomAttachValue, randomAttachValue)
		exec("cmds.select('" + str(curSel[item]) + "', r = 1)")
		exec("pt_" + str(curRange[item]) + " = cmds.xform(q = 1, ws = 1, t = 1)")
		print "pt_" + str(curRange[item])
		exec("print pt_" + str(curRange[item]))
		# exec("ptList.append(pt_" + str(curRange[item]) + ")")
		exec("tmp = " + "pt_" + str(curRange[item]))
		tmp = [(tmp[0] + randomAttachPointX), (tmp[1] + randomAttachPointY), (tmp[2] + randomAttachPointZ)]
		ptList.append(tmp)
		
	print ptList
	curveCode += "cmds.curve(d = 1, n = 'telephoneLine', p = ("
	for item in curRange:
		if (item != (1 - len(curRange))):
			curveCode += str(ptList[item]) + ", "
		else:
			curveCode += str(ptList[item])
	curveCode += "))"

	exec(curveCode)
	#------
	asd = .5
	curSel2 = cmds.ls(sl = 1, fl = 1)
	while(asd < (len(curRange) - 1)):
		cmds.select(curSel2[0], r = 1)
		cmds.insertKnotCurve(p = (asd), nk=1, rpo = 1)
		#cmds.select(curSel2[0], r = 1)
		#cmds.insertKnotCurve(p = (asd + .495), nk=1, rpo = 1)
		#cmds.select(curSel2[0], r = 1)
		#cmds.insertKnotCurve(p = (asd + .505), nk=1, rpo = 1)
		asd += 1

	asd = .5
	counter = 1
	while(asd < (len(curRange) - 1)):
		generatedRandomValue = rand.uniform(randomWeightValue*-1,randomWeightValue)
		# print generatedRandomValue
		exec("pt_before = cmds.xform('" + str(curSel2[0]) + ".cv[" + str(counter - 1) + "]', q = 1, t = 1)")
		exec("pt_after = cmds.xform('" + str(curSel2[0]) + ".cv[" + str(counter + 1) + "]', q = 1, t = 1)")
		distance = math.sqrt((pt_before[0]-pt_after[0])**2  + (pt_before[1]-pt_after[1])**2 + (pt_before[2]-pt_after[2])**2)
		exec("cmds.select('" + str(curSel2[0]) + ".cv[" + str(counter) + "]')")
		cmds.xform(r = 1, os = 1, t = [0,(distance * ((cordWeight + generatedRandomValue) * -1.00)),0])
		cmds.xform
		asd += 1
		counter += 2
		
	asd = .5
	cmds.select(curSel2[0], r = 1)
	while(asd < (len(curRange) - 1)):
		cmds.select(curSel2[0], r = 1)
		cmds.insertKnotCurve(p = (asd + .495), nk=1, rpo = 1)
		cmds.select(curSel2[0], r = 1)
		cmds.insertKnotCurve(p = (asd + .505), nk=1, rpo = 1)
		asd += 1
		
	cmds.select(curSel2[0], r = 1)
	cmds.rebuildCurve(ch=1, rpo=1, rt=0, end=1, kr=1, kcp=1, kep=0, kt=0, s=4, d=3, tol=0.01)
	if(len(recoverySel) < 1):
		cmds.button('backUp',e = 1, en = 0)
	else:
		cmds.button('backUp',e = 1, en = 1)

def makeGui():
	# Make a new window
	cordMakerWindow = cmds.window('cordMaker', title="Hanging Cord Generator", iconName='cordMaker', widthHeight=(350, 100) )
	cmds.columnLayout('uiColWrapper', w = 350, adjustableColumn=False, parent = 'cordMaker' )
	cmds.floatSliderGrp('cordWeightRandomizeGrp', label='Weight Randomization', v = .25, min =0, max = 5, cw2 = [120,200], parent = 'cordMaker' )
	cmds.floatSliderGrp('cordWeightPointRandomization', label='Attach Randomization', v = .2, min =0, max = 5, cw2 = [120,200], parent = 'cordMaker' )
	cmds.floatSliderButtonGrp('cordWeightGrp', label='Cord Weight', field=True, pre = 2,v = .25, min =-10, max = 10, buttonLabel='Generate', cw4 = [75,50,146,5], bc = makeCord, parent = 'cordMaker' )

	cmds.button('backUp', label = "Revert to Selection", parent = 'uiColWrapper', en = 0, width = 334, c = recoverSel)
	
	cmds.showWindow( cordMakerWindow )

makeGui()