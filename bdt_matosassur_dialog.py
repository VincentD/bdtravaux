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
    def __init__(self, iface):
        """Constructor."""
        QtGui.QDialog.__init__(self)
        self.ui = Ui_MatosAssurDialog()
        self.ui.setupUi(self)

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

        # Connexions signaux - slots
        self.ui.buttonBox.accepted.connect(self.trsfrtDonnees)
        self.ui.buttonBox.rejected.connect(self.close)
        
    def trsfrtDonnees(self, idsortie):
        
    
        queryMatosAssur = QtSql.QSqlQuery(self.db)
        qMatosAssur = u"""INSERT INTO bdtravaux.t_matos_assur_pts(id_matos, codesite, nomsite, commune, typ_matos, dat_pose, 
            dat_vandal, dat_retrait, id_sortie, geom) VALUES ('{zr_idmatos}', '{zr_codesite}', '{zr_nomsite}', '{zr_commune}','{zr_typmatos}', '{zr_datpose}', '{zr_datvandal}', '{zr_retrait}', '{zr_idsortie}', {zr_thegeom})""".format (\
        zr_idmatos = self.ui.cbx_codesite.itemData(self.ui.cbx_codesite.currentIndex()),\
        zr_codesite = self.ui.cbx_auteur.itemData(self.ui.cbx_auteur.currentIndex()),\
        zr_nomsite = self.ui.cbx_annee.itemText(self.ui.cbx_annee.currentIndex()),\
        zr_commune = self.ui.cbx_habref.itemData(self.ui.cbx_habref.currentIndex()),\
        zr_typmatos = self.habcod,\
        zr_datpose = self.ui.cbx_hablat.itemText(self.ui.cbx_hablat.currentIndex()).replace("\'","\'\'"),\
        zr_datvandal = self.ui.cbx_habfr.itemText(self.ui.cbx_habfr.currentIndex()).replace("\'","\'\'"),\
        zr_retrait = self.ui.txt_comment.toPlainText().replace("\'","\'\'"),\
        zr_idsortie = v_syntax,\
        zr_thegeom = v_cahab)
        ok = queryMatosAssur.exec_(qMatosAssur)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête saisie données Matos à Assurer ratée')

    ############ En cours : adapter les zr_xxx pour récupérer toutes les données à insérer dans la table t_matos_assur_pts
   

    def recupDonnSortie(self, idsortie):
        #recup de données en fction de l'Id de la sortie. Pr afficher le site et les txts des étiqu dans composeur()
        querycodesite = QtSql.QSqlQuery(self.db)
        qcodesite = u"""select sor.codesite, (select nomsite from sites_cen.t_sitescen sit where sit.codesite=sor.codesite) as nomsite, (select loc_commune from sites_cen.t_sitescen sit where sit.codesite=sor.codesite) as communes, date_sortie from bdtravaux.sortie sor where sortie_id = {zr_sortie_id}""".format \
        (zr_sortie_id = str(idsortie)) #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        oksort = querycodesite.exec_(qcodesite)
        if not oksort:
            print u'Requête recupDonnSortie ratée'
        querycodesite.next()
        self.codedusite=querycodesite.value(0)
        self.nomdusite=querycodesite.value(1)
        self.communes=querycodesite.value(2)
        self.datesortie=querycodesite.value(3).toPyDate().strftime("%Y-%m-%d")






