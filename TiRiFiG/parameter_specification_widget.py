#!/usr/bin/env python
#########################################################################################
# Author: Samuel (samueltwum1@gmail.com) with MSc supervisors                           #
# Copyright 2019 Samuel N. Twum                                                         #
#                                                                                       #
# MIT license - see LICENSE.txt for details                                             #
#########################################################################################

from PyQt5 import QtCore, QtWidgets


def _center(self):
    """Centers the window

    Parameters
    ----------
    self : QtWidgets.QWidget 
        the current instance of the window being displayed

    Notes
    -----
    The screen resolution is gotten from user's desktop and the center
    point is figured out for which the window is placed
    """
    # geometry of the main window
    q_rect = self.frameGeometry()

    # center point of screen
    centre_point = QtWidgets.QDesktopWidget().availableGeometry().center()

    # move rectangle's center point to screen's center point
    q_rect.moveCenter(centre_point)

    # top left of rectangle becomes top left of window centering it
    self.move(q_rect.topLeft())


class ParamSpec(QtWidgets.QWidget):

    def __init__(self, par, window_title, logger):
        super(ParamSpec, self).__init__()
        self.par = par
        self.window_title = window_title
        self.logger = logger

        self.lbl_parameter = QtWidgets.QLabel("Parameter")
        self.parameter = QtWidgets.QComboBox()
        self.parameter.setEditable(True)
        self.parameter.addItem("Select Parameter")
        for par in self.par:
            self.parameter.addItem(par)

        self.parameter.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.parameter.setMaxVisibleItems(6)
        index = self.parameter.findText("Select Parameter", QtCore.Qt.MatchFixedString)
        self.parameter.setCurrentIndex(index)
        self.lbl_unit_meas = QtWidgets.QLabel("Unit Measurement")
        self.unit_measurement = QtWidgets.QLineEdit()
        # self.unit_measurement.setPlaceholderText("Unit Measurement")

        self.grid = QtWidgets.QGridLayout()
        self.grid.setSpacing(10)
        self.grid.addWidget(self.lbl_parameter, 1, 0)
        self.grid.addWidget(self.parameter, 1, 1)
        self.grid.addWidget(self.lbl_unit_meas, 2, 0)
        self.grid.addWidget(self.unit_measurement, 2, 1)

        self.btn_ok = QtWidgets.QPushButton("OK", self)
        self.btn_cancel = QtWidgets.QPushButton("Cancel", self)

        self.h_box = QtWidgets.QHBoxLayout()
        self.h_box.addStretch(1)
        self.h_box.addWidget(self.btn_ok)
        self.h_box.addWidget(self.btn_cancel)

        self.grid.addLayout(self.h_box, 3, 1)
        self.setLayout(self.grid)

        self.setWindowTitle(self.window_title)
        self.setGeometry(300, 300, 300, 150)

        _center(self)
        self.setFocus()
