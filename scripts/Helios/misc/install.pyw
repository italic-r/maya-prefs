import sys
import os
import webbrowser
import subprocess
import shutil

from glob import glob
from PyQt4 import QtGui, QtCore

class HeliosInstallGUI(QtGui.QWidget):
    def __init__(self):
        super(HeliosInstallGUI, self).__init__()

        self.cur_path = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
        self.cur_path = self.cur_path.split("/")[0:-1]
        self.cur_path = "/".join(self.cur_path)
        self.setWindowIcon(QtGui.QIcon(self.cur_path + "/misc/ThibH-icon.png"))

        self.setStyleSheet("background-color: rgb(250, 250, 250); color: rgb(75, 75, 75); font-size: 12px;")

        self.mainLayout = QtGui.QVBoxLayout(self)

        self.label = QtGui.QLabel("Enter the path to the folder where you want to install Helios:")
        self.label.setStyleSheet('color: rgb(35, 35, 35);')

        self.directoryLineEdit = QtGui.QLineEdit(self)
        self.directoryLineEdit.setText('C:\Users\{0}\Documents\maya\scripts'.format(os.getenv('username')))
        self.directoryLineEdit.setStyleSheet('border-style: inset; color: rgb(35, 35, 35); border-width: 1px; border-color: rgb(125, 125, 125);')
        self.directoryLineEdit.setFixedHeight(25)

        self.installButton = customPushButton()
        self.installButton.clicked.connect(self.install)
        
        self.codeToCopy = QtGui.QTextEdit(self)

        self.explainLabel = QtGui.QLabel("^ execute this python script in Maya to launch Helios (<a href='http://helios.readthedocs.io/en/latest/_installation/creating_hotkey_in_maya.html'>see help</a>).")
        self.explainLabel.setStyleSheet('color: rgb(35, 35, 35);')
        self.explainLabel.setOpenExternalLinks(True)

        self.separatorLabel = QtGui.QLabel("---------------------")
        self.separatorLabel.setStyleSheet('color: rgb(200, 200, 200);')
        self.separatorLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.creditLabel = QtGui.QLabel('Made with love and a keyboard by <a href=http://www.thibh.com>Thibault Houdon</a>.')
        self.creditLabel.setStyleSheet('color: rgb(35, 35, 35);')
        self.creditLabel.setOpenExternalLinks(True)
        self.creditLabel.setAlignment(QtCore.Qt.AlignCenter)

        self.mainLayout.addWidget(self.label)
        self.mainLayout.addWidget(self.directoryLineEdit)
        self.mainLayout.addWidget(self.installButton)
        self.mainLayout.addWidget(self.codeToCopy)
        self.mainLayout.addWidget(self.explainLabel)
        self.mainLayout.addWidget(self.separatorLabel)
        self.mainLayout.addWidget(self.creditLabel)

        self.setWindowTitle("Helios - Installation")
        self.resize(500, 300)
        self.show()

        if os.path.isfile(self.cur_path + "/qt.conf"):
            os.remove(self.cur_path + "/qt.conf")


    def install(self):

        installation_path = str(self.directoryLineEdit.text().replace("\\", "/") + "/Helios")

        if not os.path.exists(installation_path):
            os.makedirs(installation_path)
        else:
            return QtGui.QMessageBox.critical(self, "There's been an error", "There's already a Helios folder at path location. Please choose another folder.")

        helios_path = self.cur_path + "/Helios.py"
        css_path = self.cur_path + "/misc/style.css"
        commands_path = self.cur_path + "/commands"
        docs_path = self.cur_path + "/docs"

        try:
            shutil.copy(helios_path, "{0}/Helios.py".format(installation_path))
        except Exception, e:
            print(str(e))
            return QtGui.QMessageBox.critical(self, "There's been an error", "Couldn't install files.")

        try:
            os.mkdir(installation_path + "/misc")
            shutil.copy(css_path, "{0}/misc/style.css".format(installation_path))
        except Exception, e:
            print(str(e))
            return QtGui.QMessageBox.critical(self, "There's been an error", "Couldn't install files.")
        
        try:
            shutil.copytree(commands_path, "{0}/commands".format(installation_path))
        except Exception, e:
            print(str(e))
            return QtGui.QMessageBox.critical(self, "There's been an error", "Couldn't install files.")

        try:
            shutil.copytree(docs_path, "{0}/docs".format(installation_path))
        except Exception, e:
            print(str(e))
            return QtGui.QMessageBox.critical(self, "There's been an error", "Couldn't install files.")

        self.installButton.setText("Helios has been successfully installed.")

        self.codeToCopy.setText("import sys\nsys.path.append('{0}')\n\nimport Helios\nHelios.HeliosGUI()".format(installation_path))
        self.codeToCopy.setFocus(True)
        self.codeToCopy.selectAll()
        self.codeToCopy.copy()

class customPushButton(QtGui.QPushButton):
    def __init__(self):
        super(customPushButton, self).__init__()
        self.setText('Start Installation')
        self.setStyleSheet('color: rgb(35, 35, 35); background: rgb(230, 230, 230); border: none; font-size: 14px;')

        self.setFixedHeight(50)

    def enterEvent(self, e):
        self.setStyleSheet('color: rgb(35, 35, 35); background: rgb(200, 200, 200); border: none; font-size: 14px;')

    def leaveEvent(self, e):
        self.setStyleSheet('color: rgb(35, 35, 35); background: rgb(230, 230, 230); border: none; font-size: 14px;')

    

app = QtGui.QApplication(sys.argv)
mainApp = HeliosInstallGUI()
sys.exit(app.exec_())