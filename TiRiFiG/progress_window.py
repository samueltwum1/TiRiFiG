#!/usr/bin/env python
#########################################################################################
# Author: Samuel (samueltwum1@gmail.com) with MSc supervisors                           #
# Copyright 2019 Samuel N. Twum                                                         #
#                                                                                       #
# MIT license - see LICENSE.txt for details                                             #
#########################################################################################

import os, re, sys, time
from subprocess import Popen as run, PIPE
from PyQt5 import QtWidgets, Qt
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal, QThread


"""
globals

source: https://stackoverflow.com/questions/21071448/redirecting-stdout-and-stderr-to-a-pyqt4-qtextedit-from-a-secondary-thread
"""

process = None

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

class WriteStream(object):
    """The new Stream Object which replaces the default stream associated with sys.stdout
    This object just puts data in a queue
    """
    def __init__(self,queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)
    
    def flush(self):
        sys.__stdout__.flush()


class MyReceiver(QObject):
    """A QObject (to be run in a QThread) which sits waiting for data to come through a Queue.Queue().
    It blocks until data is available, and one it has got something from the queue, it sends it to the 
    "MainThread" by emitting a Qt Signal
    """
    mysignal = pyqtSignal(str)

    def __init__(self,queue):
        super(MyReceiver, self).__init__()
        self.queue = queue

    @pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)

class Tirific(QObject):
    """QObject (to be run in a QThread) which outputs information
    """
    def __init__(self, file_name, progress, loops):
        super(Tirific, self).__init__()
        self.file_name = file_name
        self.progress = progress
        self.loops = loops

    @pyqtSlot()
    def run(self):
        global process
        try:
            process = run(["tirific", "deffile=", self.file_name], stdout=PIPE)
        except OSError:
            # self.logger.debug("TiRiFiC is not installed on the computer")
            QtWidgets.QMessageBox.information(self, "Information",
                                              "TiRiFiC is not installed or configured"
                                              " properly on system.")
        else:
            self.progress.setMaximum(self.loops*1e6)
            self.progress.resize(500, 100)
            prev = 1
            completed = int(prev * 1e6) / 2
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll():
                    break
                if output:
                    output = output.strip()
                    print(output)
                    # send data to the progress bar
                    # output looks like this 'L:1/1 I:15/5.0E+06 M:04/5.0E+06/145 P:Z0 ... \n'
                    data = output.split()
                    try:
                        # sometimes data is an empty list
                        first_item = data[0]
                    except IndexError:
                        # self.logger.debug("Empty list from split")
                        pass
                    else:
                        if "L:" in first_item.upper():
                            loop_num = first_item.split(":")[1]
                            loop_num = loop_num.split("/")[0]
                            if int(loop_num) > prev:
                                # we may be on the final loop but not yet finished
                                # in such cases just keep increasing completed by a
                                # small figure
                                if int(loop_num) == self.loops:
                                    completed += 0.0001
                                else:
                                    # this will surely make the progress bar moves
                                    prev = int(loop_num)
                                    completed = prev * 1e6
                            else:
                                # just keep incrementing the completed value if
                                # we're on the same loop number
                                completed += 0.0001
                        elif "finish" in first_item.lower():
                            # set the progress bar to its max value
                            self.progress.setValue(self.loops * 1e6)
                            break
                            # self.logger.debug("TiRiFiC finished and stopped")
                        self.progress.setValue(completed)
        
class Progress(QtWidgets.QWidget):
    """application QWidgets containing the textedit to redirect stdout to
    """
    def __init__(self, window_title, logger, file_name, loops):
        super(Progress, self).__init__()
        self.window_title = window_title
        self.logger = logger
        self.file_name = file_name
        self.loops = loops
        self.progress_path = None
        
        self.tirific_display = QtWidgets.QTextEdit()
        self.progress = QtWidgets.QProgressBar()
        self.btn_start = QtWidgets.QPushButton("tirific deffile="+self.file_name)
        self.btn_start.clicked.connect(self.start_thread)

        self.v_box = QtWidgets.QVBoxLayout()
        self.v_box.addWidget(self.progress)
        self.v_box.addWidget(self.tirific_display)
        self.v_box.addWidget(self.btn_start)

        self.setLayout(self.v_box)

        self.setWindowTitle(self.window_title)
        self.setGeometry(300, 300, 300, 150)

        _center(self)
        self.setFocus()
    
    @pyqtSlot(str)
    def append_text(self, text):
        self.tirific_display.moveCursor(Qt.QTextCursor.End)
        self.tirific_display.insertPlainText(text)

    @pyqtSlot()
    def start_thread(self):
        self.thread = QThread()
        self.tirific = Tirific(self.file_name, self.progress, self.loops)
        self.tirific.moveToThread(self.thread)
        self.thread.started.connect(self.tirific.run)
        self.thread.start()
        self.btn_start.setEnabled(False)
