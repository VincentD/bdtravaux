# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BdTravauxDialog
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
from ui_bdtravaux_sortie import Ui_BdTravaux
from composeur import composerClass

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
            QtGui.QMessageBox.warning(self, 'Alerte', u'La connexion est échouée'+self.db.hostName())

        # Remplir les comboboxs "site" avec les codes et noms de sites 
        # issus de la table "sites"
        query = QtSql.QSqlQuery(self.db)
        # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        if query.exec_('select idchamp, codesite, nomsite from sites_cen.t_sitescen order by codesite'):
            while query.next():
                self.ui.site.addItem(query.value(1) + " " + query.value(2), query.value(1) )
                self.ui.cbx_edcodesite.addItem(query.value(1) + " " + query.value(2), query.value(1) )
            # *Voir la doc de la méthode additem d'une combobox : 1er paramètre = ce qu'on affiche (ici, codesite nomsite), 
            # 2ème paramètre = ce qu'on garde en mémoire pour plus tard

        #Initialisations pour :
        # - objetVisiText (récup "objectif de la visite") 
        self.objetVisiText=str(self.ui.obj_travaux.text())
        # - self.chantvol et l'activation (ou pas) de l'onglet "Chantier de volontaire"
        self.chantvol=False
        self.ui.tab_chantvol.setEnabled(0)
        # - gestion des chantiers de volontaire si aucun partenaire n'est sélectionné
        aucunpart=self.ui.ch_partenaire.findItems('Aucun',QtCore.Qt.MatchExactly)
        # findItems nécessite 2 arguments : la chaine à trouver et un QT.matchFlags qui correspond à la façon de chercher (chaine exacte, regex...) cf. http://qt-project.org/doc/qt-4.8/qt.html#MatchFlag-enum
        for item in aucunpart:
            item.setSelected(True)

        # - chbox_plsrsjours et l'activation (oupas) du calendrier "datefin" et de la zone de texte "plsrsdates"
        self.ui.chbox_plsrsjrs.setChecked(0)
        self.date_fin='NULL'
        self.jourschan=""

        # Mise à jour du label "Id de la future sortie"
        queryidfutsort = QtSql.QSqlQuery(self.db)
        if queryidfutsort.exec_('SELECT sortie_id+1 FROM bdtravaux.sortie ORDER BY sortie_id DESC LIMIT 1'):
            while queryidfutsort.next():
                self.ui.lbl_idfutsortie.setText(str(queryidfutsort.value(0)))

        ## Connexions signaux-slots
        self.connect(self.ui.buttonBox_2, QtCore.SIGNAL('accepted()'), self.sauverInfos)
        self.connect(self.ui.buttonBox_2, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.objetvisite, QtCore.SIGNAL('buttonClicked(QAbstractButton*)'), self.objetVisiClicked)
        #http://www.qtcentre.org/archive/index.php/t-15687.html pour l'emploi de QAbstractButton
        #Connexion du signal "changement d'onglet" à la fonction qui active / désactive les bouton "OK" et "Annuler"
        self.connect(self.ui.tab_widget, QtCore.SIGNAL('currentChanged(int)'), self.masqueBoutons)
        self.connect(self.ui.btn_imp_exsortie, QtCore.SIGNAL('clicked()'), self.imprimExSort)
        self.connect(self.ui.chbox_plsrsjrs, QtCore.SIGNAL('stateChanged(int)'), self.enablePlsrsJours)
        self.connect(self.ui.cbx_exsortie, QtCore.SIGNAL('currentIndexChanged(int)'), self.fillEditControls)
        self.connect(self.ui.pbt_savemodifs, QtCore.SIGNAL('clicked()'), self.saveModifsSortie)
        self.connect(self.ui.pbt_supprsort, QtCore.SIGNAL('clicked()'), self.supprSort)




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
        if self.ui.obj_autre.isChecked()==True:
            self.objetVisiText='Autre...'
        return



    def enablePlsrsJours(self):
        if self.ui.chbox_plsrsjrs.isChecked()==True:
            self.ui.datefin.setEnabled(1)
            self.ui.lbl_datefin.setEnabled(1)
            self.ui.plsrsdates.setEnabled(1)
            self.ui.lbl_plsrsdates.setEnabled(1)
        else:
            self.ui.datefin.setEnabled(0)
            self.ui.lbl_datefin.setEnabled(0)
            self.ui.plsrsdates.setEnabled(0)
            self.ui.lbl_plsrsdates.setEnabled(0)
            



    def sauverInfos(self):
        self.objetVisiClicked()
        # S'il y a plusieurs dates, alors lire les données dans "datefin" et "plsrsdates". Sinon, la date de fin = la date de début et les jours ne sont pas renseignés
        if self.ui.chbox_plsrsjrs.isChecked()==True:
            self.date_fin=self.ui.datefin.selectedDate().toPyDate().strftime("%Y-%m-%d")
            self.jourschan=self.ui.plsrsdates.toPlainText().replace("\'","\'\'")
        else : 
            self.date_fin=self.ui.date.selectedDate().toPyDate().strftime("%Y-%m-%d")
            self.jourschan=""
        #Insertion en base des données saisies par l'utilisateur dans le module "sortie".
        query_save = QtSql.QSqlQuery(self.db)
        query = u'INSERT INTO bdtravaux.sortie (date_sortie, date_fin, jours_chan, codesite, chantvol, sortcom, objvisite, objvi_autr, natfaune, natflore, natautre) VALUES (\'{zr_date_sortie}\'::date, \'{zr_date_fin}\'::date,\'{zr_jourschan}\',\'{zr_site}\', {zr_chantier_vol}, \'{zr_sort_com}\', \'{zr_objvisite}\', \'{zr_objvi_autr}\',\'{zr_natfaune}\',\'{zr_natflore}\',\'{zr_natautre}\' )'.format(\
        zr_date_sortie=self.ui.date.selectedDate().toPyDate().strftime("%Y-%m-%d"),\
        zr_date_fin=self.date_fin,\
        zr_jourschan=self.jourschan,\
        zr_site=self.ui.site.itemData(self.ui.site.currentIndex()),\
        zr_chantier_vol=self.chantvol,\
        zr_sort_com=self.ui.comm.toPlainText().replace("\'","\'\'"),\
        zr_objvisite=self.objetVisiText,\
        zr_objvi_autr=self.ui.obj_autre_text.text().replace("\'","\'\'"),\
        zr_natfaune=self.ui.natfaune.toPlainText().replace("\'","\'\'"),\
        zr_natflore=self.ui.natflore.toPlainText().replace("\'","\'\'"),\
        zr_natautre=self.ui.natfaune.toPlainText().replace("\'","\'\'")).encode("latin1")
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
        # contrôle "site" : c'est une combobox, mais on ne veut pas de texte, on veut la data définie quand on a rempli la combobox (cf. l54)
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
            zr_salarie = self.ui.obsv.selectedItems()[item].text().split(" /")[0].replace("\'","\'\'"),\
            zr_initiales=self.ui.obsv.selectedItems()[item].text().split("/")[1])
            ok3 = querysalarie.exec_(qsalarie)
            if not ok3:
               QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des salariés en base ratée')
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
            zr_nb_jours = self.ui.ch_nb_jours.text().replace(",","."),\
            zr_nb_heur_ch = self.ui.ch_nb_heur_ch.text().replace(",","."),\
            zr_nb_heur_de = self.ui.ch_nb_heur_dec.text().replace(",","."),\
            zr_partenaire = self.ui.ch_partenaire.currentItem().text().replace("\'","\'\'"),\
            zr_heberg = self.ui.ch_heberg.text().replace("\'","\'\'"),\
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


    def masqueBoutons(self, index):
        #si l'onglet actif est "tab_extsortie" (index=4), alors les boutons OK et annuler sont masqués. Sinon ils sont actifs.
        print 'Boutons à masquer'+str(index)
        if index == 4:
            self.ui.buttonBox_2.setEnabled(False)
        else:
            self.ui.buttonBox_2.setEnabled(True)


    def fillExSortieList(self):
        self.ui.cbx_exsortie.clear()
        # Remplir la QlistWidget "listesortie" avec les champs date_sortie+site de la table "sortie" et le champ sal_initia de la table "join_salaries"
        query = QtSql.QSqlQuery(self.db)  # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        querySortie=u"""select sortie_id, date_sortie, codesite, array_to_string(array(select distinct sal_initia from bdtravaux.join_salaries where id_joinsal=sortie_id), '; ') as salaries from bdtravaux.sortie order by date_sortie DESC """
        ok = query.exec_(querySortie)
        while query.next():
            self.ui.cbx_exsortie.addItem(query.value(1).toPyDate().strftime("%Y-%m-%d") + " / " + str(query.value(2)) + " / "+ str(query.value(3)), int (query.value(0)))
        # 1er paramètre = ce qu'on affiche, 
        # 2ème paramètre = ce qu'on garde en mémoire pour plus tard
        if not ok :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête remplissage sortie ratée')
        self.ui.cbx_exsortie.setCurrentIndex(0)




    def fillEditControls(self):
        if self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex())==None :
            return
        else :
            #dans le tab "exsortie", réinitialise les contrôles contenant les données de la sortie à modifier.
            self.ui.dat_eddatdeb.setDate(QtCore.QDate.fromString("20000101","yyyyMMdd"))
            self.ui.dat_eddatfin.setDate(QtCore.QDate.fromString("20000101","yyyyMMdd"))
            self.ui.txt_edjourschan.setText('')
            self.ui.cbx_edcodesite.setCurrentIndex(0)
            self.ui.lst_edsalaries.clearSelection()
            self.ui.txt_edsortcom.setText('')
            self.ui.lst_edobjvisit.setCurrentRow(1)
            self.ui.txt_edobjvisautre.setText('')
            self.ui.txt_ednatfaune.setText('')
            self.ui.txt_ednatflor.setText('')
            self.ui.txt_ednatautr.setText('')
        
        
            #dans le tab "exsortie", remplit les contrôles contenant les données de la sortie à modifier.
            queryidsortie = QtSql.QSqlQuery(self.db)
            qidsort = u"""SELECT sortie_id, date_sortie, date_fin, jours_chan, codesite, array_to_string(array(select distinct salaries from bdtravaux.join_salaries where id_joinsal={zr_sortie}), '; ') as salaries, chantvol, sortcom, objvisite, objvi_autr, natfaune, natflore, natautre FROM bdtravaux.sortie WHERE sortie_id={zr_sortie};""".format(zr_sortie=self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex()))
            ok2=queryidsortie.exec_(qidsort)
            queryidsortie.next()
            if not ok2:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Pas trouvé la sortie à modifier')
            self.ui.dat_eddatdeb.setDate(queryidsortie.value(1))
            self.ui.dat_eddatfin.setDate(queryidsortie.value(2))
            self.ui.txt_edjourschan.setText(unicode(queryidsortie.value(3)))
            self.ui.cbx_edcodesite.setCurrentIndex(self.ui.cbx_edcodesite.findText(queryidsortie.value(4), QtCore.Qt.MatchStartsWith))
            self.ui.txt_edsortcom.setText(unicode(queryidsortie.value(7)))
            self.ui.lst_edobjvisit.setCurrentItem(self.ui.lst_edobjvisit.findItems(queryidsortie.value(8), QtCore.Qt.MatchExactly) [0])
            self.ui.txt_edobjvisautre.setText(unicode(queryidsortie.value(9)))
            self.ui.txt_ednatfaune.setText(unicode(queryidsortie.value(10)))
            self.ui.txt_ednatflor.setText(unicode(queryidsortie.value(11)))
            self.ui.txt_ednatautr.setText(unicode(queryidsortie.value(12)))
            self.ui.lbl_idsortie.setText(unicode(queryidsortie.value(0)))

            #cas à part : sélection d'items dans une liste (salariés présents lors de la sortie)
            list_sal = queryidsortie.value(5).split("; ")
            for y in xrange (self.ui.lst_edsalaries.count()):
                salarie=self.ui.lst_edsalaries.item(y)
                for x in list_sal:
                    if unicode(salarie.text().split(" /")[0])==x:
                        salarie.setSelected(True) 



    def imprimExSort(self):
        #Récupérer l'id_sortie à partir de la combobox cbx_exsortie (cf. RecupDonnSortie)
        self.sourceAffiche='ModSortie' # Pour indiquer au nouveau module "composeur.py" qu'on vient du module "Sortie" (peut-être pus nécessaire si on récupère id_sortie ici, et qu'on le passe en paramètre du composeur => le module composeur se fiche d'où vient l'info, tant qu'elle lui arrive)
        id_sortie = self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex())
        #lancement de la fonction Composeur dans le module composerClass avec le paramètre id_sortie
        self.obj_compo=composerClass()
        self.obj_compo.Composer(id_sortie)
        # Après fermeture du composeur, afficher le formulaire "bdtravauxdialog.py" devant iface, et l'activer.
        self.obj_compo.composerView.composerViewHide.connect(self.raiseModule)
        #Après fermeture du composeur, lancement de la fonction afterComposeurClose dans le module composerClass pour effacer les couches ayant servi au composeur, et réafficher les autres.
        self.obj_compo.composerView.composerViewHide.connect(self.obj_compo.afterComposerClose)



    def saveModifsSortie(self):
        # sauvegarde des modifications d'une sortie
        querysavemodsort = QtSql.QSqlQuery(self.db)
        qsavmods = u"""UPDATE bdtravaux.sortie SET date_sortie = '{zr_datedeb}'::date , date_fin = '{zr_datefin}'::date , codesite= '{zr_codesite}' , jours_chan='{zr_jourschan}' , sortcom = '{zr_sortcom}' , objvisite = '{zr_objvisite}' , objvi_autr = '{zr_objviautr}' , natfaune = '{zr_natfaune}' , natflore = '{zr_natflore}', natautre = '{zr_natautre}'  WHERE sortie_id={zr_sortie}""".format (\
        zr_datedeb = self.ui.dat_eddatdeb.date().toPyDate().strftime("%Y-%m-%d"),\
        zr_datefin = self.ui.dat_eddatfin.date().toPyDate().strftime("%Y-%m-%d"),\
        zr_codesite = self.ui.cbx_edcodesite.itemData(self.ui.cbx_edcodesite.currentIndex()),\
        zr_jourschan = self.ui.txt_edjourschan.toPlainText().replace("\'","\'\'"),\
        zr_sortcom = self.ui.txt_edsortcom.toPlainText().replace("\'","\'\'"),\
        zr_objvisite = self.ui.lst_edobjvisit.selectedItems()[0].text().replace("\'","\'\'"),\
        zr_objviautr = self.ui.txt_edobjvisautre.toPlainText().replace("\'","\'\'"),\
        zr_natfaune = self.ui.txt_ednatfaune.toPlainText().replace("\'","\'\'"),\
        zr_natflore = self.ui.txt_ednatflor.toPlainText().replace("\'","\'\'"),\
        zr_natautre = self.ui.txt_ednatautr.toPlainText().replace("\'","\'\'"),\
        zr_sortie = self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex()))
        ok = querysavemodsort.exec_(qsavmods)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Mise à jour sortie ratée')

        #sauvegarde des modifications de salariés : sortie_id, noms et initiales du (des) salarié(s)
            #suppression des salariés appartenant à la sortie modifiée
        querysupprsal = QtSql.QSqlQuery(self.db)
        qsupprsal = u"""DELETE FROM bdtravaux.join_salaries WHERE id_joinsal={zr_idjoinsal}""".format(\
        zr_idjoinsal = self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex()))
        ok4 = querysupprsal.exec_(qsupprsal)
        if not ok4 :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression des salariés en base ratée')
        print "salaries en trop supprimes"

            #ajout de la liste de salariés modifiée
        for item in xrange (len(self.ui.lst_edsalaries.selectedItems())):
            querymodifsal = QtSql.QSqlQuery(self.db)
            qmodsal = u"""insert into bdtravaux.join_salaries (id_joinsal, salaries, sal_initia) values ({zr_idjoinsal}, '{zr_salarie}','{zr_initiales}')""".format (\
            zr_idjoinsal = self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex()),\
            zr_salarie = self.ui.lst_edsalaries.selectedItems()[item].text().split(" /")[0].replace("\'","\'\'"),\
            zr_initiales=self.ui.lst_edsalaries.selectedItems()[item].text().split("/")[1])
            ok5 = querymodifsal.exec_(qmodsal)
            if not ok5:
               QtGui.QMessageBox.warning(self, 'Alerte', u'Modification des salariés en base ratée')
            querymodifsal.next()
            print "salaries modifies"

        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.close()

