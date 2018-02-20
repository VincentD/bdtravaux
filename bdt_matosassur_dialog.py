# -*- coding: utf-8 -*-
"""
/***************************************************************************
 bdmatosassurDialog
                                 A QGIS plugin
 Plugin de saisie d'habitats naturels dans QGIS
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
from ui_bdtravaux_matosassur import Ui_MatosAssurDialog


class matosAssurDialog(QtGui.QDialog):
    def __init__(self,id_sortie):
        """Constructor."""
        QtGui.QDialog.__init__(self)
        self.ui = Ui_MatosAssurDialog()
        self.ui.setupUi(self)

        # Connexion à la base de données. DB type, host, user, password...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        self.db.setHostName("192.168.0.10") 
        self.db.setPort(5432) 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'La connexion est échouée'+self.db.hostName())

        #Création de l'objet self.idsortie pour requêtes sur la sortie, à partir du paramètre id_sortie venant du module "opération".
        print "idsortie dans matassur = "+str(id_sortie)
        self.id_sortie=id_sortie

        #Le boutons OK est grisé tant qu'on n'a pas sélectionné un item de la liste
        self.ui.btn_matosassur.setEnabled(0)


        # Connexions signaux - slots
        self.ui.btn_matosassur.clicked.connect(self.trsfrtDonnees)
        self.ui.lst_assur.itemSelectionChanged.connect(self.activButton)       
        
        
    def activButton(self):
        matosassurlist = self.ui.lst_assur.selectedItems()
        if len(matosassurlist) !=0:
            self.ui.btn_matosassur.setEnabled(1)
        
        
    def recupDonnSortie(self):
    # Récupération des données de la sortie pour les intégrer dans la reqte de remplaissage de la table t_matos_assur.
        # Initialisations
        self.datpose = None
        self.datvandal = None
        self.datretrait = None
        
        #recup de données en fction de l'Id de la sortie.
        querycodesite = QtSql.QSqlQuery(self.db)
        qcodesite = u"""select sor.codesite, (select nomsite from sites_cen.t_sitescen sit where sit.codesite=sor.codesite) as nomsite, (select loc_commune from sites_cen.t_sitescen sit where sit.codesite=sor.codesite) as communes, date_sortie from bdtravaux.sortie sor where sortie_id = {zr_sortie_id}""".format \
        (zr_sortie_id = str(self.id_sortie)) #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        oksort = querycodesite.exec_(qcodesite)
        if not oksort:
            print u'Requête recupDonnSortie ratée'
        querycodesite.next()
        self.codedusite=querycodesite.value(0)
        self.nomdusite=querycodesite.value(1)
        self.communes=querycodesite.value(2)
        self.datesortie=querycodesite.value(3).toPyDate().strftime("%Y-%m-%d")
        
        
        #calcul des objets qui seront insérés dans la requête d'insertion (cf. fonction trsfrtDonnees)
        print len(self.ui.lst_assur.selectedItems())
        for item in xrange (len(self.ui.lst_assur.selectedItems())):
            print self.ui.lst_assur.selectedItems()[item].text().replace("\'","\'\'")
            if self.ui.lst_assur.selectedItems()[item].text().replace("\'","\'\'") == u"""Pose de nouveau matériel""" or \
            self.ui.lst_assur.selectedItems()[item].text().replace("\'","\'\'") == u"""Remplacement pour usure""" or \
            self.ui.lst_assur.selectedItems()[item].text().replace("\'","\'\'") == u"""Remplacement pour vol / vandalisme""":
                print "pose nouveau matos"
                self.datpose = self.datesortie
                self.datvandal = 'Null'
                self.datretrait='Null'
            elif self.ui.lst_assur.selectedItems()[item].text().replace("\'","\'\'") == u"""Constat de dégradation""":
                print "vandalisme"
                self.datvandal = self.datesortie
            elif self.ui.lst_assur.selectedItems()[item].text().replace("\'","\'\'") == u"""Retrait (sans remplacement le jour même)""":
                print "retrait"
                self.datretrait = self.datesortie
            else :
                print 'hivernage du matériel'
                self.close()
        
        
        
    def trsfrtDonnees(self):
        
        self.recupDonnSortie()
        
        queryMatosAssur = QtSql.QSqlQuery(self.db)
        qMatosAssur = u"""INSERT INTO bdtravaux.t_matos_assur_pts(id_matos, codesite, nomsite, commune, typ_matos, dat_pose, 
            dat_vandal, dat_retrait, id_sortie, geom) VALUES ('{zr_idmatos}', '{zr_codesite}', '{zr_nomsite}', '{zr_commune}','{zr_typmatos}', '{zr_datpose}', {zr_datvandal}, {zr_datretrait}, '{zr_idsortie}', '{zr_geom}')""".format (\
        zr_idmatos = '',\
        zr_codesite = self.codedusite,\
        zr_nomsite = self.nomdusite,\
        zr_commune = self.communes,\
        zr_typmatos = '',\
        zr_datpose = self.datpose,\
        zr_datvandal = self.datvandal,\
        zr_datretrait = self.datretrait,\
        zr_idsortie = self.id_sortie,\
        zr_geom = '')
        ok = queryMatosAssur.exec_(qMatosAssur)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête saisie données Matos à Assurer ratée')
            print unicode(qMatosAssur)

    ############ En cours : adapter les zr_xxx pour récupérer toutes les données à insérer dans la table t_matos_assur_pts
   


            






