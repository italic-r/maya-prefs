import maya.api.OpenMaya as om
from maya import cmds
from maya import mel
import maya.utils as utils


# Red9 Tools
import Red9
Red9.start()
# end Red9


# start mGear
def mGearLoader():
    import mGear_menu
    mGear_menu.CreateMenu()
utils.executeDeferred('mGearLoader()')
# end mGear


# Viewport 2.0 settings
def setVP2settings(arg=None):
    """
    hwInstancingCheckBoxOnCommand;
    """
    cmds.setAttr("hardwareRenderingGlobals.consolidateWorld", True)
    cmds.setAttr("hardwareRenderingGlobals.vertexAnimationCache", 2)
    cmds.setAttr("hardwareRenderingGlobals.maxHardwareLights", 2)
    cmds.setAttr("hardwareRenderingGlobals.transparencyAlgorithm", 0)
    cmds.setAttr("hardwareRenderingGlobals.enableTextureMaxRes", 1)
    cmds.setAttr("hardwareRenderingGlobals.textureMaxResolution", 1024)
    cmds.setAttr("hardwareRenderingGlobals.ssaoEnable", False)
    cmds.setAttr("hardwareRenderingGlobals.motionBlurEnable", False)
    cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", False)
    cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", True)
    cmds.setAttr("hardwareRenderingGlobals.gammaCorrectionEnable", False)
    cmds.setAttr("hardwareRenderingGlobals.floatingPointRTEnable", False)
    cmds.setAttr("hardwareRenderingGlobals.caching", True)
    mel.eval('updateLineWidth 1.3;')
utils.executeDeferred('setVP2settings()')
om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, setVP2settings)
om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, setVP2settings)


# Open port for communication with Atom maya package
cmds.commandPort(name=":7005", sourceType="python")

# Open port for communication with Eclipse maya package
cmds.commandPort(name=":7720", sourceType="python", eo=False, nr=True)

"""
import os, inspect
USER_SETUP_PATH = os.path.dirname(inspect.currentframe().f_code.co_filename)
"""
# start aTools

if not cmds.about(batch=True):

    # launch aTools_Animation_Bar
    cmds.evalDeferred("from aTools.animTools.animBar import animBarUI; animBarUI.show('launch')", lowestPriority=True)

# end aTools
