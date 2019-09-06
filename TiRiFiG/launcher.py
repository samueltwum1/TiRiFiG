#!/usr/bin/env python
#########################################################################################
# Author: Samuel (samueltwum1@gmail.com) with MSc supervisors                           #
# Copyright 2019 Samuel N. Twum                                                         #
#                                                                                       #
# MIT license - see LICENSE.txt for details                                             #
#########################################################################################

"""
main : gets the whole thing started

"""

import logging, sys, os

from PyQt5 import QtCore, QtWidgets

from tirig import MainWindow


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    file_handler = logging.FileHandler('TiRiFiG.log', mode='a')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    logger.info("Log handling set up")

    if os.path.isfile(os.getcwd() + "/tmpDeffile.def"):
        os.remove(os.getcwd() + "/tmpDeffile.def")

    app = QtWidgets.QApplication(sys.argv)
    logger.info("Starting the GUI")
    GUI = MainWindow(logger)
    GUI.show()

    app.exec_()

if __name__ == '__main__':
    main()
