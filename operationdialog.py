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
 *   it under the terms of the GNU General Public License as published by  * *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui, QtSql
from qgis.core import *
from ui_operation import Ui_operation
from convert_geoms import convert_geometries
import sys
# create the dialog for zoom to point


class OperationDialog(QtGui.QDialog):
    def __init__(self, iface):
        
        QtGui.QDialog.__init__(self)
        # Set up the user interface from QTDesigner.
        self.ui = Ui_operation()
        self.ui.setupUi(self)
        # référencement de iface dans l'interface (iface = interface de QGIS)
        self.iface = iface
        
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
        
        # Remplir la combobox "sortie" avec les champs date_sortie+site+redacteur de la table "sortie" 
        # issus de la table "sites"
        query = QtSql.QSqlQuery(self.db)
        # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        if query.exec_('select sortie_id, date_sortie, codesite, redacteur from bdtravaux.sortie order by date_sortie DESC LIMIT 30'):
            while query.next():
                self.ui.sortie.addItem(query.value(1).toString() + " " + query.value(2).toString() + " "+ query.value(3).toString(), query.value(0).toInt()[0])
            # voir la doc de la méthode additem d'une combobox : 1er paramètre = ce qu'on affiche, 
            # 2ème paramètre = ce qu'on garde en mémoire pour plus tard
            # .toInt renvoie deux paramètres. Le [0] précise qu'on ne veut récupérer que le premier, qui est l'entier 
            # (le 2ème para = boolean pour savoir si la conversion a marché)
        
        #connexions aux boutons OK et Annuler
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'), self.sauverOpe)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'), self.close)

    def actu_lblgeom(self):
        # Indiquer le nombre d'entités sélectionnées dans le contrôle lbl_geo et le type de géométrie.
        # En premier lieu, on compare la constante renvoyée par geometrytype() à celle renvoyée par les constante de QGis pour 
        # obtenir une chaîne de caractère : geometryType() ne renvoie que des constantes (0, 1 ou 2). Il faut donc ruser...
        geometrie=""
        if self.iface.activeLayer().geometryType() == QGis.Polygon:
            geometrie="polygone"
        elif self.iface.activeLayer().geometryType() == QGis.Line:
            geometrie="ligne"
        elif self.iface.activeLayer().geometryType() == QGis.Point:
            geometrie="point"
            #puis, on écrit la phrase qui apparaîtra dans lbl_geom
        self.ui.lbl_geom.setText(u"{nb_geom} géométries, de type {typ_geom}".format (nb_geom=self.iface.activeLayer().selectedFeatureCount(),\
        typ_geom=geometrie))
        
    def sauverOpe(self):
        geom2=convert_geometries([feature.geometry() for feature in self.iface.activeLayer().selectedFeatures()],QGis.Polygon) #compréhension de liste
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.operation_poly (sortie, plangestion, code_gh, typ_operat, descriptio, the_geom) values ({zr_sortie}, '{zr_plangestion}', '{zr_code_gh}', '{zr_ope_typ}', '{zr_libelle}', st_transform(st_setsrid(st_geometryfromtext ('{zr_the_geom}'),4326), 2154))""".format (zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()).toInt()[0],\
        zr_plangestion = self.ui.opprev.currentItem().text().split("/")[-1],\
        zr_code_gh = self.ui.opprev.currentItem().text().split("/")[1],\
        zr_ope_typ= self.ui.opreal.currentItem().text(),\
        zr_libelle= self.ui.descriptio.toPlainText(),\
        zr_the_geom= geom2.exportToWkt())
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
        print query
        self.close
