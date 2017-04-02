'''
Copyright Jeffrey "Italic_" Hoover 2016

This script is licensed under the Apache 2.0 license.
See details of this license here:
https://www.apache.org/licenses/LICENSE-2.0

To use the script, run:
import cameraStack
reload(cameraStack)

For help, see helpCall.helpText below,
or open the help from the script UI.

Jeffrey "Italic_" Hoover
10 Feb 2016
v1.2
'''

import maya.cmds as cmds
from functools import partial

windowID = 'camSettingsWindow'
helpID = 'camHelpWindow'


def createUI(pWindowTitle, pApplyCall):

    destroyWindow()

    cmds.window(
        windowID,
        title=pWindowTitle,
        sizeable=True,
        resizeToFitChildren=True
    )

    cmds.rowColumnLayout(
        numberOfColumns=3,
        columnWidth=[(1, 55), (2, 75), (3, 60)],
        columnOffset=[(1, 'left', 3), (2, 'right', 3), (3, 'left', 3)]
    )

    # First row - focal length
    cmds.button(label='Help', command=helpCall)
    cmds.text(label='Focal Length:')
    camFocLenField = cmds.floatField(value=35.0)

    # Second row - name
    cmds.separator(h=10, style='none')
    cmds.text(label='Name:')
    camNameField = cmds.textField(text='shot')

    # Third row - separators only
    cmds.separator(h=10, style='none')
    cmds.separator(h=10, style='none')
    cmds.separator(h=10, style='none')

    # Fourth row - buttons only
    cmds.button(label='Generate', command=genCall)
    cmds.button(
        label='Apply',
        command=partial(
            pApplyCall, camFocLenField, camNameField
        )
    )
    cmds.button(label='Cancel', command=destroyWindow)

    cmds.showWindow()


def applyCall(pCamFocLenField, pCamNameField, *args):
    """Create a new camera stack at the scene origin with
    assigned custom properties."""

    camFocLen = cmds.floatField(pCamFocLenField, query=True, value=True)
    camName = cmds.textField(pCamNameField, query=True, text=True)

    print 'Focal Length: %s' % (camFocLen)
    print 'Name: %s' % (camName)

    # Create new stack at scene origin
    camMover = cmds.circle(
        name=camName + '_cam_move_all',
        normal=[0, 1, 0],
        center=[0, 0, 0],
        radius=1.5,
        sweep=360,
        sections=8
    )

    # Beauty cam - basic camera moves
    cmds.camera(
        displayGateMask=True,
        filmFit='overscan',
        focalLength=camFocLen,
        overscan=1.0
    )

    mainCam = cmds.rename(camName + '_main')
    cmds.parent(mainCam, camMover)

    # Generate child cameras and connections
    subCam(mainCam, camName)

    cmds.select(mainCam, replace=True)

    destroyWindow()


def genCall(pCamNameExists, *args):
    """Generate a camera stack based on one or more selected cameras,
    using original properties for the rest of the stack."""
    selectedCam = cmds.ls(selection=True)

    if selectedCam is not None:
        camList = []
        for cams in selectedCam:
            if cmds.listRelatives(
                    cams, shapes=True,
                    type='camera'
            ) is not None:
                camList.append(cams)
            else:
                continue

        if camList != []:
            for item in camList:

                fL = '.focalLength'
                hFA = '.horizontalFilmAperture'
                vFA = '.verticalFilmAperture'
                camFocLen = cmds.getAttr(item + fL)
                camHoFiAp = cmds.getAttr(item + hFA)
                camVeFiAp = cmds.getAttr(item + vFA)

                print(
                    'Focal length: %s\n'
                    'Horizontal Film Aperture: %s\n'
                    'Vertical Film Aperture: %s'
                ) % (camFocLen, camHoFiAp,camVeFiAp)
                # Main mover
                camMover = cmds.circle(
                    name=item + '_cam_move_all',
                    normal=[0, 1, 0],
                    center=[0, 0, 0],
                    radius=1.5,
                    sweep=360,
                    sections=8
                )

                # Beauty cam - basic camera moves
                mainCam = item
                cmds.select(mainCam)
                mainCam = cmds.rename(item + '_main')
                cmds.parent(mainCam, camMover)

                # Generate child cameras and connections
                subCam(mainCam, item)

                cmds.select(mainCam, replace=True)

            destroyWindow()

        else:
            cmds.warning("Please select your camera(s) and generate again.")

    else:
        cmds.warning("Please select your camera(s) and generate again.")


