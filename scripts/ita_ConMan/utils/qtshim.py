"""
Provides a common interface between PyQt4 and PySide.

By Rob Galanakis: Practical Maya Programming with Python
"""

from . import Qt
from Qt import QtCore, QtGui, QtWidgets

try:
    import pymel.internal.plogging as logging
except ImportError:
    import logging

log = logging.getLogger(__name__)

if Qt.__binding__ in ("PySide", "PySide2"):
    try:
        import shiboken
    except:
        from Shiboken import shiboken

    log.debug("Imported PySide and shiboken")

    def _getcls(name):
        result = getattr(QtWidgets, name, None)
        if result is None:
            result = getattr(QtCore, name, None)
        return result

    def wrapinstance(ptr):
        """
        Convert a pointer (int or long) into the concrete
        PyQt/PySide object it represents.
        """
        ptr = long(ptr)
        # Get the pointer as a QObject, and use metaObject
        # to find a better type.
        qobj = shiboken.wrapInstance(ptr, QtCore.QObject)
        metaobj = qobj.metaObject()
        # Look for the real class in qt namespaces.
        # If not found, walk up the hierarchy.
        # When we reach the top of the Qt hierarchy,
        # we'll break out of the loop since we'll eventually
        # reach QObject.
        realcls = None
        while realcls is None:
            realcls = _getcls(metaobj.className())
            metaobj = metaobj.superClass()
        # Finally, return the same pointer/object
        # as its most specific type.
        return shiboken.wrapInstance(ptr, realcls)

elif Qt.__binding__ in ("PyQt4", "PyQt5"):
    import sip
    log.debug("Imported PyQt and sip")

    def wrapinstance(ptr):
        """
        Convert a pointer (int or long) into the concrete
        PyQt/PySide object it represents.
        """
        return sip.wrapinstance(long(ptr), QtCore.QObject)
