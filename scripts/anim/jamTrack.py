'''
Copyright 2016 Jonathan Marshall

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


jamTrack
Author: Jonathan Marshall
Last Updated: Feb 5, 2016


To use this script, run as python:

    import jamTrack
    reload (jamTrack)
'''

import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMaya as om


winID = "jamTrack"
helpID = "HelpWindow"


# Launches Help Window.
def Help(self):

    helpID = "HelpWindow"

    # Closes the window first, if it already exists.
    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)

    # Opens a new Help window.
    cmds.window(helpID, title="Help", w=150, h=100, mnb=False, mxb=False, sizeable=False)
    cmds.columnLayout(w=150, h=150)

    helpText = '  // jamTrack //\n'\
               '  A tool for animation cleanup and repositioning.\n'\
               '\n'\
               '\n'\
               '  // LOCATOR ONLY // \n'\
               '  Creates a locator and snaps it to the location of your current selection.\n'\
               '\n'\
               '  // TRACK AND CONSTRAIN //\n'\
               '  (*select one object*)\n'\
               '  Creates a locator that follows the path of your  selected object in world\n'\
               '  space, and parent constrains the object to the locator. If a locator for\n'\
               '  the object already exists, its current position will be used instead of\n'\
               '  snapping to the object.\n'\
               '\n'\
               '  // TRACK, CONSTRAIN, AND PARENT //\n'\
               '  (*Select two objects*)\n'\
               '  Creates two locators, one for each object. The first locator tracks the\n'\
               '  first object selected, and the object is constrained to it. The second\n'\
               '  locator is parent constrained to the second object, and acts as a parent\n'\
               '  to the first locator. If a locator for the first object already exists,\n'\
               '  its current position will be used instead of snapping to the object.\n'\
               '\n'\
               '  // OPTIONS //\n'\
               '  Allows you to turn on/off translation and rotation for each of the\n'\
               '  constraint steps, and change the scale value of the Locator.\n'\
               '\n'\
               '  Created by Jonathan Marshall'

    cmds.text(helpText, align="left")

    cmds.showWindow()


# Creates just the Locator
def locatorOnly(self):

    sel = cmds.ls(sl=True)

    # Gives error if more than one object is selected.
    if len(sel) > 1:
        cmds.error("Too many objects selected!")

    # Creates and snaps a locator to object.
    elif len(sel):
        tObj = sel[0]
        tLoc = "{0}_tLoc".format(tObj)
        LScale = cmds.floatField(LocScale, q=True, v=True)

        if cmds.objExists(tLoc):
            cmds.delete(tLoc)

        cmds.spaceLocator(n="{0}_tLoc".format(tObj))
        cmds.scale(LScale, LScale, LScale)
        cmds.parentConstraint(tObj, tLoc, mo=False)
        cmds.parentConstraint(tObj, tLoc, rm=True)

        print LScale
    # Gives error if no objects are selected.
    else:
        cmds.error("No objects selected!")


