#!/usr/bin/python
"""
This is a python program that provides an interface to fuskbugg.se, it is
called "fuskbugg python uploader".

Copyright (C) 2011 Linus Wallgren
This file is part of fuskbugg python uploader.

This program  is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
import fuskbugg
from PyQt4 import QtGui, QtCore

class MainGui(QtGui.QMainWindow):
    # Contains default values
    geometry_config = {"x" : 0, "y": 0, "width": 750, "height" : 300}
    labels = ["url", "ip", "trash", "date", "size"] # The order of items
    def __init__(self):
        self.init_config()
        self.init_UI()

    def init_config(self):
        if not fuskbugg.config.has_section("geometry"):
            fuskbugg.config.add_section("geometry")
            for (key, value) in self.geometry_config.iteritems():
                fuskbugg.config.set("geometry", key, str(value))
        for (key, value) in fuskbugg.config.items("geometry"):
            self.geometry_config[key] = value

    def init_UI(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Fuskbugg uploader")
        self.setGeometry(int(self.geometry_config['x']), int(self.geometry_config['y']), int(self.geometry_config['width']), int(self.geometry_config['height']))
        self.setWindowIcon(QtGui.QIcon('images/icon.png'))

        # All widgets displayed on screen
        screenshot_button = QtGui.QAction('Upload screenshot', self)
        screenshot_button.setShortcut('Ctrl+p')
        screenshot_button.setToolTip('Take screenshot and upload to fuskbugg')
        about_button = QtGui.QAction('About', self)
        about_button.setToolTip('About fuskbugg python uploader')

        self.toolbar_action = self.addToolBar('Actions')
        self.toolbar_about = self.addToolBar('About')

        self.toolbar_action.addAction(screenshot_button)
        self.toolbar_about.addAction(about_button)

        # Connect signals with slots
        self.connect(screenshot_button, QtCore.SIGNAL('triggered()'), self.take_screenshot)
        self.connect(about_button, QtCore.SIGNAL('triggered()'), self.about_dialog)
        self.connect(QtGui.QApplication.instance(), QtCore.SIGNAL('aboutToQuit()'), self.quit)

        label_mapping = {"url" : "URL", "ip" : "IP", "trash" : "In trash", "date" : "Upload date", "size": "Size"}

        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels([label_mapping[i] for i in self.labels])

        tree = QtGui.QTreeView(self)
        tree.setModel(self.model)
        self.update_filelist()
        tree.setSortingEnabled(True)
        tree.sortByColumn(self.labels.index('date'),QtCore.Qt.DescendingOrder)

        tree.header().setResizeMode(QtGui.QHeaderView.Interactive)

        # if url doesnt exist in the config file we assume no other
        # column-width values does either, and therefore resize them to fit the
        # contents
        if not fuskbugg.config.has_option("geometry", "url"):
            tree.header().resizeSections(QtGui.QHeaderView.ResizeToContents)
        else:
            for i in xrange(0, len(self.labels)):
                tree.header().resizeSection(i, int(self.geometry_config[self.labels[i]]))

        self.setCentralWidget(tree)

    def update_filelist(self):
        self.model.removeRows(0, self.model.rowCount())
        for file in fuskbugg.get_file_list():
            items = []
            for key in self.labels:
                items.append(QtGui.QStandardItem(str(file[key])))
            self.model.appendRow(items)


    def take_screenshot(self):
        self.hide()
        window = QtGui.QPixmap.grabWindow(QtGui.QApplication.desktop().winId())
        filename = str(QtGui.QFileDialog.getSaveFileName(self, 'Save file as'))
        self.show()
        if window.save(filename):
            print "Saved screenshot as %s" % (filename)
            (status, result) = fuskbugg.post_file(filename) 
            if status:
                print "%s uploaded to URL %s" % (filename, result)
                self.update_filelist()
            else:
                print result
        else:
            print "The file could not be saved"

    def about_dialog(self):
        QtGui.QMessageBox.about(self, "About %s" % (self.windowTitle()), 
                """This program is written by Linus Wallgren, and licensed under GPLv3.

My contact information and further information about this program can be found in the README file included in the root directory of this program."""
                )

    def quit(self):
        geometry = self.geometry()
        fuskbugg.config.set("geometry", "x", str(geometry.x()))
        fuskbugg.config.set("geometry", "y", str(geometry.y()))
        fuskbugg.config.set("geometry", "height", str(geometry.height()))
        fuskbugg.config.set("geometry", "width", str(geometry.width()))

        header = self.findChild(QtGui.QTreeView).header()
        for i in xrange(0, len(self.labels)):
            fuskbugg.config.set("geometry", self.labels[i], str(header.sectionSize(i)))
        with open(fuskbugg.config_file, 'wb') as configfile:
            fuskbugg.config.write(configfile)

# Used for the argument parser to start the GUI
def run_gui():
    app = QtGui.QApplication(sys.argv)
    main_gui = MainGui()
    main_gui.show()
    return app.exec_()

# For debuging purpouses
if __name__ == '__main__':
    run_gui()

