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
        self.db.setPort(5432) 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'La connexion est échouée'+self.db.hostName())


        #Initialisations
        self.ui.cbx_channee.setCurrentIndex(self.ui.cbx_channee.findText((datetime.now().strftime('%Y')), Qt.MatchStartsWith))
        self.text_sal = 'Janczak Alexandra'
        self.idligne = 0 # compteur permettant d'incrémenter l'ID des nouvelles lignes

        # Remplir la liste de choix lst_salaries
        self.ui.lst_salaries.clear()
        querySal = QtSql.QSqlQuery(self.db)
        qsalaries=u"""SELECT id_salarie, sa_nomcomp FROM sites_cen.t_salaries_cen WHERE sa_pole IN ('scientifique') ORDER BY sa_nomcomp;"""
        ok = querySal.exec_(qsalaries)
        while querySal.next():
            self.ui.lst_salaries.addItem(unicode(querySal.value(1)))
        if not ok :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête remplissage salariés ratée')

        # Remplir la combobox "site" avec les codes et noms de sites issus de la table "sites" et les codes et noms des études issus de la table "etudes"
        query = QtSql.QSqlQuery(self.db)
        if query.exec_('SELECT codesite, nomsite FROM sites_cen.t_sitescen UNION SELECT spe_code, spe_nom FROM bdsuivis.t_list_etudes ORDER by codesite;'):
            while query.next():
                self.ui.cbx_chsite.addItem(query.value(0) + " " + query.value(1), query.value(0) )


        # Remplir le QtableView au chargement du module
        self.recupdonnees()
        
        # Connexions signaux - slots
        #self.ui.cbx_chsalarie.currentIndexChanged.connect(self.recupdonnees)
        #self.ui.cbx_channee.currentIndexChanged.connect(self.recupdonnees)
        self.ui.btn_okannul.accepted.connect(self.sauvModifs)
        self.ui.btn_okannul.rejected.connect(self.close)
        self.ui.btn_ajoutlgn.clicked.connect(self.ajoutlgn)
        self.ui.btn_supprlgn.clicked.connect(self.supprlgn)
        self.ui.btn_duplgn.clicked.connect(self.dupllgn)
        self.ui.btn_choisal.clicked.connect(self.choisal)
        self.ui.btn_expcsv.clicked.connect(self.saveCsv)



    def choisal(self):
        self.list_sal = []
        for item in xrange (len(self.ui.lst_salaries.selectedItems())):
            salarie = self.ui.lst_salaries.selectedItems()[item].text().replace("\'","\'\'")
            self.list_sal.append(salarie)
        self.text_sal = ",".join((unicode(x) for x in self.list_sal)).replace(",","\',\'")
        print unicode(self.text_sal)
        self.recupdonnees()

    def recupdonnees(self):

        # 1 Récupération et affichage des données du nombre de jours maximum travaillés dans un mois
        query_jrsmaxmois = QtSql.QSqlQuery(self.db)
        q_jrsmaxmois = u"""WITH tablo AS (SELECT id, CASE WHEN mois = 'janvier' THEN nb_jrs_ouv ELSE NULL END as janvier, CASE WHEN mois = 'fevrier' THEN nb_jrs_ouv ELSE NULL END as fevrier, CASE WHEN mois = 'mars' THEN nb_jrs_ouv ELSE NULL END as mars, CASE WHEN mois = 'avril' THEN nb_jrs_ouv ELSE NULL END as avril, CASE WHEN mois = 'mai' THEN nb_jrs_ouv ELSE NULL END as mai, CASE WHEN mois = 'juin' THEN nb_jrs_ouv ELSE NULL END as juin, CASE WHEN mois = 'juillet' THEN nb_jrs_ouv ELSE NULL END as juillet, CASE WHEN mois = 'aout' THEN nb_jrs_ouv ELSE NULL END as aout, CASE WHEN mois = 'septembre' THEN nb_jrs_ouv ELSE NULL END as septembre, CASE WHEN mois = 'octobre' THEN nb_jrs_ouv ELSE NULL END as octobre, CASE WHEN mois = 'novembre' THEN nb_jrs_ouv ELSE NULL END as novembre, CASE WHEN mois = 'decembre' THEN nb_jrs_ouv ELSE NULL END as decembre FROM bdsuivis.t_list_jours_ouvres ORDER BY id) SELECT string_agg(t.janvier, ',')::real AS janvier, string_agg(t.fevrier, ',')::real AS fevrier, string_agg(t.mars, ',')::real AS mars, string_agg(t.avril, ',')::real AS avril, string_agg(t.mai, ',')::real AS mai, string_agg(t.juin, ',')::real AS juin, string_agg(t.juillet, ',')::real AS juillet, string_agg(t.aout, ',')::real AS aout, string_agg(t.septembre, ',')::real AS septembre, string_agg(t.octobre, ',')::real AS octobre, string_agg(t.novembre, ',')::real AS novembre, string_agg(t.decembre, ',')::real AS décembre FROM bdsuivis.t_list_jours_ouvres l JOIN tablo t ON (l.id = t.id) WHERE l.annee='{zr_annee}'""".format(\
        zr_annee = self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex()))
        #print q_jrsmaxmois
        ok = query_jrsmaxmois.exec_(q_jrsmaxmois)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête rempl jours max mois ratée')
        #Stockage des nb max de jours travaillés dans une liste pour comparaison ultérieure avec les nb réels de jours travaillés. (cf. dans les environs de la ligne 147)
        resultQjrsMax = []
        while query_jrsmaxmois.next():
            #resultQjrsMax.append([])  # nouvelle ligne
            j = 0
            for j in range(12):
                moismax = query_jrsmaxmois.value(j)
                #print moismax
                # ajout d'une donnée dans la liste
                resultQjrsMax.append(moismax)

        # création du modèle et de sa liaison avec la base SQL
        self.modelmaxjrs = QtSql.QSqlRelationalTableModel(self, self.db)
        # création du lien entre la table et le modèle
        self.ui.tbv_tps.setModel(self.modelmaxjrs)
        # désactiver le tri en cliquant sur les têtes de colonnes
        self.ui.tbv_tps.setSortingEnabled(False)
        # affiche la requête demandée
        self.modelmaxjrs.setQuery(query_jrsmaxmois)
        # peuple le modèle avec les données de la table
        self.modelmaxjrs.select()
        # ajuste la largeur des colonnes
        for a in range(0,12):
            self.ui.tbv_tps.setColumnWidth(a,35)
        self.ui.tbv_tps.verticalHeader().hide()
        # rétrécit la taille de la police dans les headers
        sizefont = self.ui.tbv_tps.horizontalHeader().setStyleSheet("QHeaderView{ font-size: 7pt; }")
        # adapte les libellés dans les entêtes
        listLabel = ['Janv.', u'Fév.', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', u'Août', 'Sept.', 'Oct.', 'Nov.', u'Déc.']
        for column in range(12):
            self.modelmaxjrs.setHeaderData(column,Qt.Horizontal,listLabel[column])



        # 2 Récupération et affichage des données du nombre de jours travaillés dans le mois (= somme des jours de suivis prévus dans le QTableView principal). comparaison avec le nb de jours maximum
        query_jrsmois = QtSql.QSqlQuery(self.db)
        qjrsmois = u"""SELECT sum(coalesce(t.janvier,0)) as sjanvier, sum(coalesce(t.fevrier,0)) as sfevrier, sum(coalesce(t.mars,0)) as smars, sum(coalesce(t.avril,0)) as savril, sum(coalesce(t.mai,0)) as smai, sum(coalesce(t.juin,0)) as sjuin, sum(coalesce(t.juillet,0)) as sjuillet, sum(coalesce(t.aout,0)) as saout, sum(coalesce(t.septembre,0)) as sseptembre, sum(coalesce(t.octobre,0)) as soctobre, sum(coalesce(t.novembre,0)) as snovembre, sum(coalesce(t.decembre,0)) as sdecembre FROM bdsuivis.t_suivprev_tablo t WHERE salaries IN ('{zr_salarie}') AND annee = '{zr_annee}' AND sp_operat = 'Régie';""".format(\
        zr_salarie = self.text_sal,
        zr_annee = self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex()))
        #print qjrsmois
        ok = query_jrsmois.exec_(qjrsmois)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête rempl jours mois ratée')

            # Stockage des nb réels de jours travaillés dans une liste pour comparaison avec les nb max de jours travaillés.
        resultQjrs = []
        while query_jrsmois.next():
            i = 0
            for i in range(12):
                mois = query_jrsmois.value(i)
                #print mois
                resultQjrs.append(mois)
            #print resultQjrs

            # Comparaison des nb max et réels de jours travaillés dans chaque mois de l'année sélectionnée. Police rouge si nb réel > nb max
        for i in range(12):
            if resultQjrs[i]>resultQjrsMax[i]:
                print 'trop grand'
