import maya.utils as utils

def mGearLoader():
    import mGear_menu
    mGear_menu.CreateMenu()

utils.executeDeferred('mGearLoader()')