######################
# Suppression de sorties et données liées

    def supprSort(self):

        #récupération de l'identifiant de la sortie à supprimer
        self.sortieSuppr = self.ui.cbx_exsortie.itemData(self.ui.cbx_exsortie.currentIndex())

        # récupération de la liste des id des opérations à supprimer, et des id_oper (id des opérateurs et des types d'opérations à supprimer)
        self.opesuppr , self.idopersuppr = [] , []
        queryidopesuppr = QtSql.QSqlQuery(self.db)
        qidopesuppr = u"""SELECT operation_id, id_oper from (SELECT operation_id, id_oper, sortie FROM bdtravaux.operation_lgn UNION SELECT operation_id, id_oper, sortie FROM bdtravaux.operation_poly UNION SELECT operation_id, id_oper, sortie FROM bdtravaux.operation_pts) as tabope WHERE sortie = {zr_sortie}""".format (\
        zr_sortie = self.sortieSuppr)
        ok1 = queryidopesuppr.exec_(qidopesuppr)
        if not ok1:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Sélection operations à supprimer ratée')
        while queryidopesuppr.next():
            self.opesuppr.append(queryidopesuppr.value(0))
            self.idopersuppr.append(queryidopesuppr.value(1))

        if len(self.opesuppr) > 0:
        # suppression des données dans la table "join_operateurs"        
            querysupprsprest = QtSql.QSqlQuery(self.db)
            qsupprsprest = u"""DELETE FROM bdtravaux.join_operateurs WHERE id_joinop in ({zr_idjoinop})""".format(\
            zr_idjoinop = ','.join(map(str,self.idopersuppr)))
            ok2 = querysupprsprest.exec_(qsupprsprest)
            if not ok2:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression prestataires ratée')

        # suppression des données dans la table "join_typoperation"        
            querysupprstyp = QtSql.QSqlQuery(self.db)
            qsupprstyp = u"""DELETE FROM bdtravaux.join_typoperation WHERE id_jointyp in ({zr_idjointyp})""".format(\
            zr_idjointyp = ','.join(map(str,self.idopersuppr)))
            ok3 = querysupprstyp.exec_(qsupprstyp)
            if not ok3:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression types opération ratée')


        # suppression des données dans les tables "operation_xxx"        
            for couche in ['operation_poly','operation_pts','operation_lgn']:
                querysupprsope = QtSql.QSqlQuery(self.db)
                qsupprsope = u"""DELETE FROM bdtravaux.{zr_table} WHERE operation_id in ({zr_opeid})""".format(\
                zr_table = couche,\
                zr_opeid = ','.join(map(str,self.opesuppr)))
                ok4 = querysupprsope.exec_(qsupprsope)
                if not ok4:
                    QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression opération ratée')

        # suppression des données dans la table "sortie"
        querysupprssort = QtSql.QSqlQuery(self.db)
        qsupprssort = u"""DELETE FROM bdtravaux.sortie WHERE sortie_id = {zr_sortie}""".format(\
        zr_sortie = self.sortieSuppr)
        ok5 = querysupprssort.exec_(qsupprssort)
        if not ok5:
           QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression sortie ratée')

        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.close()



    def raiseModule(self):
        self.raise_()
        self.activateWindow()



    def reinitialiser(self):
        for child in self.findChildren((QtGui.QRadioButton)):
            child.setAutoExclusive(False)
            child.setChecked(False)
            child.setAutoExclusive(True)
            if child.text()=='Travaux sur site (hors chantiers de volontaires)':
                child.setChecked(True)
        regex = QtCore.QRegExp("^ch_nb*")
        for child in self.findChildren((QtGui.QLineEdit), regex):
            child.setText('0')
        for child in self.findChildren((QtGui.QTextEdit)):
            child.clear()
        for child in self.findChildren((QtGui.QTableWidget)):
            for row in xrange(child.rowCount ()):
                for column in xrange(child.columnCount ()):
                    item = child.item (row, column )
                    item.setText('0')
        self.ui.tab_chantvol.setEnabled(0)
        self.ui.tab_widget.setCurrentIndex(0)
        for child in self.findChildren((QtGui.QCalendarWidget)):
            aujourdhui=QtCore.QDate.currentDate()
            child.setSelectedDate(aujourdhui)
