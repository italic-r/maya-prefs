"""By Rob Galanakis"""

from qtshim import wrapinstance, QtWidgets
import pymel.core as pmc
import maya.OpenMayaUI as mui


def get_maya_window():
    winptr = mui.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError("No maya window found.")
    window = wrapinstance(winptr)
    assert isinstance(window, QtWidgets.QMainWindow)
    return window


def get_main_window_name():
    return pmc.MelGlobals()['gMainWindow']


class UndoChunk():
    """
    UndoChunk context manager
    by Rob Galanakis: Practical Maya Programming with Python
    """

    def __enter__(self):
        pmc.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pmc.undoInfo(closeChunk=True)
        if exc_val is not None:
            pmc.undo()
