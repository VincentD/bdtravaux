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
        
        # DB type, host, user, password...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        #ici on crée self.db =objet de la classe, et non db=variable, car on veut réutiliser db même en étant sorti du constructeur
        # (une variable n'est exploitable que dans le bloc où elle a été créée)
        self.db.setHostName("192.168.0.103") 
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
            # l'Int renvoie deux paramètres. Le [0] précise qu'on ne veut récupérer que le premier, qui est l'entier 
            # (le 2ème para = boolean pour savoir si la conversion a marché)
            
            
        # On connecte les signaux des boutons a nos methodes definies ci dessous
        # connexion du signal du bouton OK
        self.connect(self.ui.buttonBox_2, QtCore.SIGNAL('accepted()'), self.sauverInfos)
        self.connect(self.ui.buttonBox_2, QtCore.SIGNAL('rejected()'), self.close)
            
    def sauverInfos(self):
        query_save = QtSql.QSqlQuery(self.db)
        # query = """insert into sortie (date_sortie, redacteur, site, jours_chantier, chantier_fini, chantier_vol, sort_com) values ('%s'::date, '%s', %s, '%s', %s, %s, '%s')""" % (self.ui.date.selectedDate().toString('yyyy-MM-dd'), self.ui.obsv.currentText(), self.ui.site.itemData(self.ui.site.currentIndex()).toInt()[0], self.ui.jours_chan.toPlainText(), str(self.ui.chantfini.isChecked()).lower(), str(self.ui.chantvol.isChecked()).lower(), self.ui.comm.toPlainText())
        # la requête ci-dessus avec des templates de chaîne fonctionne, mais est lourde. la syntaxe ci-dessous, sur plusieurs liges, est beaucoup plus lisible. Les zones entre accolades sont des zones à remplacer. les zones sont suivies de . format (zone1=expression, zone2=expression2...). Les antislash provoquent un retour à la ligne sans couper la ligne de commande, et à simplifier la lecture.
        query = u'INSERT INTO bdtravaux.sortie (date_sortie, redacteur, codesite, jours_chan, chantfini, chantvol, sortcom) VALUES (\'{zr_date_sortie}\'::date, \'{zr_redacteur}\', \'{zr_site}\', \'{zr_jours_chantier}\', {zr_chantier_fini}, {zr_chantier_vol}, \'{zr_sort_com}\')'.format(\
        zr_date_sortie=self.ui.date.selectedDate().toPyDate().strftime("%Y-%m-%d"),\
        zr_redacteur=self.ui.obsv.currentText(),\
        zr_site=self.ui.site.itemData(self.ui.site.currentIndex()),\
        zr_jours_chantier=self.ui.jours_chan.toPlainText(),\
        zr_chantier_fini=str(self.ui.chantfini.isChecked()).lower(),\
        zr_chantier_vol=str(self.ui.chantvol.isChecked()).lower(),\
        zr_sort_com=self.ui.comm.toPlainText())
        print query
               
        ok = query_save.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
        #print query
        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.close()
                
                
        # contrôle "date" : on utilise la méthode SelectedDate des calendriers : self.ui.date.selectedDate(), toPyDate() pour
        # transformer l'objet QDate en objet "date " de Python, et la méthode Python strftime pour définir le format de sortie.
        # contrôle "obsv" : on utilise la méthode CurrentText d'une combobox
        # contrôle "site" : c'est aussi une combobox, mais on ne neut pas de texte, on veut la data définie quand on a rempli la combobox (cf. l54)
        # contrôles checkboxes : méthode isChecked renvoie un booléen. on transforme en chaîne (str), ce qui donne True ou False.
        # Or, on veut true ou false pour que PostGreSQl puisse les interprêter. D'où laméthode Python .lower, qui change la casse des chaînes.
        # contrôles "jours_chan" et "comm" : ce qont des QTextEdit. Ils prennent donc le texte saisi au format HTML. 
        # La méthode toPleinText() renvoie du texte classique
   
