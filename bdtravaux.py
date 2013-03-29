# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BdTravaux
                                 A QGIS plugin
 Plugin d'aide à la saisie à destination des gerdes-techniciens
                              -------------------
        begin                : 2013-03-27
        copyright            : (C) 2013 by CEN NPdC
        email                : vincent.damoy@espaces-naturels.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from bdtravauxdialog import BdTravauxDialog
from operationdialog import OperationDialog


class BdTravaux:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bdtravaux"
        # initialize locale
        localePath = ""
        locale = QSettings().value("locale/userLocale").toString()[0:2]

        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/bdtravaux_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
              
        # Create the dialog (after translation) and keep reference
        self.dlg = BdTravauxDialog()
        self.dlg_ope= OperationDialog(iface)

    def initGui(self):
        # Create action that will start plugin configuration  (interface "sortie")
        self.action = QAction(
            QIcon(":/plugins/bdtravaux/icon.png"),
            u"Saisie sortie", self.iface.mainWindow())
        # connect the actions to the run methods
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.action)
        
        # Create action that will start plugin configuration (interface "opérations")
        self.operation = QAction(
            QIcon(":/plugins/bdtravaux/icon.png"),
            u"Saisie opérations", self.iface.mainWindow())
        # connect the action to the run method
        QObject.connect(self.operation, SIGNAL("triggered()"), self.run_ope)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.operation)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.operation)


    def unload(self):
        # Remove the plugin menu item and icon (interface "sortie")
        self.iface.removePluginMenu(u"&Saisie_travaux", self.action)
        self.iface.removeToolBarIcon(self.action)
        # Remove the plugin menu item and icon (interface "opérations")
        self.iface.removePluginMenu(u"&Saisie_travaux", self.operation)
        self.iface.removeToolBarIcon(self.operation)


    # run method that performs all the real work  (interface "sortie")
    def run(self):
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code)
            pass
    # run method that performs all the real work  (interface "operation")
    def run_ope(self):
        # show the dialog
        self.dlg_ope.actu_lblgeom() # mise à jour du label lbl_geom selon le nb et le type des entités sélectionnées
        self.dlg_ope.show()
        # Run the dialog event loop
        result = self.dlg_ope.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code)
            pass
