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
from PyQt4 import QtGui, QtCore
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
        self.plugin_dir = QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bdtravaux"
        # initialize locale
        localePath = ""
        locale = QtCore.QSettings().value("locale/userLocale").toString()[0:2]

        if QtCore.QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/bdtravaux_" + locale + ".qm"

        if QtCore.QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
              
        # Create the dialog (after translation) and keep reference
        self.dlg = BdTravauxDialog()
        self.dlg_ope= OperationDialog(iface)

    def initGui(self):
        # Création du bouton qui va démarrer le plugin (interface "sortie")
        self.action = QtGui.QAction(
            QtGui.QIcon(":/plugins/bdtravaux/icon.png"),
            u"Saisie sortie", self.iface.mainWindow())
        # connecte le bouton à une méthode "run" (def à la ligne 90)
        QtCore.QObject.connect(self.action, QtCore.SIGNAL("triggered()"), self.run)
        # ajoute l'icône sur la barre d'outils et l'élément de menu.
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.action)
        
        # Création du bouton qui va démarrer le plugin (interface "opérations")
        self.operation = QtGui.QAction(
            QtGui.QIcon(":/plugins/bdtravaux/icon.png"),
            u"Saisie opérations", self.iface.mainWindow())
        # connecte le bouton à une méthode "run" (def à la ligne 90)
        QtCore.QObject.connect(self.operation, QtCore.SIGNAL("triggered()"), self.run_ope)
        # ajoute l'icône sur la barre d'outils et l'élément de menu.
        self.iface.addToolBarIcon(self.operation)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.operation)


    def unload(self):
        # Remove the plugin menu item and icon (interface "sortie")
        self.iface.removePluginMenu(u"&Saisie_travaux", self.action)
        self.iface.removeToolBarIcon(self.action)
        # Remove the plugin menu item and icon (interface "opérations")
        self.iface.removePluginMenu(u"&Saisie_travaux", self.operation)
        self.iface.removeToolBarIcon(self.operation)


    # démarre la méthode qui va faire tout le travail (interface "sortie")
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
    # démarre la méthode qui va faire tout le travail  (interface "operation")
    def run_ope(self):
        # layer = la couche active. Si elle n'existe pas (pas de couche sélectionnée), alors lancer le message d'erreur et fermer la fenêtre.
        layer=self.iface.activeLayer()
        if not layer:
            QtGui.QMessageBox.warning(self.dlg_ope, 'Alerte', u'Sélectionner une couche')
            return
        # Attention : au contraire de ce qu'on a fait dans operationdialog.py, ne pas utiliser "self" en premier paramètre de
        # QMessageBox (il faut le widget parent), car ici self désigne une classe qui n'est pas un QWidget. 
        # Avec self.dlg_ope, la fenêtre "operation" devient parent => plus d'erreur "parameter 1 : unexpected 'instance'".

        #return permet de quitter la fonction sans exécuter la suite. D'où, plus de message d'erreur parce que 
        #la méthode "geometrytype" d'un "active layer" vide n'existe pas.
        
        #même code pour l'absence d'entité sélectionnée dans la couche active        
        selection=self.iface.activeLayer().selectedFeatures()
        if not selection:
            QtGui.QMessageBox.warning(self.dlg_ope, 'Alerte', u'Sélectionner une entité')
            return

        # show the dialog
        self.dlg_ope.actu_lblgeom() # mise à jour du label lbl_geom selon le nb et le type des entités sélectionnées
                                    # méthode actu_lblgeom() est importée avec OperationDialog (se trouve dans operationdialog.py)
        #self.connect(self.dlg_ope.actu_lblgeom(), QtCore.SIGNAL(), self, SLOT(close()))        
        self.dlg_ope.show()
        # Run the dialog event loop
        result = self.dlg_ope.exec_()
        # See if OK was pressed
        if result == 1:
            # do something useful (delete the line containing pass and
            # substitute with your code)
            pass
