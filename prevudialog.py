# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PrevuDialog
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

from PyQt4 import QtCore, QtGui, QtSql
from ui_gestprev import Ui_GestPrev
# create the dialog for zoom to point


class PrevuDialog(QtGui.QDialog):
    def __init__(self, iface):
        
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_GestPrev()
        self.ui.setupUi(self)

        #Quand la classe est fermée, elle est effacée. permet de réinitialiser toutes les valeurs si on réappuie sur le bouton.
        #self.setAttribute(QtCore.Qt.WA_QuitOnClose, True)
        
        # DB type, host, user, password...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        #ici on crée self.db =objet de la classe, et non db=variable, car on veut réutiliser db même en étant sorti du constructeur
        # (une variable n'est exploitable que dans le bloc où elle a été créée)
        self.db.setHostName("127.0.0.1") 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Connexion échouée')
        # Remplir la combobox "site" avec les codes et noms de sites 
        # issus de la table "sites"
        query = QtSql.QSqlQuery(self.db)
        # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
#        if query.exec_('select idchamp, codesite, nomsite from sites_cen.t_sitescen order by codesite'):
#            while query.next():
#                self.ui.site.addItem(query.value(1) + " " + query.value(2), query.value(1) )
            # *Voir la doc de la méthode additem d'une combobox : 1er paramètre = ce qu'on affiche (ici, codesite nomsite), 
            # 2ème paramètre = ce qu'on garde en mémoire pour plus tard

        # On connecte les signaux des boutons a nos methodes definies ci dessous
        # connexion du signal du bouton OK
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'), self.sauverInfos)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'), self.close)


    def sauverOpe(self):
        # Fonction à lancer quans le bouton "OK" est cliqué
        # Entre en base les infos sélectionnées dans QGIS, et saisies dans le formulaire par l'utilisateur

        if self.iface.activeLayer().geometryType()==0:
            nom_table='list_gestprev_pts'
        elif self.iface.activeLayer().geometryType()==1:
            nom_table='list_gestprev_lgn'
        elif self.iface.activeLayer().geometryType()==2:
            nom_table='list_gestprev_surf'

        coucheactive=self.iface.activeLayer()

        #lancement de la requête SQL qui introduit les données géographiques et du formulaire dans la base de données.
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.{zr_nomtable} (prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_annprev, prev_pdg, the_geom) values ({zr_codesite}, '{zr_codeope}', '{zr_typeope}', '{zr_lblope}', '{zr_annprev}', '{zr_pdg}', st_setsrid(st_geometryfromtext ('{zr_the_geom}'),2154)')""".format (zr_nomtable=nom_table,\
        zr_codesite = self.ui.prevcombo_codesite.itemData(self.ui.prevcombo_codesite.currentIndex()),\
        zr_codeope = self.ui.prevledit_gh.text(),\
        zr_typeope = self.ui.prevlist_typeope.currentItem().text(),\
        zr_lblope = self.ui.prevtedit_lblope.toPlainText(),\
        zr_annprev = self.ui.prevledit_annprev.text(),\
        zr_pdg = self.ui.prevlist_pdg.currentItem().text(),\
        zr_the_geom = coucheactive.selectedFeatures().exportToWkt(),\
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
            print query
        self.iface.setActiveLayer(coucheactive)
        self.close



#    def reinitialiser(self):
#       for child in self.findChildren((QtGui.QRadioButton)):
#            print child.objectName()
#            child.setAutoExclusive(False)
#            child.setChecked(False)
#            child.setAutoExclusive(True)
#            if child.text()=='Travaux sur site (hors chantiers de volontaires)':
#                child.setChecked(True)
#       for child in self.findChildren((QtGui.QLineEdit)):
#            child.clear()
#       for child in self.findChildren((QtGui.QTextEdit)):
#            child.clear()
#       for child in self.findChildren((QtGui.QTableWidget)):
#            child.clear()
#       for child in self.findChildren((QtGui.QCalendarWidget)):
#            aujourdhui=QtCore.QDate.currentDate()
#            child.setSelectedDate(aujourdhui)
