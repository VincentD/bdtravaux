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

import os

from PyQt4 import QtCore, QtGui, uic, QtSql, Qt
from qgis.core import *
from qgis.gui import *
from ui_bdsuivis_dialog import Ui_bdsuivis_dialog
from datetime import datetime


class bdsuivisDialog(QtGui.QDialog):
    def __init__(self):
        """Constructor."""
        QtGui.QDialog.__init__(self)
        self.ui = Ui_bdsuivis_dialog()
        self.ui.setupUi(self)

        # Référencement de iface dans l'interface (iface = interface de QGIS)
#        self.iface = iface
#        self.canvas = self.iface.mapCanvas()
        
        # Connexion à la base de données. DB type, host, user, password...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        self.db.setHostName("127.0.0.1")
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'La connexion est échouée'+self.db.hostName())

        # Remplir la combobox "cbx_chsalarie" avec les prénoms et nopm sissus de la table "t_list_salaries"
        query_salarie = QtSql.QSqlQuery(self.db)
        if query_salarie.exec_('select sps_id, sps_nomsal from bdsuivis.t_list_salaries order by sps_nomsal'):
            while query_salarie.next():
                self.ui.cbx_chsalarie.addItem(query_salarie.value(1), query_salarie.value(0) )

        #Initialisations
        self.ui.cbx_chsalarie.setCurrentIndex(0)
        self.ui.cbx_channee.setCurrentIndex(self.ui.cbx_channee.findText((datetime.now().strftime('%Y')), QtCore.Qt.MatchStartsWith))


        # Remplir le QtableView au chargement du module
        self.recupdonnees()
        
        # Désactiver le bouton "OK" tant qu'on n'a pas choisi au moins un référentiel.
#        self.ui.btn_okannul.setEnabled(False)

        # Connexions signaux - slots
        self.ui.cbx_chsalarie.currentIndexChanged.connect(self.recupdonnees)
        self.ui.cbx_channee.currentIndexChanged.connect(self.recupdonnees)
        self.ui.btn_okannul.accepted.connect(self.sauvModifs)
        self.ui.btn_okannul.rejected.connect(self.sauvModifs)


    def recupdonnees(self):
        # lorsque le module est lancé ou que les combobox ont changé d'index, récupération des données de la base et remplissage des tableaux
        query_rempl_suivemp = QtSql.QSqlQuery(self.db)
        query = u"""WITH tablo AS (SELECT tps.spt_spid, tps.spt_annee, CASE WHEN tps.spt_mois::text = 'janvier'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS janvier, CASE WHEN tps.spt_mois::text ='février'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS fevrier, CASE WHEN tps.spt_mois::text = 'mars'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS mars, CASE WHEN tps.spt_mois::text = 'avril'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS avril, CASE WHEN tps.spt_mois::text = 'mai'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS mai, CASE WHEN tps.spt_mois::text = 'juin'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS juin, CASE WHEN tps.spt_mois::text = 'juillet'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS juillet, CASE WHEN tps.spt_mois::text = 'aout'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS aout, CASE WHEN tps.spt_mois::text = 'septembre'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS septembre, CASE WHEN tps.spt_mois::text = 'octobre'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS octobre, CASE WHEN tps.spt_mois::text = 'novembre'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS novembre, CASE WHEN tps.spt_mois::text = 'decembre'::text THEN tps.spt_nb_jrs_prev ELSE NULL::real END AS decembre FROM bdsuivis.t_join_suivprev_temps tps ORDER BY tps.spt_spid) SELECT DISTINCT sp.sp_idsuivi, sp.sp_codesit, sp.sp_codese, sp.sp_libelle, sp.sp_frannu, sp.sp_tpsprev, sp.sp_operat,sp.sp_objpglt, sp.sp_rq, string_agg(t.janvier::text, ','::text) AS janvier, string_agg(t.fevrier::text, ','::text) AS fevrier, string_agg(t.mars::text, ','::text) AS mars, string_agg(t.avril::text, ','::text) AS avril, string_agg(t.mai::text, ','::text) AS mai, string_agg(t.juin::text, ','::text) AS juin, string_agg(t.juillet::text, ','::text) AS juillet, string_agg(t.aout::text, ','::text) AS aout, string_agg(t.septembre::text, ','::text) AS septembre, string_agg(t.octobre::text, ','::text) AS octobre, string_agg(t.novembre::text, ','::text) AS novembre, string_agg(t.janvier::text, ','::text) AS decembre FROM bdsuivis.t_suivprev sp JOIN tablo t ON sp.sp_idsuivi = t.spt_spid WHERE sp_salarie = '{zr_salarie}' and spt_annee = '{zr_annee}' GROUP BY t.spt_spid, sp.sp_idsuivi, sp.sp_codesit, sp.sp_codese, sp.sp_libelle, sp.sp_frannu, sp.sp_tpsprev, sp.sp_operat, sp.sp_objpglt, sp.sp_rq ORDER BY sp.sp_codesit, sp.sp_codese;""".format (\
       zr_salarie = self.ui.cbx_chsalarie.itemData(self.ui.cbx_chsalarie.currentIndex()),\
       zr_annee = self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex()))
        print query
        ok = query_rempl_suivemp.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête rempl tableau suiv_temps ratée')

        resultQuery = []
        while query_rempl_suivemp.next():
            resultQuery.append([])  # nouvelle ligne
            j = 0
            while query_rempl_suivemp.value(j):
                # ajout d'une donnée sur la ligne
                resultQuery[-1].append(query_rempl_suivemp.value(j))
                j += 1


        # table à afficher
        self.nomtable = resultQuery
        if not self.nomtable:
            #return
            QtGui.QMessageBox.warning(self, 'Alerte', u'Pas de données pour ce salarié et cette année')
        # création du modèle et de sa liaison avec la base SQL
        self.model = QtSql.QSqlRelationalTableModel(self, self.db)
        # stratégie en cas de modification de données par l'utilisateur
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        # création du lien entre la table et le modèle
        self.ui.tbv_suivtemp.setModel(self.model)
        #CRéation du délégué et lien avec le QTableView
        self.ui.tbv_suivtemp.setItemDelegate(QtSql.QSqlRelationalDelegate(self.ui.tbv_suivtemp))
        # activer le tri en cliquant sur les têtes de colonnes
        self.ui.tbv_suivtemp.setSortingEnabled(True)
        # affiche la table de base de données demandée
        self.model.setQuery(query_rempl_suivemp)
        self.model.select() # peuple le modèle avec les données de la table
 
        # tri si nécessaire selon la colonne 0
        self.model.sort(0, QtCore.Qt.AscendingOrder) # ou DescendingOrder
 
        # ajuste la largeur des colonnes
