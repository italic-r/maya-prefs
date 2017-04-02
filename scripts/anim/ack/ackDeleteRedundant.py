"""
ackDeleteRedundant 1.1
12/04/07
Aaron Koressel
23 Aug 2016 - Converted to Python by Jeffrey "italic" Hoover

Deletes keys that have the same value as its two
neighboring keys.  Will only delete keys that are
in the current selection.

SYNTAX:
mel:
ackDeleteRedundant;
python:
import ackDeleteRedundant
ackDeleteRedundant.ackDeleteRedundant()

EXAMPLE:
Assign this commnad to Ctrl-Alt-R:  ackDeleteRedundant;

CHANGELOG:
1.1 - 12/04/07
Uses a tolerance value for checking redundancy
1.0 - 2/9/07
First version
"""

import maya.cmds as cmds
import maya.OpenMaya as om
import sys


def ackDeleteRedundant():
    tolerance = 0.00001
    sc = cmds.keyframe(q=True, sl=True, name=True)

    # estimate time
    try:
        mx = len(sc)
    except TypeError:
        om.MGlobal.displayWarning("Select keys to continue")
        sys.exit()
    for ch in sc:
        mx += cmds.keyframe(ch, q=True, kc=True)

    # progess window
    cmds.progressWindow(
        title='ackDeleteRedundant',
        max=mx,
        status='Deleting redundant keys...',
        ii=True
    )

    # only run if at least one key is selected
    keyCount = cmds.keyframe(q=True, kc=True)
    if keyCount != 0:
        # loop over selected curves and process independently
        for c in sc:
            # progress update
            if cmds.progressWindow(q=True, ic=True):
                break
            cmds.progressWindow(e=True, step=1)

            # get values for current channel as array
            valueArray = cmds.keyframe(c, q=True, vc=True)

            inSeries = False
            first = False
            delArray = []

            # search for redundant keys
            for i, v in enumerate(valueArray):
                # progress update
                if cmds.progressWindow(q=True, ic=True):
                    break
                cmds.progressWindow(e=True, step=1)

                if i < len(valueArray) - 1:
                    delta = v - valueArray[i + 1]

                    if abs(delta) <= tolerance:
                        if first is False and inSeries is False:
                            first = True
                            inSeries = True

                        else:
                            # add to array of keys to delete
                            keyTime = cmds.keyframe(c, q=True, index=(i,), tc=True)
                            delArray.append(keyTime[0])

                    else:
                        # this value not the same as next to start series over
                        first = False
                        inSeries = False

            # delete the redundant keys but only those that were selected
            selArray = cmds.keyframe(c, q=True, tc=True)
            for i, v in enumerate(delArray):
                # progress update
                if cmds.progressWindow(q=True, ic=True):
                    break

                # see if this key is in the selection
                for j, w in enumerate(selArray):
                    # progress update
                    if cmds.progressWindow(q=True, ic=True):
                        break

                    if selArray[j] == delArray[i]:
                        # remove key
                        cmds.cutKey(c, time=(delArray[i], delArray[i]), clear=True)
                        break

    # kill window
    cmds.progressWindow(endProgress=True)
