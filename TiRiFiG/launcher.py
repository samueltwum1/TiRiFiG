"""
variables:
    currPar:  tilted-ring parameter whose graph widget window has focus

functions:
    main  : gets the whole thing started
    _center: centering application windows

classes:
    Timer:
        Class variables:  none

        Instance variables:
            t          (int):              the time(ms) when thread begins.
            hFunction  (function):         function to be executed by thread.
            thread     (function):         initialises and start the thread.

        Functions:
            __init__:                      initialises my instance variables.
            handle_function:               calls the function which the thread is run on.
            start:                         starts the thread.
            cancel:                        stops the thread.

    GraphWidget:
        Class variables:
            redo           (list):         the state of some parameters before undo
                                           action.
            mPress         (list):         x-y values of mouse click.
            mRelease       (list):         x-y values of mouse release.
            mMotion        (list):         x-y values of mouse motion.
            mDblPress      (list):         x-y values of mouse double click.

        Instance variables:
            xScale         (list):         upper and lower limit of x-axis.
            yScale         (list):         upper and lower limit of y-axis.
            unitMeas       (string):       the unit measurement for the parameter.
            par            (string):       a specific tilted-ring parameter.
            parVals        (list):         the values of  variable par (y-values on
                                           graph).
            parValRADI     (list):         the values of RADI (x-values on graph).
            historyList    (list):         the values of parVals for each time a point is
                                           shifted.
            key            (bool):         determines whether or not undo/redo key
                                           combination is pressed.
            numPrecisionX  (int):          the precision point to which a x-values are
                                           saved in.
            numPrecisionY  (int):          the precision point to which a y-values are
                                           saved in.
            canvas         (FigureCanvas): figure canvas where the subplots are made.
            btnAddParam    (QPushButton):  add a new plotted parameter to viewgraph.
            btnEditParam   (QPushButton):  change the parameter plotted to another
                                           parameter.

        Functions:
            __init__:                      initialises instance variables and starts
                                           graphWidget.
            changeGlobal:                  change the value of the global parameter
                                           (currPar) to reflect the parameter graphWidget
                                           is plotting.
            getClick:                      assigns x-y value captured from mouse
                                           left-click to mPress list or x-y value of.
                                           captured double click to mDblPress.
            getRelease:                    assigns x-y value captured from mouse release
                                           to mRelease list.
            getMotion:                     assigns x-y value captured from mouse motion
                                           to mMotion list.
            undoKey:                       sends the viewgraph back in history .
            redoKey:                       sends the viewgraph forward in history after
                                           an undo action.
            showInformation:               display information to say history list is
                                           exhausted when too many undo/redo actions are
                                           performed.
            firstPlot:                     produces plot of tilted-ring parameter(s) in
                                           viewgraph after .def file is opened.
            plotFunc:                      produces plot of tilted-ring parameter(s) in
                                           viewgraph when interacting with data points.

    SMWindow:
        Class Variables:  none

        Instance Variables:
            xMinVal        (int):          the value of the min x value of the parameter
                                           in focus.
            xMaxVal        (int):          the value of the max x value of the parameter
                                           in focus.
            par            (list):         list of all tilted-ring parameters
            gwDict         (dictionary):   filtered dictionary with only y-scale
            prevParVal     (string):       previous parameter value.
            parameter      (QComboBox):    drop down of all parameters retrieved from the
                                           variable <par>.
            xLabel         (QLabel):       label for RADI.
            xMin           (QLineEdit):    textbox for entering minimum value for RADI.
            xMax           (QLineEdit):    textbox for entering maximum value for RADI.
            yMin           (QLineEdit):    textbox for entering minimum value for
                                           selected parameter.
            yMax           (QLineEdit):    textbox for entering maximum value for
                                           selected parameter.
            btnUpdate      (QPushButton):  update variables with new values and close
                                           window.
            btnCancel      (QPushButton):  cancel changes and close window.

        Functions:
            __init__:                      initialises instance variables
            onChangeEvent:                 changes values of variables if the current
                                           index of the variable <parameter> changes.

    ParamSpec:
        Class Variables:  none

        Instance Variables:
            par             (list):        list of all tilted-ring parameters from .def
                                           file.
            parameterLabel  (QLabel):      label Parameter
            parameter       (QComboBox):   drop down of all tilted-ring parameters
                                           retrieved from the variable <par>.
            uMeasLabel      (QLabel):      label unit measurement
            unitMeasurement (QLineEdit):   textbox for entering unit measurement for
                                           parameter.
            btnOK           (QPushButton): updates the current parameter plotted to
                                           the new parameter specified.
            btnCancel       (QPushButton): close window

        Functions:
            __init__:                      initialises instance variables

    MainWindow:
        Class Variables:
            key             (string):      determines whether or not undo/redo key has
                                           been pressed.
            ncols           (int):         the number of columns in grid layout where
                                           viewgraphs are created.
            nrows           (int):         the number of rows in grid layout where
                                           viewgraphs are created.
            INSET           (string):      name of data cube retrieved from .def file.
            par             (list):        list of tilted-ring parameters which have
                                           their plots displayed in the viewgraph
            unitMeas        (list):        list of unit measurement for respective
                                           parameters in par list.
            tmpDeffile      (string):      path to temp file which is used to sync entry
                                           of data in text editor to viewgraph.
            gwObjects       (list):        list of graph widget objects each representing
                                           a tilted-ring parameter.
            t               (int):         thread which runs a separate process
                                           (open a text editor).
            scrollWidth     (int):         width of the scroll area.
            scrollHeight    (int):         height of the scroll area.
            before          (int):         time in milliseconds.
            numPrecisionY   (int):         precision in terms of number of decimal points
                                           to which values of parameter are handled.
            numPrecisionX   (int):         precision in terms of number of decimal points
                                           to which values of RADI are handled.
            NUR             (int):         number of rings as indicated in .def file.
            data            (list):        stream of text from .def file.
            parVals         (dictionary):  values of tilted-ring parameters.
            historyList     (dictionary):  values of tilted-ring parameters which have
                                           their values changed.
            xScale          (list):        upper and lower limit values of RADI axis
            yScale          (dictionary):  upper and lower limit values of parameter axis
            mPress          (list):        mouse x,y values when left mouse button is
                                           clicked.
            mRelease        (list):        mouse x,y values when the left mouse button
                                           is released.
            mMotion         (list):        mouse x,y values when mouse is moved.

        Instance Variables:
            cWidget        (QWidget):      central widget (main window).
            btnOpen        (QPushButton):  opens an open dialog box for user to choose
                                           the parameter file.
            scrollArea     (QScrollArea):  scroll area where graph widgets will be
                                           populated.
            mainMenu       (QMenu):        Menu bar with file menu, preference menu and
                                           run menu with each menu having different
                                           actions.

        Functions:
            __init__:                      creates the main window frame and calls the
                                           initUI function.
            initUI:                        initialises instance variables and creates
                                           menus with their actions.
            quitApp:                       closes TiRiFiG.
            cleaunUp:                      initialises class variables.
            getData:                       opens .def file and gets data from the file.
            strType:                       determines the data type of a variable.
            numPrecision:                  determines the floating point precision
                                           currently in .def file and sets it.
            getParameter:                  fetches the data points for the various
                                           tilted-ring parameters.
            openDef:                       calls getData and getParameter and creates the
                                           graph widgets for the default parameters
                                           (VROT, SBR, PA, INCL).
            undoCommand:                   undo last action for the current parameter in
                                           focus.
            redoCommand:                   redo last action for the current parameter in
                                           focus.
            setRowCol:                     specify the number of rows and columns in the
                                           grid layout.
            saveFile:                      save changes to file for one parameter.
            saveAll:                       calls saveFile function to save changes to
                                           file for all parameters.
            saveMessage:                   display information that save was successful.
            saveAs:                        save changes to a new file for one parameter.
            saveAsMessage:                 display information that save as was
                                           successful.
            saveAsAll:                     calls saveAs function to save changes for all
                                           parameters to a new file.
            slotChangeData:                change current viewgraph after making changes
                                           to .def file in text editor.
            animate:                       synchronise actions in text file to viewgraph
                                           with calls to slotChangeData function.
            openEditor:                    open preferred text editor.
            SMobj:                         instantiates the scale manager window and pops
                                           it.
            updateScale:                   updates the values in graph widget from what
                                           was entered in the scale manager window.
            updateMessage:                 displays information to say update was
                                           successful.
            add_parameter_dialog:          instantiates the parameter specfication class and
                                           connects btnOK to paramDef function for GW to be added
            insert_parameter_dialog:       instantiates the parameter specfication class and
                                           connects btnOK to paramDef function for GW to be inserted
            editParaObj:                   instantiates the parameter specfication class and
                                           connects btnOK to editParamDef function.
            paramDef:                      adds specified paramater viewgraph to layout.
            editParamDef:                  changes the parameter plotted in viewgraph to
                                           the specified parameter.
            tirificMessage:                displays information about input data cube not
                                           available in current working directory.
            startTiriFiC:                  starts TiRiFiC from terminal.
"""