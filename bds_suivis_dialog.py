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
        self.db.setHostName("192.168.0.10")
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
        self.ui.btn_ajoutlgn.clicked.connect(self.ajoutlgn)
        self.ui.btn_supprlgn.clicked.connect(self.supprlgn)


    def recupdonnees(self):

        query_jrsmaxmois = QtSql.QSqlQuery(self.db)
        q_jrsmaxmois = u"""WITH tablo AS (SELECT id, CASE WHEN mois = 'janvier' THEN nb_jrs_ouv ELSE NULL END as janvier, CASE WHEN mois = 'fevrier' THEN nb_jrs_ouv ELSE NULL END as fevrier, CASE WHEN mois = 'mars' THEN nb_jrs_ouv ELSE NULL END as mars, CASE WHEN mois = 'avril' THEN nb_jrs_ouv ELSE NULL END as avril, CASE WHEN mois = 'mai' THEN nb_jrs_ouv ELSE NULL END as mai, CASE WHEN mois = 'juin' THEN nb_jrs_ouv ELSE NULL END as juin, CASE WHEN mois = 'juillet' THEN nb_jrs_ouv ELSE NULL END as juillet, CASE WHEN mois = 'aout' THEN nb_jrs_ouv ELSE NULL END as aout, CASE WHEN mois = 'septembre' THEN nb_jrs_ouv ELSE NULL END as septembre, CASE WHEN mois = 'octobre' THEN nb_jrs_ouv ELSE NULL END as octobre, CASE WHEN mois = 'novembre' THEN nb_jrs_ouv ELSE NULL END as novembre, CASE WHEN mois = 'decembre' THEN nb_jrs_ouv ELSE NULL END as decembre FROM bdsuivis.t_list_jours_ouvres ORDER BY id) SELECT string_agg(t.janvier::text, ','::text) AS janvier, string_agg(t.fevrier::text, ','::text) AS fevrier, string_agg(t.mars::text, ','::text) AS mars, string_agg(t.avril::text, ','::text) AS avril, string_agg(t.mai::text, ','::text) AS mai, string_agg(t.juin::text, ','::text) AS juin, string_agg(t.juillet::text, ','::text) AS juillet, string_agg(t.aout::text, ','::text) AS aout, string_agg(t.septembre::text, ','::text) AS septembre, string_agg(t.octobre::text, ','::text) AS octobre, string_agg(t.novembre::text, ','::text) AS novembre, string_agg(t.decembre::text, ','::text) AS décembre FROM bdsuivis.t_list_jours_ouvres l JOIN tablo t ON (l.id = t.id) WHERE l.annee='{zr_annee}'""".format(\
        zr_annee = self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex()))
        print q_jrsmaxmois
        ok = query_jrsmaxmois.exec_(q_jrsmaxmois)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête rempl jours max mois ratée')

        resultQuery = []
        while query_jrsmaxmois.next():
            resultQuery.append([])  # nouvelle ligne
            j = 0
            while query_jrsmaxmois.value(j):
                # ajout d'une donnée sur la ligne
                resultQuery[-1].append(query_jrsmaxmois.value(j))
                j += 1

        self.nomtable = resultQuery
        if not self.nomtable:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Pas de nb de jours max pour cette année')
        # création du modèle et de sa liaison avec la base SQL
        self.modelmois = QtSql.QSqlRelationalTableModel(self, self.db)
        # création du lien entre la table et le modèle
        self.ui.tbv_tps.setModel(self.modelmois)
        # désactiver le tri en cliquant sur les têtes de colonnes
        self.ui.tbv_tps.setSortingEnabled(False)
        # affiche la requête demandée
        self.modelmois.setQuery(query_jrsmaxmois)
        # peuple le modèle avec les données de la table
        self.modelmois.select()
        # ajuste la largeur des colonnes
        for a in range(0,12):
            self.ui.tbv_tps.setColumnWidth(a,40)
        self.ui.tbv_tps.verticalHeader().hide()
        # rétrécit la taille de la police dans les headers
        sizefont = self.ui.tbv_tps.horizontalHeader().setStyleSheet("QHeaderView{ font-size: 7pt; }")
        # adapte les libellés dans les entêtes
        listLabel = ['Janvier', u'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', u'Août', 'Sept.', 'Oct.', 'Nov.', u'Déc.']
        for column in range(12):
            self.modelmois.setHeaderData(column,QtCore.Qt.Horizontal,listLabel[column])



        # table à afficher
#        self.nomtable = resultQuery
#        if not self.nomtable:
            #return
#            QtGui.QMessageBox.warning(self, 'Alerte', u'Pas de données pour ce salarié et cette année')
        # création du modèle et de sa liaison avec la base SQL
#        self.model = QtSql.QSqlRelationalTableModel(self, self.db)
        self.model = QtSql.QSqlTableModel(self, self.db)
        # stratégie en cas de modification de données par l'utilisateur
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        # création du lien entre la table et le modèle
        self.ui.tbv_suivtemp.setModel(self.model)
        #CRéation du délégué et lien avec le QTableView
        self.ui.tbv_suivtemp.setItemDelegate(QtSql.QSqlRelationalDelegate(self.ui.tbv_suivtemp))
        # activer le tri en cliquant sur les têtes de colonnes
        self.ui.tbv_suivtemp.setSortingEnabled(True)
        # affiche la table de base de données demandée
#        self.model.setQuery(query_rempl_suivemp)
        self.model.setTable("bdsuivis.t_suivprev_tablo_test")
        self.model.select() # peuple le modèle avec les données de la table
        # Création des "datas" pour les colonnes "salarié" et "année", afin de pouvoir filtrer dessus
        self.model.setHeaderData(22, QtCore.Qt.Horizontal, "Annee")
        self.model.setHeaderData(21, QtCore.Qt.Horizontal, "Salarie")

        # filtre en fonction des contenus des combobox
            #création de variables qui serviront à filtrer
        salarie = self.ui.cbx_chsalarie.itemData(self.ui.cbx_chsalarie.currentIndex())
        annee = self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex())
            # Filtre : si rien sélectionné, tout afficher. Sinon setFilter selon les variables créées à partir des combobox (ci-dessus)
        if len(annee) == 0 and len(salarie) == 0:
            self.model.setFilter("")
        else:
            self.model.setFilter("Annee = '%s' AND Salarie = '%i'" % (annee, salarie))

        # cacher les colonnes ayant servi à filtrer
        self.ui.tbv_suivtemp.hideColumn(21)
        self.ui.tbv_suivtemp.hideColumn(22)

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
        self.ui.tbv_suivtemp.setColumnWidth(7,115)
        self.ui.tbv_suivtemp.setColumnWidth(8,136)
        for a in range(9,21):
            self.ui.tbv_suivtemp.setColumnWidth(a,40)
        
        # Adapte les libellés dans les entêtes
        listLabel = ['Id', 'Site', 'SE', u'Libellé suivi', 'FrqAn' , 'JrsPrev', u'Opérateur', 'Objctf PG ou LT', 'Remarques', 'Janvier', u'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', u'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']
        for column in range(21):
            self.model.setHeaderData(column,QtCore.Qt.Horizontal,listLabel[column])

        # rétrécit la taille de la police dans les headers
        sizefont = self.ui.tbv_suivtemp.horizontalHeader().setStyleSheet("QHeaderView{ font-size: 7pt; }")

        
    def sauvModifs(self):
        submit = self.model.submitAll()
        if not submit:
            print "rate"
            erreur = self.model.lastError().text()
            print erreur

    def ajoutlgn(self):
        return

    def supprlgn(self):
        return