#        self.ui.tbv_suivtemp.resizeColumnsToContents()
        self.ui.tbv_suivtemp.setColumnWidth(0,40)
        self.ui.tbv_suivtemp.setColumnWidth(1,40)
        self.ui.tbv_suivtemp.setColumnWidth(2,50)
        self.ui.tbv_suivtemp.setColumnWidth(3,170)
        self.ui.tbv_suivtemp.setColumnWidth(4,30)
        self.ui.tbv_suivtemp.setColumnWidth(5,40)
        self.ui.tbv_suivtemp.setColumnWidth(6,50)
        self.ui.tbv_suivtemp.setColumnWidth(7,100)
        self.ui.tbv_suivtemp.setColumnWidth(8,120)
        for a in range(9,21):
            self.ui.tbv_suivtemp.setColumnWidth(a,40)
        
        # Adapte les libellés dans les entêtes
 #       self.ui.tbv_suivtemp.setHorizontalHeaderLabels(['Id', 'Site', 'SE', 'Libellé suivi', 'FrqAn' , 'JrsPrev', 'Opérateur', 'Objctf PG ou LT', 'Remarques', 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Sept.', 'Octobre', 'Nov.', 'Déc.'])
        listLabel = ['Id', 'Site', 'SE', u'Libellé suivi', 'FrqAn' , 'JrsPrev', u'Opérateur', 'Objctf PG ou LT', 'Remarques', 'Janvier', u'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', u'Août', 'Sept.', 'Octobre', 'Nov.', u'Déc.']
        for column in range(21):
            self.model.setHeaderData(column,QtCore.Qt.Horizontal,listLabel[column])

        # rétrécit la taille de la police dans les headers
        sizefont = self.ui.tbv_suivtemp.horizontalHeader().setStyleSheet("QHeaderView{ font-size: 7pt; }")

        
    def sauvModifs(self):
        self.model.submitAll()
        return
        
        
        
