# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BdTravauxDialog
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

from PyQt4 import QtCore, QtGui, QtSql
from ui_bdtravaux_sortie import Ui_BdTravaux
# create the dialog for zoom to point


class BdTravauxDialog(QtGui.QDialog):
    def __init__(self):
        
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_BdTravaux()
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
        if query.exec_('select idchamp, codesite, nomsite from sites_cen.t_sitescen order by codesite'):
            while query.next():
                self.ui.site.addItem(query.value(1) + " " + query.value(2), query.value(1) )
            # *Voir la doc de la méthode additem d'une combobox : 1er paramètre = ce qu'on affiche (ici, codesite nomsite), 
            # 2ème paramètre = ce qu'on garde en mémoire pour plus tard

        #Initialisations pour objetVisiText (récup "objectif de la visite") et l'onglet "Chantier de volontaire : self.chantvol
        # et onglet désactivé
        self.objetVisiText=str(self.ui.obj_travaux.text())
        print self.objetVisiText
        self.chantvol=False
        self.ui.tab_chantvol.setEnabled(0)
#        self.ui.ch_partenaire.setCurrentRow(1)
        aucunpart=self.ui.ch_partenaire.findItems('Aucun',QtCore.Qt.MatchExactly)
        # findItems nécessite 2 arguments : la chaine à trouver et un QT.matchFlags qui correspond à la façon de chercher (chaine exacte, regex...) cf. http://qt-project.org/doc/qt-4.8/qt.html#MatchFlag-enum
        for item in aucunpart:
            item.setSelected(True)
            print item.text()


        # On connecte les signaux des boutons a nos methodes definies ci dessous
        # connexion du signal du bouton OK
        self.connect(self.ui.buttonBox_2, QtCore.SIGNAL('accepted()'), self.sauverInfos)
        self.connect(self.ui.buttonBox_2, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.objetvisite, QtCore.SIGNAL('buttonClicked(QAbstractButton*)'), self.objetVisiClicked)
        #http://www.qtcentre.org/archive/index.php/t-15687.html pour l'emploi de QAbstractButton


    def objetVisiClicked(self):
        #cette fonction gère les boutons radio indiquant l'objectif de la visite
        #création d'un générateur
        childs = (self.ui.obj_layout.itemAt(i) for i in range(self.ui.obj_layout.count())) 
        for radio in childs:
            if radio.widget().isChecked()==True:
                self.objetVisiText=unicode(radio.widget().text())
        if self.objetVisiText=='Chantier de volontaires':
            self.chantvol=True
            self.ui.tab_chantvol.setEnabled(1)
        else: 
            self.chantvol=False
            self.ui.tab_chantvol.setEnabled(0)
        return


    def sauverInfos(self):
        self.objetVisiClicked()
        query_save = QtSql.QSqlQuery(self.db)
        # syntaxe utilisant des templates de chaînes (obsolète) : query = """insert into sortie (date_sortie, redacteur, site, jours_chantier, chantier_vol, sort_com) values ('%s'::date, '%s', %s, '%s', %s, %s, '%s')""" % (self.ui.date.selectedDate().toString('yyyy-MM-dd'), self.ui.obsv.currentText(), self.ui.site.itemData(self.ui.site.currentIndex()).toInt()[0], self.ui.jours_chan.toPlainText(), str(self.ui.chantvol.isChecked()).lower(), self.ui.comm.toPlainText())
        # la requête ci-dessus avec des templates de chaîne fonctionne, mais est lourde. la syntaxe ci-dessous, sur plusieurs lignes, est beaucoup plus lisible. Les zones entre accolades sont des zones à remplacer. les zones sont suivies de .format (zone1=expression, zone2=expression2...). Les antislash provoquent un retour à la ligne sans couper la ligne de commande, et simplifient la lecture.
        query = u'INSERT INTO bdtravaux.sortie (date_sortie, codesite, chantvol, sortcom, objvisite, objvi_autr, natfaune, natflore, natautre) VALUES (\'{zr_date_sortie}\'::date, \'{zr_site}\', {zr_chantier_vol}, \'{zr_sort_com}\', \'{zr_objvisite}\', \'{zr_objvi_autr}\',\'{zr_natfaune}\',\'{zr_natflore}\',\'{zr_natautre}\' )'.format(\
        zr_date_sortie=self.ui.date.selectedDate().toPyDate().strftime("%Y-%m-%d"),\
        #zr_redacteur=self.ui.obsv.currentText(),\
        zr_site=self.ui.site.itemData(self.ui.site.currentIndex()),\
        zr_chantier_vol=self.chantvol,\
        #str(self.ui.chantvol.isChecked()).lower(),\
        zr_sort_com=self.ui.comm.toPlainText().replace("\'","\'\'"),\
        zr_objvisite=self.objetVisiText,\
        zr_objvi_autr=self.ui.obj_autre_text.text().replace("\'","\'\'"),\
        zr_natfaune=self.ui.natfaune.toPlainText().replace("\'","\'\'"),\
        zr_natflore=self.ui.natflore.toPlainText().replace("\'","\'\'"),\
        zr_natautre=self.ui.natfaune.toPlainText().replace("\'","\'\'")).encode("latin1")
        print query
        # à rebalancer dans finchantier.py : jours_chan,  ... \'{zr_jours_chantier}\' ... zr_jours_chantier=self.ui.jours_chan.toPlainText(),\
        ok = query_save.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
        self.rempliJoinSalarie()
        self.chantVol()
        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.reinitialiser()
        self.close()

        # contrôle "date" : on utilise la méthode SelectedDate des calendriers : self.ui.date.selectedDate(), toPyDate() pour
        # transformer l'objet QDate en objet "date " de Python, et la méthode Python strftime pour définir le format de sortie.
        # contrôle "obsv" : on utilise la méthode CurrentText d'une combobox
        # contrôle "site" : c'est aussi une combobox, mais on ne neut pas de texte, on veut la data définie quand on a rempli la combobox (cf. l54)
        # contrôles checkboxes : méthode isChecked renvoie un booléen. on transforme en chaîne (str), ce qui donne True ou False.
        # Or, on veut true ou false pour que PostGreSQl puisse les interprêter. D'où laméthode Python .lower, qui change la casse des chaînes.
        # contrôles "jours_chan" et "comm" : ce qont des QTextEdit. Ils prennent donc le texte saisi au format HTML. 
        # La méthode toPleinText() renvoie du texte classique


    def rempliJoinSalarie(self):
    #remplissage de la table join_salarie avec les salaries sélectionnés dans la QListWidget "obsv"
        #récupération de id_oper dans la table "sortie" pour le remettre dans join_salaries
        queryidsal = QtSql.QSqlQuery(self.db)
        qidsal = u"""select sortie_id from bdtravaux.sortie order by sortie_id desc limit 1"""
        ok2=queryidsal.exec_(qidsal)
        if not ok2:
            QtGui.QMessagebox.warning(self, 'Alerte', u'Pas trouvé id du salarie')
        queryidsal.next()
        self.sortie_id = queryidsal.value(0)
        print str(self.sortie_id)
        #remplissage de la table join_salaries : sortie_id et noms du (des) salarié(s)
        for item in xrange (len(self.ui.obsv.selectedItems())):
            querysalarie = QtSql.QSqlQuery(self.db)
            qsalarie = u"""insert into bdtravaux.join_salaries (id_joinsal, salaries, sal_initia) values ({zr_idjoinsal}, '{zr_salarie}','{zr_initiales}')""".format (\
            zr_idjoinsal = self.sortie_id,\
            zr_salarie = self.ui.obsv.selectedItems()[item].text().split("/")[0].replace("\'","\'\'"),\
            zr_initiales=self.ui.obsv.selectedItems()[item].text().split("/")[1])
            ok3 = querysalarie.exec_(qsalarie)
            if not ok3:
               # QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des salariés en base ratée')
                print qsalarie
            querysalarie.next()


    def chantVol(self):
        if self.chantvol==True :
            #récupération de l'ID de la sortie pour intégration dans la table ch_volont
            queryidsortie = QtSql.QSqlQuery(self.db)
            querysortie = u"""select sortie_id from bdtravaux.sortie order by sortie_id desc limit 1"""
            ok = queryidsortie.exec_(querysortie)
            if not ok:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Requête IdSoertie pour Chvolontaires ratée')
            queryidsortie.next()
            idsortie = queryidsortie.value(0)
            print "sortie="+str(idsortie)
            
            querychantvol = QtSql.QSqlQuery(self.db)
            querych = u"""insert into bdtravaux.ch_volont (nb_jours, nb_heur_ch, nb_heur_de, partenaire, heberg, j1_enc_am, j1_enc_pm, j1_tot_am, j1_tot_pm, j1adcen_am, j1adcen_pm, j1_blon_am, j1_blon_pm, j2_enc_am, j2_enc_pm, j2_tot_am, j2_tot_pm, j2adcen_am, j2adcen_pm, j2_blon_am, j2_blon_pm, sortie, sem_enc, sem_ben) values ({zr_nb_jours}, {zr_nb_heur_ch}, {zr_nb_heur_de}, '{zr_partenaire}', '{zr_heberg}', {zr_j1_enc_am}, {zr_j1_enc_pm}, {zr_j1_tot_am}, {zr_j1_tot_pm}, {zr_j1adcen_am}, {zr_j1adcen_pm}, {zr_j1_blon_am}, {zr_j1_blon_pm}, {zr_j2_enc_am}, {zr_j2_enc_pm}, {zr_j2_tot_am}, {zr_j2_tot_pm}, {zr_j2adcen_am}, {zr_j2adcen_pm}, {zr_j2_blon_am}, {zr_j2_blon_pm}, {zr_sortie}, {zr_sem_enc}, {zr_sem_ben})""".format (\
            zr_nb_jours = self.ui.ch_nb_jours.text(),\
            zr_nb_heur_ch = self.ui.ch_nb_heur_ch.text(),\
            zr_nb_heur_de = self.ui.ch_nb_heur_dec.text(),\
            zr_partenaire = self.ui.ch_partenaire.currentItem().text(),\
            zr_heberg = self.ui.ch_heberg.text(),\
            zr_j1_enc_am = self.ui.chtab_nbpers_jr1.item(0,0).text(),\
            zr_j1_enc_pm = self.ui.chtab_nbpers_jr1.item(0,1).text(),\
            zr_j1_tot_am = self.ui.chtab_nbpers_jr1.item(1,0).text(),\
            zr_j1_tot_pm = self.ui.chtab_nbpers_jr1.item(1,1).text(),\
            zr_j1adcen_am = self.ui.chtab_nbpers_jr1.item(2,0).text(),\
            zr_j1adcen_pm = self.ui.chtab_nbpers_jr1.item(2,1).text(),\
            zr_j1_blon_am = self.ui.chtab_nbpers_jr1.item(3,0).text(),\
            zr_j1_blon_pm = self.ui.chtab_nbpers_jr1.item(3,1).text(),\
            zr_j2_enc_am = self.ui.chtab_nbpers_jr2.item(0,0).text(),\
            zr_j2_enc_pm = self.ui.chtab_nbpers_jr2.item(0,1).text(),\
            zr_j2_tot_am = self.ui.chtab_nbpers_jr2.item(1,0).text(),\
            zr_j2_tot_pm = self.ui.chtab_nbpers_jr2.item(1,1).text(),\
            zr_j2adcen_am = self.ui.chtab_nbpers_jr2.item(2,0).text(),\
            zr_j2adcen_pm = self.ui.chtab_nbpers_jr2.item(2,1).text(),\
            zr_j2_blon_am = self.ui.chtab_nbpers_jr2.item(3,0).text(),\
            zr_j2_blon_pm = self.ui.chtab_nbpers_jr2.item(3,1).text(),\
            zr_sortie = idsortie,\
            zr_sem_enc = self.ui.chtabsem.item(0,0).text(),\
            zr_sem_ben = self.ui.chtabsem.item(0,1).text())
            ok_chvol = querychantvol.exec_(querych)
            if not ok_chvol:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Requête chantvol ratée')
            print querych



    def reinitialiser(self):
       for child in self.findChildren((QtGui.QRadioButton)):
            print child.objectName()
            child.setAutoExclusive(False)
            child.setChecked(False)
            child.setAutoExclusive(True)
            if child.text()=='Travaux sur site (hors chantiers de volontaires)':
                child.setChecked(True)
       for child in self.findChildren((QtGui.QLineEdit)):
            child.clear()
       for child in self.findChildren((QtGui.QTextEdit)):
            child.clear()
       for child in self.findChildren((QtGui.QTableWidget)):
            child.clear()
       for child in self.findChildren((QtGui.QCalendarWidget)):
            aujourdhui=QtCore.QDate.currentDate()
            child.setSelectedDate(aujourdhui)
