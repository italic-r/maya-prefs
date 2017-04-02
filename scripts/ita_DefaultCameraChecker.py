'''
This script is licensed under the Apache 2.0 license.
See details of this license here:
https://www.apache.org/licenses/LICENSE-2.0

To use the script, run:
import ita_DefaultCameraChecker
ita_DefaultCameraChecker.init()

To reset default PB camera, run:
import ita_DefaultCameraChecker
reload(ita_DefaultCameraChecker)
ita_DefaultCameraChecker.init()

To disable 2D Pan & Zoom removal, comment out line 148 with a #

For help, call:
DefaultCameraChecker.helpCall()
or open the help from the script UI.

Jeffrey "italic" Hoover
16 October 2016
v2.2
'''

import maya.cmds as cmds
import maya.mel as mel
from functools import partial

# Maya's stock camera names from hotbox marking menu
stockCamNames = ["persp", "side", "left", "top", "bottom", "front", "back"]
windowID = 'perspPlayBlast'
helpID = 'perspPlayBlastHelp'

customPBcam = ""  # Saves camera name for future playblasts
customPBcamTmp = "persp"  # Temp camera name save for unique playblasts


def draw_warning(pWindowTitle, pbContinue, setTempCam):
    """Draw the warning window."""
    destroyWindow()

    cmds.window(
        windowID,
        title=pWindowTitle,
        sizeable=True,
        resizeToFitChildren=True
    )
    rowcol = cmds.rowColumnLayout(
        numberOfColumns=1,
        columnWidth=[(1, 250)],
        columnOffset=[(1, 'both', 5)]
    )
    cmds.text(label='You are trying to playblast from a default camera!')
    cmds.separator(h=10, style='none')
    cmds.rowLayout(
        parent=rowcol,
        numberOfColumns=3,
        columnAttach=[
            (1, 'left', 1),
            (2, 'left', 1),
            (3, 'both', 1)
        ],
        columnWidth=[
            (1, 35),  # Total == 250 - margins
            (2, 85),
            (3, 112)
        ]
    )
    cmds.button(label='Help', command=helpCall)
    makeDefault = cmds.checkBox(label='Make Default')

    makeDefaultMenu = cmds.optionMenu(label='', changeCommand=setTempCam)
    cmds.menuItem(label='')
    for camera in cmds.listRelatives(cmds.ls(type="camera"), parent=True):
        if camera in stockCamNames:
            if camera == "persp":
                cmds.menuItem(label=camera)
                continue
            else:
                continue
        else:
            cmds.menuItem(label=camera)

    cmds.rowLayout(
        parent=rowcol,
        numberOfColumns=3,
        columnAttach=[
            (1, 'both', 2),
            (2, 'both', 2),
            (3, 'both', 2)
        ],
        columnWidth=[
            (1, 123),
            (2, 50),
            (3, 60)
        ]
    )
    cmds.separator(h=10, style='none')
    cmds.button(label='OK!', command=partial(pbContinue,
                                             makeDefault,
                                             makeDefaultMenu))
    cmds.button(label='Continue', command=blast)

    cmds.showWindow()


def pbContinue(makeDefault, makeDefaultMenu, *args):
    """Confirm playblasting."""
    activepanel = cmds.getPanel(withFocus=True)
    cam = cmds.modelEditor(activepanel, query=True, camera=True)
    global customPBcam

    if cmds.checkBox(makeDefault, query=True, value=True) is True:
        customPBcam = customPBcamTmp
        cmds.lookThru(activepanel, customPBcam)  # Global default PB cam
        blast()
        cmds.lookThru(activepanel, cam)  # Return to original camera

        destroyWindow()

    else:
        if customPBcamTmp != "":
            cmds.lookThru(activepanel, customPBcamTmp)  # Temp PB cam
            blast()
            cmds.lookThru(activepanel, cam)  # Return to original camera

            destroyWindow()
        else:
            cmds.warning("Please select a camera from the dropdown menu")


def setTempCam(camName):
    """Set temp camera for pbContinue"""
    global customPBcamTmp
    customPBcamTmp = camName


