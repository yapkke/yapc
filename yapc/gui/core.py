from PyQt4 import QtGui, QtCore

class MainWindow(QtGui.QWidget):
    """Main window for applications

    @author ykk
    @date 
    """
    def __init__(self, title="yapc", width=100, height=100):
        """Initialize

        @param title string for window
        @param width width of window
        @param height height of window
        """
        QtGui.QWidget.__init__(self)
        self.setGeometry(0,0,width,height)
        self.setWindowTitle(title)

    def run(self, app):
        """Run GUI
        """
        self.show()
        return app.exec_()