#                self.modelmaxjrs.index(0,i).setStyleSheet("color : red")
                #self.ui.tbv_sum.item(0,i).setStyleSheet("color : red")
            else:
#                self.modelmaxjrs.index(0,i).setStyleSheet("color : black")
                print 'OK'

        # création du modèle et de sa liaison avec la base SQL
        self.modeljrs = QtSql.QSqlRelationalTableModel(self, self.db)
        # création du lien entre la table et le modèle
        self.ui.tbv_sum.setModel(self.modeljrs)
        # désactiver le tri en cliquant sur les têtes de colonnes
        self.ui.tbv_sum.setSortingEnabled(False)
        # affiche la requête demandée
        self.modeljrs.setQuery(query_jrsmois)
        # peuple le modèle avec les données de la table
        self.modeljrs.select()
        # ajuste la largeur des colonnes
        for a in range(0,12):
            self.ui.tbv_sum.setColumnWidth(a,35)
        self.ui.tbv_sum.verticalHeader().hide()
        self.ui.tbv_sum.horizontalHeader().hide()
        #self.ui.tbv_sum.setStyleSheet("color : red")



        # 3 Récupération et affichage des données dans le QTableView principal
        # création du modèle et de sa liaison avec la base SQL
        self.model = QtSql.QSqlTableModel(self, self.db)
        # stratégie en cas de modification de données par l'utilisateur
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        # création du lien entre la table et le modèle
        self.ui.tbv_suivtemp.setModel(self.model)
        # création du délégué et lien avec le QTableView
       # self.delegue = self.ui.tbv_suivtemp.setItemDelegate(QtSql.QSqlRelationalDelegate(self.ui.tbv_suivtemp))
   

