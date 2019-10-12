#!/usr/bin/env python
#########################################################################################
# Author: Samuel (samueltwum1@gmail.com) with MSc supervisors                           #
# Copyright 2019 Samuel N. Twum                                                         #
#                                                                                       #
# MIT license - see LICENSE.txt for details                                             #
#########################################################################################

"""
This is the GUI (PyQt5) implementation of TiRiFiC which allows users to model tilted-ring 
parameters before fitting. Instructions on how TiRiFiC works and everything you need to
know about it can be found on the github pages:
http://gigjozsa.github.io/tirific/

"""

import os, re, shutil, signal, subprocess, time, tempfile
from decimal import Decimal
from math import ceil
from subprocess import Popen as run
from threading import Thread, Event
import numpy as np

from PyQt5 import QtCore, QtWidgets

from graph_widget import GraphWidget
from parameter_specification_widget import ParamSpec
from scale_manager_widget import ScaleManager


"""
globals
"""

# tilted-ring parameter whose graph widget window has focus
curr_par = None
# determines whether a graph widget is being inserted or added
selected_option = None
# a list of tilted ring parameters and the respective units
fit_par = {"VROT":"km s-1",
           "SBR":"Jy km s-1 arcsec-2",
           "INCL":"degrees",
           "PA":"degrees",
           "RADI":"arcsec", 
           "Z0":"arcsec",
           "SDIS":"km s-1",
           "XPOS":"degrees",
           "YPOS":"degrees",
           "VSYS":"km s-1",
           "DVRO":"km s-1 arcsec-1",
           "DVRA":"km s-1 arcsec-1",
           "VRAD":"km s-1"}

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