# Runs Track and Constrain for single object.
def trackAndConstrain(self):

    # Queries the time slider.
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
    highlight = cmds.timeControl(aPlayBackSliderPython, query=True, rangeVisible=True)

    sel = cmds.ls(sl=True)

    v1 = cmds.checkBox(tTr, q=True, v=True)
    v2 = cmds.checkBox(tRo, q=True, v=True)
    v3 = cmds.checkBox(cTr, q=True, v=True)
    v4 = cmds.checkBox(cRo, q=True, v=True)

    tTranslation = 'none' if v1 else ["x", "y", "z"]
    tRotation = 'none' if v2 else ["x", "y", "z"]
    cTranslation = 'none' if v3 else ["x", "y", "z"]
    cRotation = 'none' if v4 else ["x", "y", "z"]

    # Gives error if more than one object is selected.
    if len(sel) > 1:
        cmds.error("Too many objects selected!")

    # If one object is selected, runs Track and Constrain.
    elif len(sel):
        tObj = sel[0]
        tLoc = "{0}_tLoc".format(tObj)

        # Constrains existing locator and bakes it, and constrains object to it.
        if cmds.objExists(tLoc):
            cmds.parentConstraint(tObj, tLoc, st=tTranslation, sr=tRotation, mo=True)

            if (highlight):
                tRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)

                cmds.bakeResults(tLoc, simulation=True, t=(tRange[0], tRange[1]))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=True)

            else:
                startTime = cmds.playbackOptions(query=True, minTime=True)
                endTime = cmds.playbackOptions(query=True, maxTime=True)

                cmds.bakeResults(tLoc, simulation=True, t=(startTime, endTime))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=True)

            cmds.select(tLoc)

        # Creates a locator, constrains it and bakes it, and constrains object to it.
        else:
            LScale = cmds.floatField(LocScale, q=True, v=True)

            cmds.spaceLocator(n="{0}_tLoc".format(tObj))
            cmds.scale(LScale, LScale, LScale)
            cmds.parentConstraint(tObj, tLoc, st=tTranslation, sr=tRotation, mo=False)

            if (highlight):
                tRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)

                cmds.bakeResults(tLoc, simulation=True, t=(tRange[0], tRange[1]))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=False)

            else:
                startTime = cmds.playbackOptions(query=True, minTime=True)
                endTime = cmds.playbackOptions(query=True, maxTime=True)

                cmds.bakeResults(tLoc, simulation=True, t=(startTime, endTime))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=False)

    # Gives error if no objects are selected.
    else:
        cmds.error("No objects selected!")


# Runs Track, Constrain, and Parent.
def trackAndParent(self):

    # Queries the time slider.
    aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
    highlight = cmds.timeControl(aPlayBackSliderPython, query=True, rangeVisible=True)

    sel = cmds.ls(sl=True)

    v1 = cmds.checkBox(tTr, q=True, v=True)
    v2 = cmds.checkBox(tRo, q=True, v=True)
    v3 = cmds.checkBox(cTr, q=True, v=True)
    v4 = cmds.checkBox(cRo, q=True, v=True)
    v5 = cmds.checkBox(pTr, q=True, v=True)
    v6 = cmds.checkBox(pRo, q=True, v=True)

    tTranslation = 'none' if v1 else ["x", "y", "z"]
    tRotation = 'none' if v2 else ["x", "y", "z"]
    cTranslation = 'none' if v3 else ["x", "y", "z"]
    cRotation = 'none' if v4 else ["x", "y", "z"]
    pTranslation = 'none' if v5 else ["x", "y", "z"]
    pRotation = 'none' if v6 else ["x", "y", "z"]

    # Gives error if more than two objects are selected.
    if len(sel) > 2:
        cmds.error("Too many objects selected!")
    # If two objects are selected, runs Track, Contrain, and Parent.
    elif len(sel) > 1:
        tObj = sel[0]
        pObj = sel[1]
        tLoc = "{0}_tLoc".format(tObj)
        pLoc = "{0}_pLoc".format(pObj)

        # Constrains existing locator and bakes it, and constrains object to it. Also constrains parent locator to second object.
        if cmds.objExists(tLoc):
            cmds.spaceLocator(n="{0}_pLoc".format(pObj))
            cmds.parentConstraint(pObj, pLoc, st=pTranslation, sr=pRotation, mo=False)
            cmds.parent(tLoc, pLoc)
            cmds.parentConstraint(tObj, tLoc, st=tTranslation, sr=tRotation, mo=True)

            if (highlight):
                tRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)

                cmds.bakeResults(tLoc, simulation=True, t=(tRange[0], tRange[1]))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=True)

            else:
                startTime = cmds.playbackOptions(query=True, minTime=True)
                endTime = cmds.playbackOptions(query=True, maxTime=True)

                cmds.bakeResults(tLoc, simulation=True, t=(startTime, endTime))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=True)
            cmds.select(tLoc)

        # Creates a locator, constrains it and bakes it, and constrains object to it. Also constrains parent locator to second object.
        else:
            LScale = cmds.floatField(LocScale, q=True, v=True)

            cmds.spaceLocator(n="{0}_tLoc".format(tObj))
            cmds.scale(LScale, LScale, LScale)
            cmds.spaceLocator(n="{0}_pLoc".format(pObj))
            cmds.parent(tLoc, pLoc)
            cmds.parentConstraint(pObj, pLoc, st=pTranslation, sr=pRotation, mo=False)
            cmds.parentConstraint(tObj, tLoc, st=tTranslation, sr=tRotation, mo=False)

            if (highlight):
                tRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)

                cmds.bakeResults(tLoc, simulation=True, t=(tRange[0], tRange[1]))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=False)

            else:
                startTime = cmds.playbackOptions(query=True, minTime=True)
                endTime = cmds.playbackOptions(query=True, maxTime=True)

                cmds.bakeResults(tLoc, simulation=True, t=(startTime, endTime))
                cmds.parentConstraint(tLoc, tObj, st=cTranslation, sr=cRotation, mo=False)

    # Gives error if only one object is selected.
    elif len(sel) == 1:
        cmds.error("No parent object selected!")

    # Gives error if no object is selected.
    else:
        cmds.error("No objects selected!")


