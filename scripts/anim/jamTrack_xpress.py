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


jamTrack_xpress
Author: Jonathan Marshall
Last Updated: Feb 5, 2016


To use this script, run as python:

    import jamTrack_xpress
    reload (jamTrack_xpress)
'''

import maya.mel as mel
import maya.cmds as cmds
import maya.OpenMaya as om

# Queries the time slider.
aPlayBackSliderPython = mel.eval('$tmpVar=$gPlayBackSlider')
highlight = cmds.timeControl(aPlayBackSliderPython, query=True, rangeVisible=True)

sel = cmds.ls(sl=True)

# Gives error if more than 2 objects are selected.
if len(sel) > 2:
    cmds.error("Too many objects selected!")

# If two objects are selected, runs Track, Constrain, and Parent.
elif len(sel) > 1:
    tObj = sel[0]
    pObj = sel[1]
    tLoc = "{0}_tLoc".format(tObj)
    pLoc = "{0}_pLoc".format(pObj)

    # Creates Locator and Parent Locator, snaps them to selected objects, and constrains Object to Locator.
    cmds.spaceLocator(n="{0}_tLoc".format(tObj))
    cmds.scale(30, 30, 30)
    cmds.spaceLocator(n="{0}_pLoc".format(pObj))
    cmds.parent(tLoc, pLoc)
    cmds.parentConstraint(pObj, pLoc, mo=False)
    cmds.parentConstraint(tObj, tLoc, mo=False)

    if (highlight):

        tRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)

        cmds.bakeResults(tLoc, simulation=True, t=(tRange[0], tRange[1]))
        cmds.parentConstraint(tLoc, tObj, mo=False)

    else:
        startTime = cmds.playbackOptions(query=True, minTime=True)
        endTime = cmds.playbackOptions(query=True, maxTime=True)

        cmds.bakeResults(tLoc, simulation=True, t=(startTime, endTime))
        cmds.parentConstraint(tLoc, tObj, mo=False)

# If one object is selected, runs Track and Constrain.
elif len(sel):
    tObj = sel[0]
    tLoc = "{0}_tLoc".format(tObj)

    # Creates Locator, snaps to object, constrains object to Locator.
    cmds.spaceLocator(n="{0}_tLoc".format(tObj))
    cmds.scale(30, 30, 30)
    cmds.parentConstraint(tObj, tLoc, mo=False)

    if (highlight):
        tRange = cmds.timeControl(aPlayBackSliderPython, query=True, rangeArray=True)

        cmds.bakeResults(tLoc, simulation=True, t=(tRange[0], tRange[1]))
        cmds.parentConstraint(tLoc, tObj, mo=False)

    else:
        startTime = cmds.playbackOptions(query=True, minTime=True)
        endTime = cmds.playbackOptions(query=True, maxTime=True)

        cmds.bakeResults(tLoc, simulation=True, t=(startTime, endTime))
        cmds.parentConstraint(tLoc, tObj, mo=False)


# Gives error if no object selected.
else:
    cmds.error("No objects selected")