# ci-dessous : un exemple de création de modèle (QSqlRelationalTble Model pour accéder à une table de BD), de connexion du modèle avec la QTableView (absolument recommandée par la doc de QT, plutôt que le QTableWidget), de connexion entre la requête et le modèle, puis d'affichage des données dans le QTableView + quelques paramètres (largeures des colonnes, etc...)

#https://www.developpez.net/forums/d1463248/autres-langages/python-zope/gui/pyqt/qtablewidget-remplissage-requete-sql-affichage-lignes-desordre/


#Bonjour, Voilà un petit code de test donné à titre de source d'inspiration. Il utilise un QTableView pour afficher une table d"une base de données. Il suffira de changer le nom de la base de données, le nom de la table, et de réécrire les fonctions ouvrebaseqt et fermebaseqt en fonction du type de base utilisé (j'utilise ici sqlite3).



#!/usr/bin/python
# -*- coding: utf-8 -*-
# Python 2.7, PyQt4
 
#import sys, os
#from PyQt4 import QtCore, QtGui, QtSql
 
#############################################################################
#def ouvrebaseqt(basesql, contrainte=True):
#    """ouvre la base 'basesql' et renvoie la connexion (None si échec)"""
 
    # tentative d'ouverture de la base
#    db = QtSql.QSqlDatabase.addDatabase(u"QSQLITE")
#    db.setDatabaseName(basesql)
#    if not db.open():
#        db = None
 
    # activation des contraites d'intégrité référentielles
#    if (db != None) and contrainte:
#        query = QtSql.QSqlQuery(db)
#        req = u"PRAGMA foreign_keys=on;"
#        if not query.exec_(req):
#            query.finish()    # désactive le curseur
#            query = None
#            fermebaseqt(db)  # fermeture de la base
#            db = None             
#        if query != None:
#            query.finish()    # désactive le curseur
 
    # renvoi de la connexion ouverte (ou None si échec)
#    return db
 
#############################################################################
#def fermebaseqt(db):
#    if db!=None:
#        db.close()
 
#############################################################################
#class VoirTableSql(QtGui.QMainWindow):
# 
#    def __init__(self, basesql, nomtable, parent=None):
#        super(VoirTableSql, self).__init__(parent)
# 
#        self.setWindowTitle(u"Affichage de la table %s" % (nomtable,))
#        self.resize(800, 600)
# 
        # ouverture de la base SQL
#        self.basesql = basesql
#        self.db = ouvrebaseqt(self.basesql)
#        if self.db == None:
#            self.close()
 
        # table à afficher
#        self.nomtable = nomtable    
 
        # création du modèle et de sa liaison avec la base SQL
#        self.model = QtSql.QSqlRelationalTableModel(self, self.db)
        # stratégie en cas de modification de données par l'utilisateur
#        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
 
        # création de la table et de son lien avec le modèle
#        self.vuetable = QtGui.QTableView(self)
#        self.vuetable.setModel(self.model)
#        self.vuetable.setItemDelegate(QtSql.QSqlRelationalDelegate(self.vuetable))
        # activer le tri en cliquant sur les têtes de colonnes
#        self.vuetable.setSortingEnabled(True)
 
        # positionnement du QTableView dans la fenêtre
#        self.setCentralWidget(QtGui.QFrame())
#        posit = QtGui.QGridLayout()
#        posit.addWidget(self.vuetable, 0, 0)
#        self.centralWidget().setLayout(posit)
 
        # affiche la table demandée
#        self.model.setTable(self.nomtable)
#        self.model.select() # peuple le modèle avec les données de la table
 
        # tri si nécessaire selon la colonne 0
#        self.model.sort(0, QtCore.Qt.AscendingOrder) # ou DescendingOrder
 
        # ajuste la largeur des colonnes en fonction de leurs contenus
#        self.vuetable.resizeColumnsToContents()
 
    #========================================================================
#    def closeEvent(self, event=None):
#        """Méthode appelée automatiquement à la fermeture de la fenêtre"""
#        #fermeture de la base
#        fermebaseqt(self.db)
#        event.accept()
 
#############################################################################
#if __name__ == "__main__":
#    app = QtGui.QApplication(sys.argv)
 
#    basesql = u"mabase.db3"
#    nomtable = u"photos"
 
#    fen = VoirTableSql(basesql, nomtable)
#    fen.show()
#    sys.exit(app.exec_())

