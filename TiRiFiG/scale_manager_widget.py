from PyQt5 import QtCore, QtWidgets


class ScaleManager(QtWidgets.QWidget):

    def __init__(self, x_vals, graph_widgets, logger):
        super(ScaleManager, self).__init__()
        self.x_min = x_vals[0]
        self.x_max = x_vals[1]
        self.graph_widgets = graph_widgets
        self.logger = logger
        self.prev_par_val = ""

        self.parameter = QtWidgets.QComboBox()
        self.parameter.setEditable(True)
        self.parameter.addItem("Select Parameter")
        for gw in self.graph_widgets:
            self.parameter.addItem(gw.par)
        # self.parameter.setAutoCompletion(True) : doesn't work in PyQt5
        self.parameter.setStyleSheet("QComboBox { combobox-popup: 0; }")
        self.parameter.setMaxVisibleItems(5)
        index = self.parameter.findText("Select Parameter", QtCore.Qt.MatchFixedString)
        self.parameter.setCurrentIndex(index)
        self.parameter.currentIndexChanged.connect(self.on_change_event)
        # run a for loop here to gather all the loaded parameters and populate as many text boxes

        self.x_label = QtWidgets.QLabel("RADI")
        self.txtbox_x_min = QtWidgets.QLineEdit()
        self.txtbox_x_min.setPlaceholderText("RADI min ("+str(self.x_min)+")")
        self.txtbox_x_max = QtWidgets.QLineEdit()
        self.txtbox_x_max.setPlaceholderText("RADI max ("+str(self.x_max)+")")
        self.x_grid = QtWidgets.QGridLayout()
        self.x_grid.setSpacing(10)
        self.x_grid.addWidget(self.x_label, 1, 0)
        self.x_grid.addWidget(self.txtbox_x_min, 2, 0)
        self.x_grid.addWidget(self.txtbox_x_max, 2, 1)

        self.txtbox_y_min = QtWidgets.QLineEdit()
        self.txtbox_y_max = QtWidgets.QLineEdit()
        self.y_grid = QtWidgets.QGridLayout()
        self.y_grid.setSpacing(10)
        self.y_grid.addWidget(self.parameter, 1, 0)
        self.y_grid.addWidget(self.txtbox_y_min, 2, 0)
        self.y_grid.addWidget(self.txtbox_y_max, 2, 1)

        self.h_box = QtWidgets.QHBoxLayout()
        self.h_box.addStretch(1)

        self.h_box_btns = QtWidgets.QHBoxLayout()
        self.h_box_btns.addStretch(1)
        self.btn_update = QtWidgets.QPushButton('Update', self)
        self.btn_update.clicked.connect(self.update_scale)
        self.btn_cancel = QtWidgets.QPushButton('Cancel', self)
        self.btn_cancel.clicked.connect(self.close)
        self.h_box_btns.addWidget(self.btn_update)
        self.h_box_btns.addWidget(self.btn_cancel)

        self.f_box = QtWidgets.QFormLayout()
        self.f_box.addRow(self.x_grid)
        self.f_box.addRow(self.y_grid)
        self.f_box.addRow(self.h_box_btns)

        self.setLayout(self.f_box)
        self.setWindowTitle("Scale Manager")
        self.setGeometry(300, 300, 300, 150)
        _center(self)
        self.setFocus()

        self.gw_dict = {}
        for gw in self.graph_widgets:
            self.gw_dict[gw.par] = gw.y_scale[:]

    def on_change_event(self):
        if self.txtbox_y_min.text():
            self.gw_dict[self.prev_par_val][0] = int(str(self.txtbox_y_min.text()))
        if self.txtbox_y_max.text():
            self.gw_dict[self.prev_par_val][1] = int(str(self.txtbox_y_max.text()))

        for gw in self.graph_widgets:
            if str(self.parameter.currentText()) == gw.par:
                self.txtbox_y_min.clear()
                self.txtbox_y_min.setPlaceholderText(gw.par+" min ("+str(self.gw_dict[gw.par][0])+")")
                self.txtbox_y_max.clear()
                self.txtbox_y_max.setPlaceholderText(gw.par+" max ("+str(self.gw_dict[gw.par][1])+")")
                self.prev_par_val = gw.par

    def update_scale (self):
        """Change the values of the instance variables and specific graph widget plots
        after update button is clicked.
        """
        if self.txtbox_x_min.text():
            self.x_min = int(str(self.txtbox_x_min.text()))

        if self.txtbox_x_max.text():
            self.x_max = int(str(self.txtbox_x_max.text()))

        if self.txtbox_y_min.text():
            self.gw_dict[self.prev_par_val][0] = int(str(self.txtbox_y_min.text()))

        if self.txtbox_y_max.text():
            self.gw_dict[self.prev_par_val][1] = int(str(self.txtbox_y_max.text()))

        for gw in self.graph_widgets:
            gw.y_scale = self.gw_dict[gw.par][:]
            gw.x_scale = [self.x_min, self.x_max]
            gw.first_plot()
        self.close()
        QtWidgets.QMessageBox.information(self, "Information", "Done!")
