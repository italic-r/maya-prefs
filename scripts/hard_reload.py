import sys

# qt bindings
for each in ("PySide", "PySide2"):
    try:
        _temp = __import__(each, locals(), globals(), ("QtGui", "QtCore"), -1)
        QtGui = _temp.QtGui
        QtCore = _temp.QtCore
        if each == "PySide2":
            _temp = __import__(each, locals(), globals(), ("QtWidgets", ), -1)
            QtWidgets = _temp.QtWidgets
        else:
            QtWidgets = QtGui
    except ImportError:
        pass
    else:
        break


class HardReload(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(HardReload, self).__init__(parent)
        self.setWindowTitle("Hard Reload")

        self.ui_lineEdit = QtWidgets.QLineEdit(self)
        ui_completer = QtWidgets.QCompleter(
            [i.split(".")[0] for i in sys.modules.keys()], self)
        ui_completer.setCompletionMode(QtWidgets.QCompleter.InlineCompletion)
        ui_completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.ui_lineEdit.setCompleter(ui_completer)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.ui_lineEdit)
        self.setLayout(hbox)

        self.ui_lineEdit.returnPressed.connect(self.accept)

    def move_window(self, pos=None):
        pos = pos or QtGui.QCursor.pos()
        self.move(pos.x(), pos.y())

    def accept(self, *args, **kwds):
        module_name = str(self.ui_lineEdit.text())
        if len(module_name):
            hard_reload(module_name)
        super(HardReload, self).close(*args, **kwds)


def get_parent():
    parent = QtWidgets.QApplication.activeWindow()
    if parent:
        _ = parent.parent()
        while _:
            parent = _
            _ = parent.parent()
    return parent


def hard_reload(module_name):
    for k in sys.modules.keys():
        if k.startswith(module_name):
            del sys.modules[k]


def show():
    w = HardReload(get_parent())
    w.move_window()
    w.exec_()


def __main__():
    QtWidgets.QApplication(sys.argv)
    show()
    sys.exit()


if __name__ == "__main__":
    __main__()