def blast(*args):
    """Playblast and settings. Change to your liking."""
    fileNameLong = cmds.file(query=True, sceneName=True, shortName=True)

    if fileNameLong == "":
        fileNameLong = "untitled"
    else:
        fileNameLong = cmds.file(query=True, sceneName=True, shortName=True)

    fileNameShort = fileNameLong.split(".")

    TimeRange = mel.eval('$tmpVar=$gPlayBackSlider')
    SoundNode = cmds.timeControl(TimeRange, query=True, sound=True)

    # Disable 2D Pan & Zoom in current viewport
    activepanel = cmds.getPanel(withFocus=True)
    cam = cmds.modelEditor(activepanel, query=True, camera=True)
    # camShape = cmds.listRelatives(cam, shapes=True)[0]
    cmds.setAttr(cam + '.panZoomEnabled', False)

    if cmds.ls(renderResolutions=True):
        ResX = cmds.getAttr("defaultResolution.width")
        ResY = cmds.getAttr("defaultResolution.height")

        cmds.playblast(
            filename=("movies/" + fileNameShort[0] + ".mov"),
            forceOverwrite=True, format="qt", compression="png",
            offScreen=True, width=ResX, height=ResY, quality=100,
            percent=100, sound=SoundNode
        )
    else:
        cmds.error("No resolution data in file. \
                    Please set resolution and save.")


def helpCall(*args):
    """Open a text window with help information."""
    helpText = (
        'Default Camera Checker: A tool to check if you\'re\n'
        'playblasting from a Maya default camera.\n'
        '\n'
        'If your active viewport does not use one of Maya\'s default \n'
        'cameras, it will automatically playblast to file. If your\n'
        'camera is any default camera, the tool will give options for\n'
        'blastable cameras. Use the dropdown menu to select a\n'
        'camera to blast from. Ensure you click an item or the script\n'
        'won\'t have a camera to blast from.\n'
        '\n'
        'Make Default - saves the selected camera for future blasts.\n'
        'OK! - initiates playblast with selected camera.\n'
        'Continue - blasts with current camera, regardless of settings.\n'
        'Help - opens this help window.\n'
        '\n'
        'by Jeffrey "Italic_" Hoover'
    )

    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)

    cmds.window(
        helpID,
        title='DefaultCameraCheckerHelp',
        widthHeight=[300, 200],
        sizeable=True,
        resizeToFitChildren=True
    )
    cmds.columnLayout(width=300)
    cmds.scrollField(
        wordWrap=True,
        text=helpText,
        editable=False,
        width=300,
        height=200,
        font='smallPlainLabelFont'
    )

    cmds.showWindow()


def destroyWindow(*args):
    """If perspPlayBlast windows exist, destroy them."""
    if cmds.window(windowID, exists=True):
        cmds.deleteUI(windowID)
    if cmds.window(helpID, exists=True):
        cmds.deleteUI(helpID)


def check_camera_name():
    """Get the active panel's camera.
    Return its status compared to stockCamNames."""
    activepanel = cmds.getPanel(withFocus=True)

    if cmds.getPanel(typeOf=activepanel) == 'modelPanel':
        cam = cmds.modelEditor(activepanel, query=True, camera=True)
        if cam in stockCamNames:
            return True
        else:
            return False

    else:
        return None


def init():
    """Initiate camera name comparison."""
    global customPBcamTmp
    customPBcamTmp = ""

    if customPBcam == "":
        if check_camera_name() is False:
            destroyWindow()
            blast()
        elif check_camera_name() is True:
            draw_warning('DefaultCameraChecker', pbContinue, setTempCam)
        else:
            cmds.warning("Activate a viewport and try again.")

    else:
        activepanel = cmds.getPanel(withFocus=True)
        cam = cmds.modelEditor(activepanel, query=True, camera=True)
        cmds.lookThru(activepanel, customPBcam)  # Global default PB cam
        blast()
        cmds.lookThru(activepanel, cam)  # Return to original camera
