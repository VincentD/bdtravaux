# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bdsuivisDialog
                                 A QGIS plugin
 Plugin de saisie des suivis dans QGIS
                             -------------------
        begin                : 2015-08-25
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Conseravtoire d'espaces naturels Nord - Pas-de-Calais
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

import os, sys, csv

from PyQt4 import QtGui, uic, QtSql, Qt
from PyQt4.QtCore import *
from ui_bdsuivis_dialog_test import Ui_bdsuivis_dialog
from datetime import datetime


class bdsuivisDialog_test(QtGui.QDialog):
    def __init__(self):
        """Constructor."""
        QtGui.QDialog.__init__(self)
        self.ui = Ui_bdsuivis_dialog()
        self.ui.setupUi(self)

        # Connection to the database
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        self.db.setHostName("192.168.0.10")
        self.db.setPort(5432) 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'La connexion est échouée'+self.db.hostName())

        # Remplir le QtableView au chargement du module
        self.recupdonnees()
        
        # Connexions signaux - slots
        self.ui.btn_okannul.rejected.connect(self.close)

    def recupdonnees(self):

        self.model = QtSql.QSqlTableModel(self, self.db)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.ui.tbv_suivtemp.setModel(self.model)

#Essai pour changer couleur de quelques items du QTableView     
        # remplir le fond du QTableView automatiquement
        #self.ui.tbv_suivtemp.setAutoFillBackground(True)
        #p = self.ui.tbv_suivtemp.palette()
        #p.setColor(self.ui.tbv_suivtemp.backgroundRole(), QtGui.QColor(255,0,0))
        #self.ui.tbv_suivtemp.setPalette(p)
        
        #palette = self.palette()
        #role = self.backgroundRole()
        #palette.setColor(role, QColor('green'))
        #self.setPalette(palette)
        
        #delegue33 = self.ui.tbv_suivtemp.itemDelegate(self.model.index(3,3))
        #palette = delegue33.palette()
        #role = delegue33.backgroundRole()
        #palette.setColor(role, QColor(255,0,0))
        #delegue33.setPalette(palette)
        
        #table = self.ui.tbv_suivtemp
        #delegate = monDelegue(None, table)
        #table.setItemDelegate(delegate)

        #item = QtGui.QTableViewItem()  # le QTableView n'a pas d'items. Mais le modèle si. PAsser par le modèle?

        #item.setData(monDelegue.ItemBackgroundRole, QColor(Qt.red))
        


#self.model.setData(self.model.index(self.model.rowCount()-1,col), value, role = Qt.EditRole)


#Piste : You should use signal QAbstractItemModel::dataChanged(). Every time data change in your model, it has to emit that signal to notify views and/or proxy models that data has changed. Typicaly it is emitted in QAbstractItemModel::setData() after setting data, as it stands in Qt docs: "The dataChanged() signal should be emitted if the data was successfully set."
#All views will refresh changed items. 
#http://www.qtcentre.org/threads/18388-Refreshing-a-QTableView-when-QAbstractTableModel-changes


###
        self.model.setTable("bdsuivis.t_suivprev_tablo")
        self.model.select() # peuple le modèle avec les données de la table

            

###
#        color = QtGui.QColor(Qt.red)
#        if self.model.setData(self.model.index(2,2), color, role = Qt.BackgroundRole) :
#            QtGui.QMessageBox.warning(self, 'Alerte', u'Changement réussi dans le modèle')
#        else : 
#            QtGui.QMessageBox.warning(self, 'Information', u'Changement raté dans le modèle')
###


        # Adapte les libellés dans les entêtes
        listLabel = ['Id', 'Janv.', u'Fév.']
        for column in range(3):
            self.model.setHeaderData(column,Qt.Horizontal,listLabel[column])



#Céation du délégué pour gérer la couleur des cellules individuellement.
#class monDelegue(QtGui.QItemDelegate):

#    ItemBackgroundRole = Qt.UserRole + 1

#    def __init__(self, parent, table):
#        super(monDelegue, self).__init__(parent)
#        self.table = table

#    def paint(self, painter, option, index):
#        painter.save()
#        item = self.table.itemFromIndex(index)
#        if item:
#            bg_color = item.data(MyDelegate.ItemBackgroundRole)
#            if bg_color:
                # These two roles (Window, Base) both style different aspects of the "background"
                # Try with one or both to see which works for you
#                option.palette.setColor(QPalette.Window, bg_color)
#                option.palette.setColor(QPalette.Base, bg_color)
#        super(MyDelegate, self).paint(painter, option, index)
#        painter.restore()