# This section creates the UI Layout.

# Closes UI window if it already exists.
if cmds.window(winID, exists=True):
    cmds.deleteUI(winID)

# Closes Help window if it already exists.
if cmds.window(helpID, exists=True):
    cmds.deleteUI(helpID)

# UI Window.
cmds.window(winID, title="jamTrack", mnb=False, mxb=False, sizeable=False)

# Main Container.
mainLayout = cmds.rowColumnLayout(numberOfRows=3)

#Header.
header = cmds.rowColumnLayout(numberOfColumns=2)
cmds.separator(style='none', width=115)
cmds.button(label=" Help ", command=Help)

# Body.
bodyLayout = cmds.formLayout(parent=mainLayout)
tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5)
cmds.formLayout(bodyLayout, edit=True, attachForm=((tabs, 'top', 0), (tabs, 'left', 0), (tabs,
                'bottom', 0), (tabs, 'right', 0)))

# Tab1.
child1 = cmds.rowColumnLayout(numberOfRows=6)
cmds.separator(style='none', height=8)
cmds.button(label=" Locator Only ", command=locatorOnly, height=28)
cmds.separator(style='none', height=3)
cmds.button(label=" Track and Constrain ", command=trackAndConstrain, height=28)
cmds.separator(style='none', height=3)
cmds.button(label=" Track, Constrain and Parent ", command=trackAndParent, height=28)

# Tab2.
child2 = cmds.rowColumnLayout(parent=tabs, numberOfColumns=2)
tOptions = cmds.rowColumnLayout(parent=child2, numberOfRows=4)
cmds.text("Track", font="boldLabelFont")
cmds.separator()
tTr = cmds.checkBox(label='Translation', v=True)
tRo = cmds.checkBox(label='Rotation', v=True)

cOptions = cmds.rowColumnLayout(parent=child2, numberOfRows=4)
cmds.text("Constrain", font="boldLabelFont")
cmds.separator()
cTr = cmds.checkBox(label='Translation', v=True)
cRo = cmds.checkBox(label='Rotation', v=True)

cmds.rowColumnLayout(parent=child2, numberOfRows=3)
cmds.text('  Locator Scale ')
cmds.separator()
LocScale = cmds.floatField(value=30)

pOptions = cmds.rowColumnLayout(parent=child2, numberOfRows=4)
cmds.text("Parent", font="boldLabelFont")
cmds.separator()
pTr = cmds.checkBox(label='Translation', v=True)
pRo = cmds.checkBox(label='Rotation', v=True)

cmds.tabLayout(tabs, edit=True, tabLabel=((child1, 'Track'), (child2, 'Options')))

cmds.rowColumnLayout(parent=mainLayout, numberOfColumns=2)
cmds.separator(style="none", width=50)
cmds.text("jamTrack 1.0")


cmds.showWindow()