def helpCall(*args):
    """Open a text window with help information."""
    helpText = (
        'Camera Stack: a camera generator for handheld motion.\n'
        '\n'
        '"Apply" creates a new stack at the scene origin with\n'
        'specified focal length.\n'
        '"Generate" creates a stack based on the currently selected\n'
        'camera(s), prefixing generated names with original\n'
        'camera name.\n'
        'Both operations connect focal length and film back\n'
        'attributes to the main camera. Namespaces are handled\n'
        'through the name query. To make a new namespace, you\n'
        'will need to create one in the namespace editor.\n'
        '\n'
        'by Jeffrey "Italic_" Hoover'
    )

    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)

    cmds.window(
        helpID,
        title='CamStackHelp',
        widthHeight=[300, 175],
        sizeable=True,
        resizeToFitChildren=True
    )
    cmds.columnLayout(width=300)
    cmds.scrollField(
        wordWrap=True,
        text=helpText,
        editable=False,
        width=300,
        height=175,
        font='smallPlainLabelFont'
    )

    cmds.showWindow()


def subCam(mainCam, camName):
    """Generate the stack of child cameras and parent
    under mainCam from the calling operation."""
    # Handheld1 - first layer of handheld motion
    cmds.camera(
        displayGateMask=True,
        filmFit='overscan',
        overscan=1.0
    )
    handCam1 = cmds.rename(camName + '_handheld_1')
    cmds.parent(handCam1, mainCam, relative=True)
    connectAtt(mainCam, handCam1)
    cmds.hide()

    # Handheld2 - second layer of handheld motion
    cmds.camera(
        displayGateMask=True,
        filmFit='overscan',
        overscan=1.0
    )
    handCam2 = cmds.rename(camName + '_handheld_2')
    cmds.parent(handCam2, handCam1, relative=True)
    connectAtt(handCam1, handCam2)

    # Shake1 - first layer of shake vibration
    cmds.camera(
        displayGateMask=True,
        filmFit='overscan',
        overscan=1.0
    )
    shakeCam1 = cmds.rename(camName + '_shake_1')
    cmds.parent(shakeCam1, handCam2, relative=True)
    connectAtt(handCam2, shakeCam1)

    # Shake2 - second layer of shake vibration
    cmds.camera(
        displayGateMask=True,
        filmFit='overscan',
        overscan=1.0
    )
    shakeCam2 = cmds.rename(camName + '_shake_2')
    cmds.parent(shakeCam2, shakeCam1, relative=True)
    connectAtt(shakeCam1, shakeCam2)


def connectAtt(camSrc, camTarget):
    """Connect vital attributes between source camera and child camera."""
    fL = '.focalLength'
    hFA = '.horizontalFilmAperture'
    vFA = '.verticalFilmAperture'
    lSR = '.lensSqueezeRatio'

    cmds.connectAttr((camSrc + fL), (camTarget + fL))
    cmds.connectAttr((camSrc + hFA), (camTarget + hFA))
    cmds.connectAttr((camSrc + vFA), (camTarget + vFA))
    cmds.connectAttr((camSrc + lSR), (camTarget + lSR))


def destroyWindow(*args):
    """If cameraStack windows exist, destroy them."""
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)


createUI('Create Camera Stack', applyCall)
