# -*- coding: utf-8 -*-
""" Edit history
    Author : yda
    Date : 2020-11-19

    functions
    ---------
    main : Check if authorized users
"""

import os, time, sys, datetime
from PyQt5 import QtWidgets, QtGui

from mdfstudio.gui.utils import excepthook
from mdfstudio.gui.widgets.main import MainWindow
from mdfstudio.gui.auth import get_user_info, date_check, version_updated

sys.excepthook = excepthook


def main():

    if len(sys.argv) > 1:
        args = sys.argv[1]
    else:
        args = None

    app = QtWidgets.QApplication(sys.argv)

    if not date_check():
        msgBox = QtGui.QMessageBox()
        msgBox.setIcon(QtGui.QMessageBox.Critical)
        msgBox.setWindowTitle("Access Denied")
        msgBox.setText("This version has expired.")
        msgBox.exec()
        return

    user_check = get_user_info()
    if user_check != 'OK':
        msgBox = QtGui.QMessageBox()
        msgBox.setIcon(QtGui.QMessageBox.Critical)
        msgBox.setWindowTitle("Access Denied")
        msgBox.setText(f"{user_check}.\nProgram will terminate.")
        msgBox.exec()
        return

    #2021-03-09 version check
    updated, new_version, old_version = version_updated()
    if updated:
        msgBox = QtGui.QMessageBox()
        msgBox.setIcon(QtGui.QMessageBox.Information)
        msgBox.setWindowTitle("Software Update")
        msgBox.setText(f"MDF Studio - {new_version} is now available.You have {old_version}.\nInstall the latest update from [Help - Check for Updates]")
        msgBox.exec()

    app.setOrganizationName("py-mdfstudio")
    app.setOrganizationDomain("py-mdfstudio")
    app.setApplicationName("py-mdfstudio")
    main = MainWindow(args)
    main.setMinimumHeight(768)
    main.setMinimumWidth(1280)
    app.setStyle(QtWidgets.QStyleFactory.create("Fusion"))
    app.exec_()

if __name__ == "__main__":
    main()