class TimerThread(Thread):
    """starts a thread and stops when the program closes"""
    stopped = None
    func = None
    prog_pid = None
    tmp_file = None
    def_file = None

    def __init__(self):
        super(TimerThread, self).__init__(name="TimerThread")

    def restore_file_name(self):
        """Renames the def file to its original name
        
        Notes
        -----
        The save_aas function renames the deffile name to be the name of 
        the temporary def file. This function is called when the open text
        editor command is triggered. Despite the new file created, we still
        want to keep the name of the original file in self.file_name
        """
        pass

    def run(self):
        wait_period = 0.2 # time in seconds
        while not self.stopped.wait(wait_period):
            proc1 = run(["ps", "ax"], stdout=subprocess.PIPE)
            proc2 = run(["grep", self.prog_pid], stdin=proc1.stdout,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = proc2.communicate()[0].split()
            # update the viewgraph with edits from text file, else
            # stop thread if program is no longer running
            if (len(out) > 0) and (self.prog_pid == out[0]):
                self.func()
            else:
                self.stopped.set()
                os.remove(self.def_file)
                shutil.move(self.tmp_file.name, self.def_file)
                self.restore_file_name()
                # self.logger.debug("Sync between graph and text file stopped")


class MainWindow(QtWidgets.QMainWindow, TimerThread):
    run_count = 0
    key = "Yes"
    loops = 0
    n_cols = 1; n_rows = 4
    INSET = "None"
    par = ["VROT", "SBR", "INCL", "PA"]
    tmp_def_file = tempfile.NamedTemporaryFile()
    progress_path = ""
    file_name = ""
    original_name = ""
    graph_widgets = []
    scroll_width = 0; scroll_height = 0
    before = 0
    y_precision = {}
    x_precision = 0
    NUR = 0
    data = []
    par_vals = {}
    history_list = {}
    x_scale = [0, 0]
    y_scale = {"VROT":[0, 0]}
    ms_click = [-5]
    ms_release = ["None"]
    ms_motion = [-5]

    def __init__(self, logger):
        super(MainWindow, self).__init__()
        self.logger = logger
        self.init_ui()
        # self.logger.info("Window initialisation completed without errors")


    def init_ui(self):
        self.showMaximized()
        self.setWindowTitle("TiRiFiG")
        # define a widget sitting in the main window where all other widgets will live
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        # make this new widget have a vertical layout
        vertical_layout = QtWidgets.QVBoxLayout()
        central_widget.setLayout(vertical_layout)
        # add the buttons and the scroll area which will have the graph widgets
        # open button
        btn_open = QtWidgets.QPushButton("&Open File")
        btn_open.setFixedSize(80, 30)
        btn_open.setToolTip("Open .def file")
        btn_open.clicked.connect(self.open_def)
        vertical_layout.addWidget(btn_open)
        # scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        # the scroll area needs a widget to be placed inside of it which will hold the content
        # create one and let it have a grid layout
        self.scroll_area_content = QtWidgets.QWidget()
        self.scroll_grid_layout = QtWidgets.QGridLayout()
        self.scroll_area_content.setLayout(self.scroll_grid_layout)
        scroll_area.setWidget(self.scroll_area_content)
        vertical_layout.addWidget(scroll_area)
        self.create_actions()
        self.create_menus()

    def create_actions(self):
        self.exit_action = QtWidgets.QAction("&Exit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Leave the app")
        self.exit_action.triggered.connect(self.quit_app)

        self.open_file = QtWidgets.QAction("&Open File", self)
        self.open_file.setShortcut("Ctrl+O")
        self.open_file.setStatusTip("Load .def file to be plotted")
        self.open_file.triggered.connect(self.open_def)

        self.save_changes = QtWidgets.QAction("&Save", self)
        self.save_changes.setStatusTip("Save changes to .def file")
        self.save_changes.triggered.connect(self.save_all)

        self.save_as = QtWidgets.QAction("&Save as...", self)
        self.save_as.setStatusTip("Create another .def file with current "
                                  "paramater values")
        self.save_as.triggered.connect(self.save_as_all)

        self.undo_action = QtWidgets.QAction("&Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.setStatusTip("Undo last action")
        self.undo_action.triggered.connect(self.undo_command)

        self.redo_action = QtWidgets.QAction("&Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.setStatusTip("Redo last action")
        self.redo_action.triggered.connect(self.redo_command)

        self.open_text_editor = QtWidgets.QAction("&Open Text Editor...", self)
        self.open_text_editor.setStatusTip("View the current open .def file in "
                                           "preferred text editor")
        self.open_text_editor.triggered.connect(self.open_editor)

        self.start_tirific = QtWidgets.QAction("&Start TiriFiC", self)
        self.start_tirific.setStatusTip("Starts TiRiFiC from terminal")
        self.start_tirific.triggered.connect(self.run_tirific)

        self.win_spec = QtWidgets.QAction("&Window Specification", self)
        self.win_spec.setStatusTip("Determines the number of rows and columns in a plot")
        self.win_spec.triggered.connect(self.set_row_col)

        self.scale_man = QtWidgets.QAction("&Scale Manager", self)
        self.scale_man.setStatusTip("Manages behaviour of scale and min and max values")
        self.scale_man.triggered.connect(self.create_scale_manager)

        self.para_def = QtWidgets.QAction("&Parameter Definition", self)
        # self.para_def.setStatusTip('Determines which parameter is plotted')
        self.para_def.triggered.connect(self.append_parameter_dialog)

    def create_menus(self):
        main_menu = self.menuBar()

        self.file_menu = main_menu.addMenu("&File")
        self.file_menu.addAction(self.open_file)
        self.file_menu.addAction(self.undo_action)
        self.file_menu.addAction(self.redo_action)
        self.file_menu.addAction(self.save_changes)
        self.file_menu.addAction(self.save_as)
        self.file_menu.addAction(self.exit_action)

        # edit_menu = main_menu.addMenu("&Edit")

        self.run_menu = main_menu.addMenu("&Run")
        self.run_menu.addAction(self.open_text_editor)
        self.run_menu.addAction(self.start_tirific)

        self.pref_menu = main_menu.addMenu("&Preferences")
        self.pref_menu.addAction(self.scale_man)
        self.pref_menu.addAction(self.para_def)
        self.pref_menu.addAction(self.win_spec)

    def quit_app(self):
        # kill the text editor if it is running
        # check if text editor was opened in program run time
        if self.prog_pid:
            proc1 = run(["ps", "ax"], stdout=subprocess.PIPE)
            proc2 = run(["grep", self.prog_pid], stdin=proc1.stdout,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = proc2.communicate()[0].split()
            # update the viewgraph with edits from text file, else
            # stop thread if program is no longer running
            if (len(out) > 0) and (self.prog_pid == out[0]):
                os.kill(int(self.prog_pid), signal.SIGKILL)
        # wait a while to make the thread's run method to clean up
        time.sleep(0.5)
        QtWidgets.qApp.quit()

    def clean_up(self):

        # FIXME(Samuel 11-06-2018): Find a way to do this better
        self.run_count = 0
        self.key = "Yes"
        self.n_cols = 1; self.n_rows = 4
        self.INSET = "None"
        self.par = ["VROT", "SBR", "INCL", "PA"]
        self.unit_meas = ["km/s", "Jy km/s/sqarcs", "degrees", "degrees"]
        # FIXME use Lib/tempfile.py to create temporary file
        self.tmp_def_file = os.getcwd() + "/tmpDeffile.def"
        self.file_name = ""
        self.graph_widgets = []
        self.scroll_width = 0; self.scroll_height = 0
        self.before = 0
        self.y_precision = 0
        self.x_precision = 0
        self.NUR = 0
        self.data = []
        self.par_vals = {}
        self.history_list = {}
        self.x_scale = [0, 0]
        self.y_scale = {"VROT":[0, 0]}
        self.ms_click = [-5]
        self.ms_release = ["None"]
        self.ms_motion = [-5]

        self.init_ui()

    def get_data(self):
        """Loads data from specified .def file

        Returns
        -------
        data : list
            The text found in each line of the opened file

        Notes
        -----
        data will be a none type variable if the file_name is invalid or no file is chosen
        """

        # stores file path of .def to file_name variable after user selects file in open
        # dialog box
        # TODO (Samuel 28-11-2018): If cancel is selected then suppress the message in try/except below
        self.file_name, _filter = QtWidgets.QFileDialog.getOpenFileName(self, "Open .def File", "~/",
                                                                        ".def Files (*.def)")

        # assign texts of read lines to data variable if file_name is exists, else assign
        # None
        try:
            with open(self.file_name) as f:
                data = f.readlines()
        except:
            # self.logger.debug("Error reading selected paramater file: {}".format(self.file_name))
            QtWidgets.QMessageBox.information(self, "Information",
                                              "Empty/Invalid file specified")
            return
        else:
            self.original_name = self.file_name
            return data

    def str_type(self, var):
        """Determines the data type of a variable

        ParametersError reading selected paramater file
        ----------
        var : int|float|string
            variable holding the values

        Returns
        -------
        data type : string
            value returned is either int, float or str
        """
        # why are you putting this in a try-except block
        try:
            if int(var) == float(var):
                return "int"
        except:
            try:
                float(var)
                return "float"
            except:
                return "str"

    def num_precision(self, data):
        """Determines the highest floating point precision of data points

        Parameters
        ----------
        data : list
            list of scientific values of type string
            e.g. x = ["20.00E4","55.0003E-4",...]

        Returns
        -------
        precision : int      
        """
        dec_points = []
        # ensure values from list to are converted string
        for idx, sci_num in enumerate(data):
            sci_num = str(sci_num)       
            val = sci_num.split(".")
            # check val has decimal & fractional part and append 
            # length of numbers of fractional part
            if len(val) == 2:
                dec_points.append(len(val[1].split("E")[0]))

        # assign greatest precision in dec_points to class variables handling precision
        if len(dec_points) == 0:
            return 0
        else:
            return max(dec_points)

    def get_parameter_values(self, data):
        """Fetches data points of specified parameter

        Parameters
        ----------
        data : list
            list containing texts of each line loaded from .def file

        Notes
        -----
        The values appearing after the '=' symbol of the parameter specified in search
        key. If search key isn't found, zero values are returned.

        The data points for the specific parameter value are located and converted
        from string to float data types for plotting and other data manipulation
        """
        # search through fetched data for expressions matching 
        # "PAR =" or "PAR = " or "PAR=" or "PAR= "
        # TODO 26/08/19 (Sam): will be nice to use regex for the search

        global fit_par

        # I need NUR value first that's why it's in a different loop
        for i in data:
            line_vals = i.split("=")
            if len(line_vals) > 1:
                line_vals[0] = "".join(line_vals[0].split())
                if line_vals[0].upper() == "NUR":
                    par_vals = line_vals[1].split()
                    self.NUR = int(par_vals[0])
                    break

        for each_line in data:
            line_vals = each_line.split("=")
            if len(line_vals) > 1:
                line_vals[0] = "".join(line_vals[0].split())
                par_vals = line_vals[1].split()

                if line_vals[0].upper() == "INSET":
                    self.INSET = ''.join(line_vals[1].split())
                elif line_vals[0].upper() == "LOOPS":
                    self.loops = int(par_vals[0])
                else:
                    if (len(par_vals) > 0 and not self.str_type(par_vals[0]) == "str" and
                            not self.str_type(par_vals[-1]) == "str" and
                            not self.str_type(par_vals[len(par_vals) / 2]) == "str"):
                        if (len(par_vals) == self.NUR or line_vals[0].upper() in
                                fit_par.keys()):
                            if line_vals[0].upper() == "RADI":
                                self.x_precision = self.num_precision(par_vals[:])
                            else:
                                self.y_precision[str.upper(line_vals[0])] = (
                                    self.num_precision(par_vals[:]))
                            for idx, each_value in enumerate(par_vals):
                                par_vals[idx] = float(Decimal(each_value))
                            self.par_vals[str.upper(line_vals[0])] = par_vals[:]
        # self.logger.info("Parameter values have been retrieved and ready for plotting")

    def open_def(self):
        """Opens data, gets parameter values, sets precision and sets scale

        Notes
        -----
        Makes function calls to get_data and get_parameter_values functions, assigns
        values to dictionaries par_vals and history_list and defines
        the x-scale and y-scale for plotting on viewgraph
        """
        global fit_par
        data = self.get_data()
        try:
            self.get_parameter_values(data)
        except:
            # self.logger.debug("The tilted-ring parameters could not be retrieved from the {}"
                            #  .format(self.file_name))
            QtWidgets.QMessageBox.information(self, "Information",
                                              "Tilted-ring parameters not retrieved")
        else:
            self.data = data
            if self.run_count > 0:
                # FIXME reloading another file on already opened not properly working
                # user has to close open window and reopen file for such a case
                QtWidgets.QMessageBox.information(self, "Information",
                                                  "Close app and reopen to load file. Bug "
                                                  "being fixed")
                # self.clean_up()
                # FIXME (Samuel 11-06-2018): Find a better way to do this
                # self.data = data
                # self.get_parameter_values(self.data)
            else:
                # defining the x scale for plotting
                # this is the min/max + 10% of the difference between the min and max
                min_max_diff = max(self.par_vals["RADI"]) - min(self.par_vals["RADI"])
                percentage_of_min_max_diff = 0.1 * min_max_diff
                lower_bound = min(self.par_vals["RADI"]) - percentage_of_min_max_diff
                upper_bound = max(self.par_vals["RADI"]) + percentage_of_min_max_diff
                self.x_scale = [int(ceil(lower_bound)), int(ceil(upper_bound))]
                
                self.scroll_width = self.scroll_area_content.width()
                self.scroll_height = self.scroll_area_content.height()

                # make a dict to save the graph widgets to be plotted
                # note that this approach will require another loop.
                # Not ideal but it gets the job done for now.
                g_w_to_plot = {}
                # ensure there are the same points for parameters as there are for RADI as
                # specified in NUR parameter
                for key, val in self.par_vals.items():
                    diff = self.NUR - len(val)
                    if key == "RADI": #use this implementation in other diff checkers
                        if diff == self.NUR:
                            for j in np.arange(0.0, (int(diff) * 40.0), 40):
                                self.par_vals[key].append(j)
                        elif diff > 0 and diff < self.NUR:
                            for j in range(int(diff)):
                                self.par_vals[key].append(self.par_vals[key][-1] + 40.0)
                        continue
                    else:
                        if diff == self.NUR:
                            for j in range(int(diff)):
                                self.par_vals[key].append(0.0)
                        elif diff > 0 and diff < self.NUR:
                            for j in range(int(diff)):
                                self.par_vals[key].append(val[-1])

                    self.history_list.clear()
                    self.history_list[key] = [self.par_vals[key][:]]

                    min_max_diff = max(self.par_vals[key]) - min(self.par_vals[key])
                    percentage_of_min_max_diff = 0.1 * min_max_diff
                    lower_bound = min(self.par_vals[key]) - percentage_of_min_max_diff
                    upper_bound = max(self.par_vals[key]) + percentage_of_min_max_diff
                    if (max(self.par_vals[key]) == min(self.par_vals[key])):
                        self.y_scale[key] = [lower_bound/2, upper_bound*1.5]
                    else:
                        self.y_scale[key] = [lower_bound, upper_bound]
                    
                    unit = fit_par[key] if key in fit_par.keys() else ""
                    self.graph_widgets.append(GraphWidget(self.x_scale,
                                                      self.y_scale[key][:],
                                                      unit, key,
                                                      self.par_vals[key][:],
                                                      self.par_vals["RADI"][:],
                                                      self.history_list[key][:],
                                                      self.key, self.x_precision,
                                                      self.y_precision[key],
                                                      self.logger))
                    self.graph_widgets[-1].btn_add_param.clicked.connect(
                        self.graph_widgets[-1].change_global)
                    self.graph_widgets[-1].btn_add_param.clicked.connect(
                        self.insert_parameter_dialog)
                    self.graph_widgets[-1].btn_edit_param.clicked.connect(
                        self.graph_widgets[-1].change_global)
                    self.graph_widgets[-1].btn_edit_param.clicked.connect(
                        self.change_parameter_dialog)
                    # TODO we should also probably set the minimum size for the scroll layout
                    self.graph_widgets[-1].setMinimumSize(self.scroll_width/2, self.scroll_height/2)
                    if key in self.par:
                        g_w_to_plot[key] = self.graph_widgets[-1]

                # retrieve the values in order and build a list of ordered key-value pairs
                ordered_dict_items = [(key, g_w_to_plot[key]) for key in self.par]
                for idx, items in enumerate(ordered_dict_items):
                    graph_widget = items[1] # what does 1 represent
                    self.scroll_grid_layout.addWidget(graph_widget, idx, 0)
                del g_w_to_plot, ordered_dict_items
                self.run_count += 1
                # self.logger.debug("The tilted-ring parameters retrieved from successfully")

    def undo_command(self):
        global curr_par
        for idx, gw in enumerate(self.graph_widgets):
            if gw.par == curr_par:
                gw.undo_key()
                break

    def redo_command(self):
        global curr_par
        for idx, gw in enumerate(self.graph_widgets):
            if gw.par == curr_par:
                gw.redo_key()
                break

    def set_row_col(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Window number Input Dialog",
                                                  "Specify the number of rows and columns (5,5):")
        if ok:
            if text:
                text = str(text)
                text = text.split(",")
                self.n_rows = int(text[0])
                self.n_cols = int(text[1])
                if (self.n_rows * self.n_cols) >= len(self.par):
                    # clear the existing graph objects
                    item_count = self.scroll_grid_layout.count()
                    for i in range(item_count):
                        widget_to_remove = self.scroll_grid_layout.itemAt(0).widget()
                        self.scroll_grid_layout.removeWidget(widget_to_remove)
                        widget_to_remove.close()

                    # get only the plot widgets for the we want to plot: defined in par
                    g_w_to_plot = [gwObject for gwObject in self.graph_widgets
                                   if gwObject.par in self.par]
                    # retrieve the parameter for each graph widget in the g_w_to_plot list
                    # self.par for instance contains [VROT, SBR, PA and INCL]
                    # g_w_pars will also contain a list of parameters but in the order
                    # of self.graph_widgets e.g. new_par = [PA, SBR, VROT, INCL].
                    # Create a new sorted list of graph widgets based as below:
                    # loop through self.par [VROT, SBR, PA, INCL]grab the index of the 
                    # parameter in the new_par list [PA, SBR, VROT, INCL] i.e. 
                    # index(VROT) in new_par list: 2
                    # index(SBR) in new_par list: 1
                    # index(PA) in new_par list: 0
                    # index(INCL) in new_par list: 3
                    # Use these indexes to get a sorted list of graph widgets
                    # from g_w_to_plot for the plotting
                    g_w_pars = [g_w.par for g_w in g_w_to_plot]
                    sorted_g_w_to_plot = []
                    for par in self.par:
                        idx = g_w_pars.index(par)
                        sorted_g_w_to_plot.append(g_w_to_plot[idx])
                    # delete the unordered list of graph widgets
                    del g_w_to_plot

                    counter = 0
                    for i in range(self.n_rows):
                        for j in range(self.n_cols):
                            self.scroll_grid_layout.addWidget(
                                sorted_g_w_to_plot[counter], i, j)
                            # call the show method on the graphWidget object in order to
                            # display it
                            sorted_g_w_to_plot[counter].show()
                            # don't bother iterating to plot if all the parameters have been
                            # plotted else you'll get an error
                            if counter == len(sorted_g_w_to_plot) -1 :
                                break
                            counter += 1
                    del sorted_g_w_to_plot
                else:
                    # self.logger.debug("Product of rows and columns did not match the "
                                    #   "currently plotted parameters")
                    QtWidgets.QMessageBox.information(self, "Information",
                                                      "Product of rows and columns should"
                                                      " match the current number of parameters"
                                                      " on viewgraph")

    def save_file(self, new_vals, search_key, unit_measurement, x_precision, y_precision):
        """Save changes made to data points to .def file

        Parameters
        ----------
        new_vals : list
            list of new values
        search_key : str
            tilted ring parameter
        unit_measurement : str
        x_precision : int
        y_precision : int

        Notes
        -----
        The .def file would be re-opened and updated per the new values that
        are contained in the par_val* variable
        """

        # get the new values and format it as e.g. [0 20 30 40 50...]
        txt = ""
        for val in new_vals:
            if search_key == "RADI":
                txt = txt+" " +'{0:.{1}E}'.format(val, x_precision)
            else:
                txt = txt+" " +'{0:.{1}E}'.format(val, y_precision)

        # FIXME (11-06-2018) put this block of code in a try except block
        tmp_file = []
        with open(self.file_name, "a") as f:
            status = False
            for each_line in self.data:
                line_vals = each_line.split("=")
                if len(line_vals) > 1:
                    line_vals[0] = "".join(line_vals[0].split())
                    if search_key == line_vals[0]:
                        txt = "    "+search_key+"="+txt+"\n"
                        tmp_file.append(txt)
                        status = True
                    else:
                        tmp_file.append(each_line)
                else:
                    tmp_file.append(each_line)

            if not status:
                tmp_file.append("# "+search_key+" parameter in "+unit_measurement+"\n")
                txt = "    "+search_key+"="+txt+"\n"
                tmp_file.append(txt)

            f.seek(0)
            f.truncate()
            for line in tmp_file:
                f.write(line)

            self.data = tmp_file[:]

    def save_all(self):
        """Save changes made to data point to .def file for all parameters
        """
        for gw in self.graph_widgets:
            self.save_file(gw.par_vals, gw.par, gw.unit_meas, gw.x_precision, gw.y_precision)

        # self.logger.info("Changes saved successfully to current file")

        QtWidgets.QMessageBox.information(self, "Information",
                                          "Changes successfully written to file")

    def save_aas(self, file_name, new_vals, search_key, unit_measurement, x_precision,
               y_precision):
        """Creates a new .def file with the specified file path

        Parameters
        ----------
        file_name : str
            file path where new file should be saved to
        new_vals : list
            list of new values
        search_key : str
            tilted ring parameter
        unit_measurement : str
        x_precision : int
        y_precision : int
        """
        # get the new values and format it as [0 20 30 40 50...]
        txt = ""
        for val in new_vals:
            if search_key == "RADI":
                txt = txt+" " +"{0:.{1}E}".format(val, x_precision)
            else:
                txt = txt+" " +"{0:.{1}E}".format(val, y_precision)

        tmp_file = []

        if file_name:
            with open(file_name, "a") as f:
                status = False
                for each_line in self.data:
                    line_vals = each_line.split("=")
                    if len(line_vals) > 1:
                        line_vals[0] = "".join(line_vals[0].split())
                        if search_key == line_vals[0]:
                            txt = "    "+search_key+"="+txt+"\n"
                            tmp_file.append(txt)
                            status = True
                        else:
                            tmp_file.append(each_line)
                    else:
                        tmp_file.append(each_line)

                if not status:
                    tmp_file.append("# "+search_key+" parameter in "+unit_measurement+"\n")
                    txt = "    "+search_key+"="+txt+"\n"
                    tmp_file.append(txt)

                f.seek(0)
                f.truncate()
                for line in tmp_file:
                    f.write(line)

                self.data = tmp_file[:]
                self.file_name = file_name

    def save_as_all(self):
        """Creates a new .def file for all parameters in current .def file opened
        """
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, "Save .def file as ",
                                                          os.getcwd(),
                                                          ".def Files (*.def)")
        for gw in self.graph_widgets:
            self.save_aas(file_name, gw.par_vals, gw.par, gw.unit_meas, gw.x_precision,
                          gw.y_precision)

        # self.logger.info("Changes saved successfully to new file")

        QtWidgets.QMessageBox.information(self, "Information", "File Successfully Saved")

    def change_data(self, file_name):
        global fit_par
        with open(file_name) as f:
            self.data = f.readlines()

        self.get_parameter_values(self.data)

        for trp in fit_par.keys():
            for gw in self.graph_widgets:
                if gw.par == trp:
                    gw.par_vals = self.par_vals[trp][:]
                    gw.par_val_radi = self.par_vals["RADI"][:]

        # FIXME(Samuel 11-06-2018):
        # the comments below will probably be important to keep/implement
        # it's possible that the user will delete some points in the .def file

        # ensure there are the same points for parameter as there are for RADI as
        # specified in NUR parameter
        # diff = self.NUR-len(self.par_vals[self.par])
        # lastItemIndex = len(self.par_vals[self.par])-1
        # if diff == self.NUR:
        #    for i in range(int(diff)):
        #        self.par_vals[self.par].append(0.0)
        # elif diff > 0 and diff < self.NUR:
        #    for i in range(int(diff)):
        #        self.par_vals[self.par].append(self.par_vals[self.par][lastItemIndex])

        for gw in self.graph_widgets:
            if not gw.history_list[len(gw.history_list)-1] == gw.par_vals[:]:
                gw.history_list.append(gw.par_vals[:])
            gw.first_plot()

    def animate(self):
        if os.path.isfile(self.tmp_def_file.name):
            after = os.stat(self.tmp_def_file.name).st_mtime
            if self.before != after:
                self.before = after
                self.change_data(self.tmp_def_file.name)

    def rename_file(self):
        self.file_name = self.original_name

    def open_editor(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Text Editor Input Dialog",
                                                  "Enter text editor :")
        if ok:
            for gw in self.graph_widgets:
                self.save_aas(self.tmp_def_file.name, gw.par_vals, gw.par, gw.unit_meas,
                              gw.x_precision, gw.y_precision)

            if text:
                program_name = str(text)
                reply = QtWidgets.QMessageBox.information(self, "Information",
                                                          "To see change in graph, save changes to the file")
                if reply:
                    try:
                        prog_pid = run([program_name, self.tmp_def_file.name]).pid
                    except OSError:
                        # self.logger.debug("{} is not installed or configured.".format(program_name))
                        QtWidgets.QMessageBox.information(self, "Information",
                                                        "{} is not installed or configured"
                                                        " properly on this system.".format(program_name))
                    else:
                        # assign current modified time of temporary def file to before
                        self.before = os.stat(self.tmp_def_file.name).st_mtime
                        stop_event = Event()
                        # set the values of the inherited values from TimerThread
                        self.stopped = stop_event
                        self.func = self.animate
                        self.prog_pid = str(prog_pid)
                        self.tmp_file = self.tmp_def_file
                        self.def_file = self.original_name
                        self.restore_file_name = self.rename_file
                        #start the thread
                        self.start()
                        # self.logger.debug("Sync between graph and text file started")

    def create_scale_manager(self):
        self.sm = ScaleManager(self.x_scale, self.graph_widgets, self.logger)
        self.sm.show()

    def add_parameter(self):
        global curr_par, fit_par, selected_option
        user_input = self.ps.parameter.currentText()
        # check if the inputted parameter value has its plot displayed
        if (user_input and
            not str.upper(str(user_input)) in self.par):
            # the graph for the new tilted ring parameter will be inserted right after
            # the tilted ring parameter which has focus (defined in curr_par)
            # if no tilted ring parameter has focus then the graph of the new tilted ring
            # parameter will be placed in the last position
            if curr_par:
                if selected_option == "insert":
                    par_index = self.par.index(curr_par)
                    par_index += 1
                else:
                    raise ValueError ("Expecting an insert option but got {}".
                                      format(selected_option))
            else:
                if selected_option == "append":
                    par_index = len(self.par)
                else:
                    raise ValueError("Expecting an append option but got {}".
                                     format(selected_option))
            self.par.insert(par_index,
                            str.upper(str(user_input)))

            unit_meas = str(self.ps.unit_measurement.text())

            # only parameters in the self.par variable have their plots displayed.
            # other parameters specified in the .def file each have a graph widget
            # object saved as part of the graph_widgets list. Handle cases where new parameter
            # to be plotted doesn't exist in the expected tilted ring parameters (defined
            # as fit_par) or wasn't defined in the .def file.
            tilted_ring_par = self.par[par_index]
            if tilted_ring_par not in fit_par.keys():
                fit_par[tilted_ring_par] = unit_meas
            # check if new tilted ring parameter isn't already in the list of graph_widgets
            list_of_t_r_p = [gwObject.par for gwObject in self.graph_widgets]
            if tilted_ring_par not in list_of_t_r_p:
                zero_vals = [0.0] * self.NUR
                self.par_vals[tilted_ring_par] = zero_vals[:]
                del zero_vals
                self.history_list[tilted_ring_par] = (
                    [self.par_vals[tilted_ring_par][:]])
                self.y_scale[tilted_ring_par] = [-100, 100]
                fit_par[tilted_ring_par] = unit_meas
                self.graph_widgets.insert(par_index,
                                          GraphWidget(self.x_scale,
                                                      self.y_scale[tilted_ring_par],
                                                      unit_meas,
                                                      tilted_ring_par,
                                                      self.par_vals[tilted_ring_par],
                                                      self.par_vals["RADI"],
                                                      self.history_list[tilted_ring_par],
                                                      "Yes",
                                                      self.x_precision,
                                                      1,
                                                      self.logger))
                self.graph_widgets[par_index].setMinimumSize(self.scroll_width/2,
                                                             self.scroll_height/2)
                self.graph_widgets[par_index].btn_add_param.clicked.connect(
                    self.graph_widgets[par_index].change_global)
                self.graph_widgets[par_index].btn_add_param.clicked.connect(
                    self.insert_parameter_dialog)
                self.graph_widgets[par_index].btn_edit_param.clicked.connect(
                    self.graph_widgets[par_index].change_global)
                self.graph_widgets[par_index].btn_edit_param.clicked.connect(
                    self.change_parameter_dialog)

                del list_of_t_r_p

            self.n_rows = self.scroll_grid_layout.rowCount()
            self.n_cols = self.scroll_grid_layout.columnCount()
            item_count = self.scroll_grid_layout.count()
            if selected_option == "add":
                g_w_to_plot = [gw for gw in self.graph_widgets
                               if gw.par == tilted_ring_par][0]
                last_item_index = item_count - 1
                graph_widget_position = (
                    self.scroll_grid_layout.getItemPosition(last_item_index))
                row_number = graph_widget_position[0]
                column_number = graph_widget_position[1]
                if column_number < self.n_cols:
                    self.scroll_grid_layout.addWidget(
                        g_w_to_plot, row_number, column_number + 1)
                else:
                    if row_number == self.n_rows:
                        self.n_rows += 1 # does this even matter
                    self.scroll_grid_layout.addWidget(g_w_to_plot, row_number + 1, 0)

                del g_w_to_plot
            else:
                self.n_rows += 1

                for i in range(item_count):
                    widget_to_remove = self.scroll_grid_layout.itemAt(0).widget()
                    self.scroll_grid_layout.removeWidget(widget_to_remove)
                    widget_to_remove.close()

                # get only the plot widgets for the we want to plot: defined in par
                    g_w_to_plot = [gwObject for gwObject in self.graph_widgets
                                   if gwObject.par in self.par]
                    g_w_pars = [g_w.par for g_w in g_w_to_plot]
                    sorted_g_w_to_plot = []
                    for par in self.par:
                        idx = g_w_pars.index(par)
                        sorted_g_w_to_plot.append(g_w_to_plot[idx])
                    # delete the unordered list of graph widgets
                    del g_w_to_plot

                    counter = 0
                    for i in range(self.n_rows):
                        for j in range(self.n_cols):
                            self.scroll_grid_layout.addWidget(
                                sorted_g_w_to_plot[counter], i, j)
                            # call the show method on the graphWidget object in order to
                            # display it
                            sorted_g_w_to_plot[counter].show()
                            # don't bother iterating to plot if all the parameters have been
                            # plotted else you'll get an error
                            if counter == len(sorted_g_w_to_plot) - 1 :
                                break
                            counter += 1
                    del sorted_g_w_to_plot

            self.ps.close()

    def change_parameter(self):
        global curr_par, fit_par
        par_index = self.par.index(curr_par)
        user_input = self.ps.parameter.currentText()
        if (user_input and
            not str.upper(str(user_input)) in self.par):
            try:
                self.par_vals[self.par[par_index]]
            except KeyError:
                # self.logger.debug("Inputted parameter ({}) is not known.".format(user_input))
                QtWidgets.QMessageBox.information(self, "Information",
                                                  "This parameter does not exist. Add to"
                                                  " view it.")
            else:
                user_input = str.upper(str(user_input))
                self.par[par_index] = user_input
                unit_meas = str(self.ps.unit_measurement.text())
                if user_input not in fit_par.keys():
                    fit_par[user_input] = unit_meas
                    for graph_widget in self.graph_widgets:
                        if graph_widget.par == user_input:
                            graph_widget.unit_meas = unit_meas
                            break

                g_w_to_plot = [gwObject for gwObject in self.graph_widgets
                               if gwObject.par == user_input]
                curr_par_position_on_layout = (
                    self.scroll_grid_layout.getItemPosition(par_index))
                row_number = curr_par_position_on_layout[0]
                column_number = curr_par_position_on_layout[1]
                widget_to_remove = self.scroll_grid_layout.itemAt(par_index).widget()
                self.scroll_grid_layout.removeWidget(widget_to_remove)
                widget_to_remove.close() # will this make me lose values of tilted-ring parameters?
                self.scroll_grid_layout.addWidget(g_w_to_plot[0], row_number,
                                                  column_number)
                # TODO 03/07/19 (sam): will be nice to add a little close icon on each graph widget
                # and then implement removeWidget and close functions when it's clicked
                self.ps.close()
    
    def add_parameter_dialog(self, opt, title):
        global selected_option
        selected_option = opt
        val = []
        for key in self.par_vals:
            if key in self.par:
                continue
            else:
                val.append(key)
        self.ps = ParamSpec(val, title, self.logger)
        self.ps.add_parameter = self.add_parameter
        self.ps.show()
        self.ps.btn_ok.clicked.connect(self.add_parameter)
        self.ps.btn_cancel.clicked.connect(self.ps.close)

    def append_parameter_dialog(self):
        selected_option = "append"
        title = "Append Parameter"
        self.add_parameter_dialog(selected_option, title)

    def insert_parameter_dialog(self):
        selected_option = "insert"
        title = "Insert Parameter"
        self.add_parameter_dialog(selected_option, title)

    def change_parameter_dialog(self):
        val = []
        for key in self.par_vals:
            if key in self.par:
                continue
            else:
                val.append(key)

        self.ps = ParamSpec(val, "Change Parameter", self.logger)
        self.ps.show()
        self.ps.btn_ok.clicked.connect(self.change_parameter)
        self.ps.btn_cancel.clicked.connect(self.ps.close)

    def progress_bar(self, cmd):
        progress = QtWidgets.QProgressDialog("Operation in progress...",
                                             "Cancel", 0, 100)
        progress.setWindowModality(QtCore.Qt.WindowModal)
        progress.setMaximum(self.loops*1e6)
        progress.resize(500, 100)
        prev = 1
        completed = int(prev * 1e6) / 2
        status = "running"
        progress.show()
        time.sleep(10)
        while cmd.poll() is None and status == "running":
            # TODO 11/10/2019 (sam): investigate if it's better to tail the file
            with open(self.progress_path, "r") as f:
                data = f.readlines()
                for each_line in data:
                    line = each_line.split(" ")
                    if "L:" in line[0].upper():
                        count = line[0].split(":")
                        count = count[1].split("/")
                        if int(count[0]) > prev:
                            if int(count[0]) == self.loops:
                                completed += 0.0001
                            else:
                                prev = int(count[0])
                                completed = prev * 1e6
                        else:
                            completed += 0.0001
                    elif "finish" in line[0].lower():
                        status = "finished"
                        progress.setValue(self.loops * 1e6)
                        message = each_line
                        break
            progress.setValue(completed)
            if progress.wasCanceled():
                cmd.kill()
                break
        progress.setValue(self.loops * 1e6)
        # self.logger.debug("TiRiFiC finished and stopped")
        QtWidgets.QMessageBox.information(self, "Information", "Finished")

    def run_tirific(self):
        """Starts TiRiFiC
        """
        # it's possible that the text file is still open when the user runs tirific
        # in this case the original file name must be restored before tirific is called
        if self.file_name != self.original_name:
            os.remove(self.original_name)
            shutil.copy(self.tmp_file.name, self.original_name)
            self.rename_file()
            
        fits_file_path = self.file_name.split("/")
        fits_file_path[-1] = self.INSET
        fits_file_path = "/".join(fits_file_path)
        if os.path.isfile(fits_file_path):
            for gw in self.graph_widgets:
                self.save_file(
                    gw.par_vals, gw.par, gw.unit_meas, gw.x_precision, gw.y_precision)

            tmp_file = []
            with open(self.file_name, "a") as f:
                for each_line in self.data:
                    line_vals = each_line.split("=")
                    if len(line_vals) > 1:
                        line_vals[0] = "".join(line_vals[0].split())
                        if line_vals[0] == "ACTION":
                            tmp_file.append("ACTION = 1\n")
                        elif line_vals[0] == "PROMPT":
                            tmp_file.append("PROMPT = 0\n")
                        elif line_vals[0] == "GR_DEVICE":
                            tmp_file.append(each_line)
                            tmp_file.append("GR_CONT = \n")
                        elif line_vals[0] == "PROGRESSLOG":
                            tmp_file.append("PROGRESSLOG = progress\n")
                        elif line_vals[0] == "GR_CONT":
                            pass
                        else:
                            tmp_file.append(each_line)
                    else:
                        tmp_file.append(each_line)

                f.seek(0)
                f.truncate()
                for line in tmp_file:
                    f.write(line)
            try:
                cmd = run(["tirific", "deffile=", self.file_name])
            except OSError:
                # self.logger.debug("TiRiFiC is not installed on the computer")
                QtWidgets.QMessageBox.information(self, "Information",
                                                  "TiRiFiC is not installed or configured"
                                                  " properly on system.")
            else:
                regex = "^progress$"
                list_of_files = []
                # this may not be the best way to do this but it ensures the right file is used
                # walk through all directories in home looking for files named progress. gather
                # the list of all these files and return the latest file
                for root, dirs, files in os.walk("/home"):
                    for prog_file in files:
                        if re.match(regex, prog_file):
                            list_of_files.append(os.path.join(root, prog_file))

                if list_of_files:
                    self.progress_path = max(list_of_files, key=os.path.getctime)
                else:
                    raise IndexError("No progress file found")
                self.progress_bar(cmd)
        else:
            # self.logger.debug("Fit file is not in the same location as .def file")
            QtWidgets.QMessageBox.information(self, "Information",
                                              "Data cube ("+self.INSET+") specified at INSET parameter"
                                              " doesn't exist in specified directory ("+fits_file_path+").")