### Essai pour changer couleur de quelques items du QTableView     
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
        
        # activer le tri en cliquant sur les têtes de colonnes
        self.ui.tbv_suivtemp.setSortingEnabled(True)
        # affiche la table de base de données demandée
        self.model.setTable("bdsuivis.t_suivprev_tablo")
        self.model.select() # peuple le modèle avec les données de la table


        # filtre en fonction des contenus de la liste à choix multiples et de la combobox
            #création de variables qui serviront à filtrer
        site = self.ui.cbx_chsite.itemText(self.ui.cbx_chsite.currentIndex())
        annee = self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex())
        if len(site) == 0 or site == "Tous les sites":
            site = '0filtresite'
        if len(annee) == 0 or annee == u"""Toutes les années""":
            annee = '0filtreannee'
            # Filtre : si pas de salarié sélectionné, ne rien afficher. Sinon création du filtre selon les variables créées à partir des combobox (ci-dessus), et application via setFilter.
        if len(self.text_sal) == 0:
            return
        else:
            if site == '0filtresite' and annee == '0filtreannee':
                filtre = "salaries IN ('%s')" % (self.text_sal)
            elif site == '0filtresite' and annee != '0filtreannee':
                filtre = "annee = '%s' AND salaries IN ('%s')" % (annee, self.text_sal)
            elif site != '0filtresite' and annee == '0filtreannee':
                filtre = "sp_codesit = '%s' AND salaries IN ('%s')" % (site[:3], self.text_sal)
            elif site != '0filtresite' and annee != '0filtreannee':
                filtre = "sp_codesit = '%s' AND annee = '%s' AND salaries IN ('%s')" % (site[:3], annee, self.text_sal)
            print filtre
            self.model.setFilter(filtre)

###
#        color = QtGui.QColor(Qt.red)
#        if self.model.setData(self.model.index(2,2), color, role = Qt.BackgroundRole) :
#            QtGui.QMessageBox.warning(self, 'Alerte', u'Changement réussi dans le modèle')
#        else : 
#            QtGui.QMessageBox.warning(self, 'Information', u'Changement raté dans le modèle')
###


        # tri si nécessaire selon la colonne 0
        self.model.sort(0, Qt.AscendingOrder) # ou DescendingOrder
 

        # ajuste la largeur des colonnes
