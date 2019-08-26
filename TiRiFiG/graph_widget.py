import matplotlib
import matplotlib.pyplot as plt
from matplotlib import style
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from PyQt5 import QtCore, QtWidgets

style.use("seaborn")
matplotlib.use("qt5Agg")


class GraphWidget(QtWidgets.QWidget):
    """plotting window for each tilted ring parameter"""
    redo = []
    ms_click = [None, None]
    ms_release = [None, None]
    ms_motion = [None]
    ms_dbl_press = [None, None]
    last_value = 0

    def __init__(self, x_scale, y_scale, unit_meas, par, par_vals, par_val_radi,
                 history_list, key, x_precision, y_precision, logger):
        super(GraphWidget, self).__init__()
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.unit_meas = unit_meas
        self.par = par
        self.par_vals = par_vals
        self.par_val_radi = par_val_radi
        self.history_list = history_list
        self.key = key
        self.x_precision = x_precision
        self.y_precision = y_precision
        self.logger = logger

        # Grid Layout
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)
        # Canvas and Toolbar
        self.figure = plt.figure()

        self.canvas = FigureCanvas(self.figure)
        # self.canvas.setFocusPolicy( QtCore.Qt.ClickFocus )
        # self.canvas.setFocusPolicy( QtCore.Qt.WheelFocus )
        self.canvas.setFocus()


        self.canvas.mpl_connect('button_press_event', self.get_click)
        self.canvas.mpl_connect('button_release_event', self.get_release)
        self.canvas.mpl_connect('motion_notify_event', self.get_motion)
        # self.canvas.mpl_connect('key_press_event', self.keyPressed)

        self.ax = self.figure.add_subplot(111)

        # button to add another tilted-ring parameter to plot
        self.btn_add_param = QtWidgets.QPushButton('&Add',self)
        self.btn_add_param.setFixedSize(50, 30)
        self.btn_add_param.setFlat(True)
        # FIX ME: use icon instead of text
        # self.btn_add_param.setIcon(QtGui.QIcon('utilities/icons/plus.png'))
        self.btn_add_param.setToolTip('Add Parameter')

        # modify plotted parameter
        self.btn_edit_param = QtWidgets.QPushButton('&Change',self)
        self.btn_edit_param.setFixedSize(80, 30)
        self.btn_edit_param.setFlat(True)
        # FIX ME: use icon instead of text
        # self.btn_edit_param.setIcon(QtGui.QIcon('utilities/icons/edit.png'))
        self.btn_edit_param.setToolTip('Modify plotted parameter')

        h_box = QtWidgets.QHBoxLayout()
        h_box.addWidget(self.btn_add_param)
        h_box.addWidget(self.btn_edit_param)

        grid.addLayout(h_box, 0, 0)
        grid.addWidget(self.canvas, 2, 0, 1, 2)

        self.first_plot()

    def change_global(self, val=None):
        global curr_par
        if val == None:
            curr_par = None
        else:
            curr_par = self.par

    def _almost_equal(self, a, b, rel_tol=5e-2, abs_tol=0.0):
        '''Takes two values return true if they are almost equal'''
        diff = abs(b - a)
        return (diff <= abs(rel_tol * b)) or (diff <= abs_tol)

    def get_click(self, event):
        """Record x-y data when left mouse button is clicked

       Parameters
       ----------
        event : matplotlib.backend_bases.MouseEvent
            left mouse click in this case

        Notes
        -----
        The x_y_data is captured when the left mouse button is clicked on the canvas
        """
        # on left click in figure canvas, capture mouse press and assign 'None' to
        # mouse release
        if event.button == QtCore.Qt.LeftButton and not event.xdata is None:
            self.ms_click[0] = event.xdata
            self.ms_click[1] = event.ydata
            self.ms_release[0] = None
            self.ms_release[1] = None

        if event.dblclick and not event.xdata is None:
            self.ms_dbl_press[0] = event.xdata
            self.ms_dbl_press[1] = event.ydata

            text, ok = QtWidgets.QInputDialog.getText(self, "Input Dialog",
                                                      "Enter new node value:")
            if ok:
                if text:
                    new_val = float(str(text))
                    for idx, radi_val in enumerate(self.par_val_radi):
                        if ((self.ms_dbl_press[0] < (self.par_val_radi[idx])+3) and
                            (self.ms_dbl_press[0] > (self.par_val_radi[idx])-3)):

                            self.par_vals[idx] = new_val
                            bottom, top = self.ax.get_ylim()
                            self.ax.clear()
                            max_yvalue = max(self.par_vals)
                            min_yvalue = min(self.par_vals)

                            if self._almost_equal(min_yvalue, bottom, rel_tol=1e-2):
                                bottom *= 1.2
                                top = max_yvalue * 1.1
                            elif min_yvalue < bottom:
                                bottom = min_yvalue * 1.2
                                top = max_yvalue * 1.1

                            if self._almost_equal(max_yvalue, top, rel_tol=1e-2):
                                top *= 1.2
                                bottom = min_yvalue * 1.1
                            elif max_yvalue > top:
                                top = max_yvalue * 1.2
                                bottom = min_yvalue * 1.1

                            self.ax.set_ylim(bottom, top)
                            self.ax.set_xlabel("RADI (arcsec)")
                            self.ax.set_ylabel(self.par + "( "+self.unit_meas+ " )")
                            self.ax.plot(self.par_val_radi, self.par_vals, '--bo')
                            self.ax.set_xticks(self.par_val_radi)
                            self.canvas.draw()
                            self.key = "No"
                            break

                    # append the new point to the history if the last item in history differs
                    # from the new point
                    if not self.history_list[len(self.history_list)-1] == self.par_vals[:]:
                        self.history_list.append(self.par_vals[:])

            self.ms_click[0] = None
            self.ms_click[1] = None

    def get_release(self, event):
        """Record x-y data when left mouse button is released

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent
            left mouse button is released

        Notes
        -----
        The x_y_data is captured when the left mouse button is released on the canvas.
        The new data point is added to the history and mouse pressed is assigned None
        """
        # re-look at this logic --seems to be a flaw somewhere
        if not event.ydata is None:
            self.ms_release[0] = event.xdata
            self.ms_release[1] = event.ydata
            self.change_global()
            self.redo = []

        # append the new point to the history if the last item in history differs
        # from the new point
        if not self.history_list[len(self.history_list)-1] == self.par_vals[:]:
            self.history_list.append(self.par_vals[:])

        self.ms_click[0] = None
        self.ms_click[1] = None

    def get_motion(self, event):
        """Record x-y data when mouse is in motion

        Parameters
        ----------
        event : matplotlib.backend_bases.MouseEvent

        Notes
        -----
        The y_data is captured and plot for parameter in focus is redrawn
        """
        if event.guiEvent.MouseMove == QtCore.QEvent.MouseMove:
            if event.button == QtCore.Qt.LeftButton:
                # if the mouse pointer moves out of the figure canvas use
                # the last value to redraw the graph
                if event.ydata is None:
                    self.last_value += 0.1 * self.last_value
                    self.ms_motion[0] = self.last_value
                else:
                    self.last_value = event.ydata
                    self.ms_motion[0] = event.ydata
                self.plot_func()

    def undo_key(self):
        """Undo last action

        Notes
        -----
        Deletes the last item in the history list when "Ctrl+z" is pressed and
        re-draws graph
        """
        if len(self.history_list) > 1:
            self.redo.append([self.y_precision, self.par_vals[:],
                              self.history_list[-1], self.y_scale[:]])
            self.history_list.pop()
            self.par_vals = self.history_list[-1][:]
            self.key = "Yes"
            self.plot_func()
        else:
            QtWidgets.QMessageBox.information(self, "Information", "History list is exhausted")

    def redo_key(self):
        """Redo last action

        Notes
        -----
        Deletes the last item in the redo list when "Ctrl+y" is pressed and
        re-draws graph
        """

        if len(self.redo) > 0:
            self.y_precision = self.redo[-1][2]
            self.par_vals = self.redo[-1][3][:]
            self.history_list.append(self.redo[-1][4][:])
            self.y_scale = self.redo[-1][5][:]
            self.redo.pop()
            self.key = "Yes"
            self.plot_func()
        else:
            QtWidgets.QMessageBox.information(self, "Information", "History list is exhausted")

    def first_plot(self):
        """Plots data from .def file

        Notes
        -----
        Produces view graph from history_list
        """
        self.ax.clear()

        max_yvalue = max(self.history_list[-1])
        min_yvalue = min(self.history_list[-1])

        if max_yvalue == 0:
            top = 10 # this is some arbitrary number, rethink this
        else:
            top = max_yvalue + (0.1 * (max_yvalue))
        if min_yvalue == 0:
            bottom = -10 # ditto
        else:
            bottom = min_yvalue - (0.1 * (min_yvalue))

        self.ax.set_ylim(bottom, top)
        self.ax.set_xlabel("RADI (arcsec)")
        self.ax.set_ylabel(self.par + "( "+self.unit_meas+ " )")
        self.ax.plot(self.par_val_radi, self.history_list[-1], '--bo')
        self.ax.set_xticks(self.par_val_radi)
        self.canvas.draw()
        self.key = "No"

    def plot_func(self):
        """Plots data from file

        Notes
        -----
        Produces view graph from history_list or par_vals
        """

        if self.key == "Yes":
            self.first_plot()

        # this re-plots the graph as long as the mouse is in motion and the right data
        # point is clicked
        else:
            for idx, radi_val in enumerate(self.par_val_radi):
                if ((self.ms_click[0] < (self.par_val_radi[idx]) + 3) and
                    (self.ms_click[0] > (self.par_val_radi[idx]) - 3) and
                    (self.ms_release[0] is None)):
                    dy = self.ms_motion[0] - self.par_vals[idx]
                    self.par_vals[idx] += dy
                    bottom, top = self.ax.get_ylim()
                    self.ax.clear()
                    # self.ax.set_xlim(self.x_scale[0], self.x_scale[1])
                    max_yvalue = max(self.par_vals)
                    min_yvalue = min(self.par_vals)

                    if self._almost_equal(self.ms_motion[0], min_yvalue):
                        bottom = min_yvalue - (0.3*(max_yvalue-min_yvalue))
                        top = max_yvalue + (0.1*(max_yvalue-min_yvalue))
                    elif self._almost_equal(self.ms_motion[0], max_yvalue):
                        top = max_yvalue + (0.3*(max_yvalue-min_yvalue))
                        bottom = min_yvalue - (0.1*(max_yvalue-min_yvalue))

                    self.ax.set_ylim(bottom, top)
                    self.ax.set_xlabel("RADI (arcsec)")
                    self.ax.set_ylabel(self.par + "( "+self.unit_meas+ " )")
                    self.ax.plot(self.par_val_radi, self.par_vals, '--bo')
                    self.ax.set_xticks(self.par_val_radi)
                    self.canvas.draw()
                    self.key = "No"
                    break
