#!/usr/bin/env python
#########################################################################################
# Author: Samuel (samueltwum1@gmail.com) with MSc supervisors                           #
# Copyright 2019 Samuel N. Twum                                                         #
#                                                                                       #
# MIT license - see LICENSE.txt for details                                             #
#########################################################################################

from PyQt5 import QtCore, QtWidgets


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