#        self.ui.tbv_suivtemp.resizeColumnsToContents()
        self.ui.tbv_suivtemp.setColumnWidth(0,35)
        self.ui.tbv_suivtemp.setColumnWidth(1,35)
        self.ui.tbv_suivtemp.setColumnWidth(2,45)
        self.ui.tbv_suivtemp.setColumnWidth(3,170)
        self.ui.tbv_suivtemp.setColumnWidth(4,30)
        self.ui.tbv_suivtemp.setColumnWidth(5,40)
        self.ui.tbv_suivtemp.setColumnWidth(6,50)
        self.ui.tbv_suivtemp.setColumnWidth(7,50)
        self.ui.tbv_suivtemp.setColumnWidth(8,115)
        self.ui.tbv_suivtemp.setColumnWidth(9,35)
        self.ui.tbv_suivtemp.setColumnWidth(10,115)
        for a in range(11,23):
            self.ui.tbv_suivtemp.setColumnWidth(a,35)

        
        # Adapte les libellés dans les entêtes
        listLabel = ['Id', 'Site', 'SE', u'Libellé suivi', 'FrqAn' , 'JrsPrev', u'Opérateur', 'Objctf PG ou LT', 'Remarques', 'Annee', 'Salarie', 'Janv.', u'Fév.', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', u'Août', 'Sept.', 'Oct.', 'Nov.', u'Déc.']
        for column in range(22):
            self.model.setHeaderData(column,Qt.Horizontal,listLabel[column])

        # rétrécit la taille de la police dans les headers
        sizefont = self.ui.tbv_suivtemp.horizontalHeader().setStyleSheet("QHeaderView{ font-size: 7pt; }")



    def sauvModifs(self):
        # on vérifie pour chaque champ de texte que le texte saisi ne dépasse par la longueur du champ.
        # Requête renvoyant les longueurs maximales des chaînes de caractères dans les champs de type character varying
        query_longmax = QtSql.QSqlQuery(self.db)
        qlgmax = u"""SELECT CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = 't_suivprev_tablo';"""
        ok = query_longmax.exec_(qlgmax)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête longueur champs ratée')
        # Récupératuion des longueurs maximales de texte dans les champs de type "character varying", et comparaison avec les valeurs saisies par l'utilisateur
        i = 0
        while query_longmax.next():
            lgchamp = query_longmax.value(0)
            if lgchamp:
                #print lgchamp
                for j in range (self.model.rowCount()):
                    if self.model.data(self.model.index(j,i)):
                        if lgchamp < len(self.model.data(self.model.index(j,i))):
                            QtGui.QMessageBox.warning(self, 'Alerte', u'Texte trop long dans la colonne {}'.format(i+1))
                            return
            i = i+1

        # Les données du modèle sont saisies en base
        submit = self.model.submitAll()
        if not submit:
            print "rate"
            erreur = self.model.lastError().text()
            print unicode(erreur)
        else:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Données saisies en base')



    def ajoutlgn(self):
        #Ajout d'une nouvelle ligne dans le QTableView et remplissage de l'identifiant unique
        query_idNewLine = QtSql.QSqlQuery(self.db)
        if self.idligne == 0:
            if query_idNewLine.exec_('SELECT sp_idsuivi+1 FROM bdsuivis.t_suivprev_tablo ORDER BY sp_idsuivi DESC LIMIT 1'):
                while query_idNewLine.next():
                    identifiant = query_idNewLine.value(0)
                    print identifiant
            self.idligne = identifiant
        else:
            self.idligne = self.idligne +1
            identifiant = self.idligne

        record = self.model.record();
        record.setValue(0,identifiant)
        record.setValue(22,self.ui.cbx_channee.itemText(self.ui.cbx_channee.currentIndex()))
        record.setValue(23,self.text_sal.replace("\',\'",","))
        self.model.insertRecord(self.model.rowCount(), record)
        #self.model.dataChanged.emit(self.model.createIndex(self.model.rowCount(), 0),self.model.createIndex(self.model.rowCount(), 22))



    def supprlgn(self):
        index_list = []                                                          
        for model_index in self.ui.tbv_suivtemp.selectionModel().selectedRows():       
            index = QPersistentModelIndex(model_index)         
            index_list.append(index)                                             

        for index in index_list:                                      
             self.model.removeRow(index.row()) 


    def dupllgn(self):
        index_list = []                                                          
        for model_index in self.ui.tbv_suivtemp.selectionModel().selectedRows():       
            index = QPersistentModelIndex(model_index)         
            index_list.append(index)
            if len(index_list) == 1:
                self.ajoutlgn()  
                list_values = []
                for col in xrange(1,23):
                    value = self.model.data(self.model.index(index_list[0].row(),col), role = Qt.DisplayRole)
                    list_values.append(value)
                    self.model.setData(self.model.index(self.model.rowCount()-1,col), value, role = Qt.EditRole)
            else:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Choisir une et une seule ligne à dupliquer')


    def saveCsv(self):
        path = QtGui.QFileDialog.getSaveFileName(
                self, 'Save File', '', 'CSV(*.csv)')
        if path!= '':
            with open(unicode(path), 'wb') as stream:
                writer = csv.writer(stream)
                for row in range(self.model.rowCount()):
                    rowdata = []
                    for column in range(self.model.columnCount()):
                        value = self.model.data(self.model.index(row, column))
                        if value is not None:
                            rowdata.append(
                                unicode(value).encode('utf8'))
                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)


#Céation du délégué pour gérer la couleur des cellules individuellement.
class monDelegue(QtGui.QItemDelegate):

    ItemBackgroundRole = Qt.UserRole + 1

    def __init__(self, parent, table):
        super(monDelegue, self).__init__(parent)
        self.table = table

    def paint(self, painter, option, index):
        painter.save()
        item = self.table.itemFromIndex(index)
        if item:
            bg_color = item.data(MyDelegate.ItemBackgroundRole)
            if bg_color:
                # These two roles (Window, Base) both style different aspects of the "background"
                # Try with one or both to see which works for you
                option.palette.setColor(QPalette.Window, bg_color)
                option.palette.setColor(QPalette.Base, bg_color)
        super(MyDelegate, self).paint(painter, option, index)
        painter.restore()





