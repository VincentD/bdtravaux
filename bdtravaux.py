# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BdTravaux
                                 A QGIS plugin
 Plugin d'aide à la saisie à destination des gardes-techniciens
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
from prevudialog import PrevuDialog


class BdTravaux:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bdtravaux"
        # initialize locale
        localePath = ""
        # locale = QtCore.QSettings().value("locale/userLocale").toString()[0:2] (ancienne phrase)
        #pb : 'unicode' object has no attribute 'toString'. Pb de compatibilité entre 1.8 et 2.0 : le type QVariant (qui utilise ".toString" n'existe plus. Simplement enlever ".toString" (si on voulait transformer en un autre format, inclure type=str ou TYPE=INT... dans la parenthèse => .value("locale/userLocale", type=int) par exemple
        locale = QtCore.QSettings().value("locale/userLocale")[0:2]
             

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
        self.dlg_prev= PrevuDialog(iface)
        
    def initGui(self):
        # Création du bouton qui va démarrer le plugin (interface "sortie")
        self.action = QtGui.QAction(
            QtGui.QIcon(":/plugins/bdtravaux/icon2.png"),
            u"Saisie sortie", self.iface.mainWindow())
        # connecte le bouton à une méthode "run" 
        QtCore.QObject.connect(self.action, QtCore.SIGNAL("triggered()"), self.run)
        # ajoute l'icône sur la barre d'outils et l'élément de menu.
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.action)
        
        # Création du bouton qui va démarrer le plugin (interface "opérations")
        self.operation = QtGui.QAction(
            QtGui.QIcon(":/plugins/bdtravaux/icon3.png"),
            u"Saisie opérations", self.iface.mainWindow())
        # connecte le bouton à une méthode "run" 
        QtCore.QObject.connect(self.operation, QtCore.SIGNAL("triggered()"), self.run_ope)
        # ajoute l'icône sur la barre d'outils et l'élément de menu.
        self.iface.addToolBarIcon(self.operation)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.operation)
        
        # Création du bouton qui va démarrer le plugin (interface "gestion et suivis prévus")
        self.prevu = QtGui.QAction(
            QtGui.QIcon(":/plugins/bdtravaux/icon3.png"),
            u"Saisie gestion prévue", self.iface.mainWindow())
        # connecte le bouton à une méthode "run" 
        QtCore.QObject.connect(self.prevu, QtCore.SIGNAL("triggered()"), self.run_prev)
        # ajoute l'icône sur la barre d'outils et l'élément de menu.
        self.iface.addToolBarIcon(self.prevu)
        self.iface.addPluginToMenu(u"&Saisie_travaux", self.prevu)


    def unload(self):
        # Remove the plugin menu item and icon (interface "sortie")
        self.iface.removePluginMenu(u"&Saisie_travaux", self.action)
        self.iface.removeToolBarIcon(self.action)
        # Remove the plugin menu item and icon (interface "opérations")
        self.iface.removePluginMenu(u"&Saisie_travaux", self.operation)
        self.iface.removeToolBarIcon(self.operation)
        # Remove the plugin menu item and icon (interface "gestion et suivis prévus")
        self.iface.removePluginMenu(u"&Saisie_gestion_prévue", self.prevu)
        self.iface.removeToolBarIcon(self.prevu)


    # démarre la méthode qui va faire tout le travail (interface "sortie")
    def run(self):
        # show the dialog
        self.dlg.fillExSortieList()    # mise à jour de la liste de sorties déjà saisies (onglet 4)
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
        self.verif_geom()
        if self.dlg_ope.sansgeom=='True' or self.dlg_ope.sansgeom=='Geom':
            # show the dialog
            self.dlg_ope.actu_cbbx()    # mise à jour de la combobox "sortie"
            self.dlg_ope.actu_listeschoix() 
            print 'sansGeom ='+self.dlg_ope.sansgeom
            self.dlg_ope.actu_lblgeom() # mise à jour du label lbl_geom selon le nb et le type des entités sélectionnées
            self.dlg_ope.actu_gestprev_chxopechvol()#maj de la QListWidget gestprev selon le site choisi dans la ccbox "sortie"
            self.dlg_ope.show()
            # Run the dialog event loop
            result = self.dlg_ope.exec_()
            # See if OK was pressed
            if result == 1:
                # do something useful (delete the line containing pass and
                # substitute with your code)
                pass


    # démarre la méthode qui va faire tout le travail (interface "gestion et suivis prévus")
    def run_prev(self):
        self.verif_geom()
        if self.dlg_prev.sansgeom=='True' or self.dlg_prev.sansgeom=='Geom':
            # show the dialog
            self.dlg_prev.actu_listeOpe() 
            self.dlg_prev.show()
            # Run the dialog event loop
            result = self.dlg_prev.exec_()
            # See if OK was pressed
            if result == 1:
                # do something useful (delete the line containing pass and
                # substitute with your code)
                pass



    def verif_geom(self):
        # layer = la couche active. Si elle n'existe pas (pas de couche sélectionnée), alors lancer le message d'erreur et fermer la fenêtre.
        layer=self.iface.activeLayer()
        self.dlg_ope.sansgeom='Geom'
        self.dlg_prev.sansgeom='Geom'
        # construction du message d'erreur, qui sera utilisé si aucune couche ou aucune entité n'est sélectionnée
        messlayer=QtGui.QMessageBox()
        messlayer.setInformativeText(u'Voulez-vous saisir des données sans les placer sur le terrain?')
        messlayer.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        messlayer.setDefaultButton(QtGui.QMessageBox.No)
        messlayer.setIcon(QtGui.QMessageBox.Question)

        if not layer:
            #S'il n'y a aucune couche active
            messlayer.setText(u'Aucune couche SIG sélectionnée')
            ret = messlayer.exec_()
            if ret == QtGui.QMessageBox.Yes:
                self.dlg_ope.sansgeom='True'
                self.dlg_prev.sansgeom='True'
            elif ret == QtGui.QMessageBox.No:
                self.dlg_ope.sansgeom='False'
                self.dlg_prev.sansgeom='False'
                return
        # Attention : au contraire de ce qu'on a fait dans operationdialog.py, ne pas utiliser "self" en premier paramètre de
        # QMessageBox (il faut le widget parent), car ici self désigne une classe qui n'est pas un QWidget. 
        # Avec self.dlg_ope, la fenêtre "operation" devient parent => plus d'erreur "parameter 1 : unexpected 'instance'".
        # return permet de quitter la fonction sans exécuter la suite. D'où, plus de message d'erreur parce que 
        # la méthode "geometrytype" d'un "active layer" vide n'existe pas.
        
        else:
            # S'il y a une couche active, mais que c'est un raster
            if layer.type() == QgsMapLayer.RasterLayer:
                messlayer.setText(u'La couche SIG sélectionnée est une image')
                ret = messlayer.exec_()
                if ret == QtGui.QMessageBox.Yes:
                    self.dlg_ope.sansgeom='True'
                    self.dlg_prev.sansgeom='True'
                elif ret == QtGui.QMessageBox.No:
                    self.dlg_ope.sansgeom='False'
                    self.dlg_prev.sansgeom='False'
                    return
            else:
                #Si la couche active est bien un vecteur, mais aucune entité n'est sélectionnée
                selection=self.iface.activeLayer().selectedFeatures()
                if not selection:
                    #QtGui.QMessageBox.warning(self.dlg_ope, 'Alerte', u'Voulez-vous saisir des données non géographiques?')
                    messlayer.setText(u'Aucune entité sélectionnée')
                    ret = messlayer.exec_()
                    if ret == QtGui.QMessageBox.Yes:
                        self.dlg_ope.sansgeom='True'
                        self.dlg_prev.sansgeom='True'
                    elif ret == QtGui.QMessageBox.No:
                        self.dlg_ope.sansgeom='False'
                        self.dlg_prev.sansgeom='False'
                        return

