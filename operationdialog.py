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
 *   it under the terms of the GNU General Public License as published by  * *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui, QtSql, QtXml, Qt
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
from ui_operation import Ui_operation
from convert_geoms import convert_geometries
from composeur import composerClass


class OperationDialog(QtGui.QDialog):
    def __init__(self, iface):
        
        QtGui.QDialog.__init__(self)
        # Configure l'interface utilisateur issue de QTDesigner.
        self.ui = Ui_operation()
        self.ui.setupUi(self)
        # Référencement de iface dans l'interface (iface = interface de QGIS)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # Type de BD, hôte, utilisateur, mot de passe...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        self.db.setHostName("192.168.0.10") 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'La connexion est échouée')

        #Definition de URI pour extraire des couches des tables PG. Uri est utilisé dans les fonctions "afficher" et "composeur".
        #QgsDataSourceUri() permet d'aller chercher une table d'une base de données PostGis (cf. PyQGIS cookbook)
        self.uri = QgsDataSourceURI()
        # configure l'adresse du serveur (hôte), le port, le nom de la base de données, l'utilisateur et le mot de passe.
        self.uri.setConnection("192.168.0.10", "5432", "sitescsn", "postgres", "postgres")

        #Initialisations
        self.ui.chx_opechvol.setVisible(False)
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)

        # Connexions signaux-slots
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'), self.sauverOpeChoi)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.compoButton, QtCore.SIGNAL('clicked()'), self.creatComposer)
        self.connect(self.ui.sortie, QtCore.SIGNAL('currentIndexChanged(int)'), self.actu_gestprev_chxopechvol)
        # Si l'une des listes de choix est cliquée, connexion à la fonction activBoutons, qui vérifie qu'un item est sélectionné dans chaque pour donner accès aux boutons "OK" et "Dernier - Editer CR".
        self.connect(self.ui.opprev, QtCore.SIGNAL('itemSelectionChanged()'), self.activBoutons)
        self.connect(self.ui.opreal, QtCore.SIGNAL('itemSelectionChanged()'), self.activBoutons)
        self.connect(self.ui.prestataire, QtCore.SIGNAL('itemSelectionChanged()'), self.activBoutons)



    def actu_cbbx(self):
        self.blocActuGestPrev='1'
        self.ui.sortie.clear()
        # Remplir la combobox "sortie" avec les champs date_sortie+site de la table "sortie" et le champ sal_initia de la table "join_salaries"
        query = QtSql.QSqlQuery(self.db)  # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        querySortie=u"""select sortie_id, date_sortie, codesite, array_to_string(array(select distinct sal_initia from bdtravaux.join_salaries where id_joinsal=sortie_id), '; ') as salaries from bdtravaux.sortie order by sortie_id DESC LIMIT 30"""
        ok = query.exec_(querySortie)
        while query.next():
            self.ui.sortie.addItem(query.value(1).toPyDate().strftime("%Y-%m-%d") + " / " + str(query.value(2)) + " / "+ str(query.value(3)), int(query.value(0)))
        # 1er paramètre = ce qu'on affiche, 
        # 2ème paramètre = ce qu'on garde en mémoire pour plus tard
        # query.value(0) = le 1er élément renvoyé par le "select" d'une requête SQL. Et ainsi de suite...
        if not ok :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête remplissage sortie ratée')
        self.blocActuGestPrev='0'



    def actu_listeschoix(self):
        self.ui.opreal.clear()
        queryopes = QtSql.QSqlQuery(self.db)
        if queryopes.exec_('select * from bdtravaux.list_operations_cen order by operations'):
            while queryopes.next():
                self.ui.opreal.addItem(unicode(queryopes.value(1)))

        self.ui.prestataire.clear()
        queryoper = QtSql.QSqlQuery(self.db)
        if queryoper.exec_('select * from bdtravaux.list_operateur order by nom_oper'):
            while queryoper.next():
                self.ui.prestataire.addItem(unicode(queryoper.value(1)))



    def actu_lblgeom(self):
        # Indiquer le nombre d'entités sélectionnées dans le contrôle lbl_geo et le type de géométrie.
        # En premier lieu, on compare la constante renvoyée par geometrytype() à celle renvoyée par les constantes de QGis pour 
        # obtenir une chaîne de caractère : geometryType() ne renvoie que des constantes (0, 1 ou 2). Il faut donc ruser...
        if not self.iface.activeLayer():
            self.ui.lbl_geom.setText(u"0 points, lignes ou polygones sélectionnés")
        elif self.iface.activeLayer().type() == QgsMapLayer.RasterLayer:
            self.ui.lbl_geom.setText(u"0 points, lignes ou polygones sélectionnés")
        else:
            geometrie=""
            if self.iface.activeLayer().geometryType() == QGis.Polygon:
                geometrie="polygone"
            elif self.iface.activeLayer().geometryType() == QGis.Line:
                geometrie="ligne"
            elif self.iface.activeLayer().geometryType() == QGis.Point:
                geometrie="point"
                #puis, on écrit la phrase qui apparaîtra dans lbl_geom
            self.ui.lbl_geom.setText(u"{nb_geom} {typ_geom}(s) sélectionné(s)".format (nb_geom=self.iface.activeLayer().selectedFeatureCount(),\
            typ_geom=geometrie))



    def actu_gestprev_chxopechvol(self):
        if self.blocActuGestPrev=='1':
            return
        else:
            # Actualise la liste des opérations de gestion prévues en base de données et filtre selon le code du site
            self.ui.opprev.clear()
            #Récupération du code du site et de chantvol
            querycodesite = QtSql.QSqlQuery(self.db)
            qcodesite = u"""select codesite,chantvol from bdtravaux.sortie where sortie_id = {zr_sortie_id}""".format \
            (zr_sortie_id = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
            ok2 = querycodesite.exec_(qcodesite)
            if not ok2:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Requête recupCodeSite raté')
            querycodesite.next()
            self.codedusite=querycodesite.value(0)
            self.chantvol=querycodesite.value(1)

            query = QtSql.QSqlQuery(self.db)
            if query.exec_(u"""select prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_pdg from (select * from bdtravaux.list_gestprev_surf UNION select * from bdtravaux.list_gestprev_lgn UNION select * from bdtravaux.list_gestprev_pts) as gestprev where prev_codesite='{zr_codesite}' or prev_codesite='000' group by prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_pdg order by prev_codesite , prev_pdg , prev_codeope""".format (zr_codesite = self.codedusite)):
                while query.next():
                    self.ui.opprev.addItem(unicode(query.value(0)) + " / " + unicode(query.value(1)) + " / "+ unicode(query.value(2)) + " / "+ unicode(query.value(3)) + " / "+ unicode(query.value(4)))
            # Si la sortie contient un chantier de volontaire, la case à cocher "Chantier de volontaire" apparaît pour indiquer si l'opération courante fait partiue ou non du chantier de volontaire. Sinon, la case à cocher est cachée.
            if self.chantvol == True:
                self.ui.chx_opechvol.setVisible(True)
                self.ui.chx_opechvol.setChecked(True)
            else :
                self.ui.chx_opechvol.setVisible(False)
                # la liste "opprev" vient de changer. Les boutons "OK - Annuler" et "Dertnier - Editer CR" sont inactifs jusqu'à ce qu'un nouvel item soit sélectionné dans "opprev".
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
            self.ui.compoButton.setEnabled(0)



    def activBoutons(self):
        opprevlist = self.ui.opprev.selectedItems()
        opreallist = self.ui.opreal.selectedItems()
        prestalist = self.ui.prestataire.selectedItems()
        if len(opprevlist)!=0 and len(opreallist)!=0 and len(prestalist)!=0 :
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(1)
            self.ui.compoButton.setEnabled(1)



    def sauverOpeChoi(self):
        if self.sansgeom=='True':
            self.sauvOpeSansGeom()
        else:
            self.sauverOpe()



    def sauvOpeSansGeom(self):
        self.recupIdChantvol()
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u'insert into bdtravaux.operation_poly (sortie, plangestion, code_gh, typ_operat, descriptio, chantfini, ope_chvol) values ({zr_sortie}, \'{zr_plangestion}\', \'{zr_code_gh}\', \'{zr_ope_typ}\', \'{zr_libelle}\', \'{zr_chantfini}\',{zr_opechvol})'.format (\
        zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_plangestion = self.ui.opprev.currentItem().text().split("/")[-1],\
        zr_code_gh = self.ui.opprev.currentItem().text().split("/")[1],\
        zr_ope_typ= self.ui.opreal.currentItem().text().replace("\'","\'\'"),\
        zr_libelle= self.ui.descriptio.toPlainText().replace("\'","\'\'"),\
        zr_chantfini= str(self.ui.chantfini.isChecked()).lower(),\
        zr_opechvol = self.id_opechvol)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête sansgeom ratée')
        self.nom_table='operation_poly'
        self.rempliJoinOpe()
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)
        self.close



    def sauverOpe(self):
        # Fonction à lancer quans les boutons "OK" ou "Dernier - Editer CR" sont cliqués
        # Entre en base les infos sélectionnées dans QGIS, et saisies dans le formulaire par l'utilisateur
        # Gère les erreurs "pas assez de points sélectionnés pour construire une ligne ou un polygone"
        # Gère également la transformation géométrique, via le module convert_geoms


        # Récupération de la géométrie finale. On en déduit la table où sera stockée l'information, et on gère les erreurs 
        # "pas assez de points pour faire la transformation"
        geom_cbbx=self.ui.trsf_geom.itemText(self.ui.trsf_geom.currentIndex())
        if geom_cbbx == 'Points' :
            geom_output=QGis.Point
            self.nom_table='operation_pts'
        elif geom_cbbx == 'Lignes':
            geom_output=QGis.Line
            self.nom_table='operation_lgn'
            if self.iface.activeLayer().geometryType()==0:
                if self.iface.activeLayer().selectedFeatureCount()<2:
                    mess2pts=QtGui.QMessageBox()
                    mess2pts.setText(u'Pas assez de points sélectionnés')
                    mess2pts.setInformativeText(u'Il faut au moins 2 points pour faire une ligne. Merci d\'en sélectionner plus')
                    mess2pts.setIcon(QtGui.QMessageBox.Warning)
                    mess2pts.setStandardButtons(QtGui.QMessageBox.Ok)
                    ret = mess2pts.exec_()
                    return
        elif geom_cbbx == 'Surfaces':
            geom_output=QGis.Polygon
            self.nom_table='operation_poly'
            if self.iface.activeLayer().geometryType()==0:
                if self.iface.activeLayer().selectedFeatureCount()<3:
                    mess3pts=QtGui.QMessageBox()
                    mess3pts.setText(u'Pas assez de points sélectionnés')
                    mess3pts.setInformativeText(u'Il faut au moins 3 points pour faire un polygone. Merci d\'en sélectionner plus')
                    mess3pts.setIcon(QtGui.QMessageBox.Warning)
                    mess3pts.setStandardButtons(QtGui.QMessageBox.Ok)
                    ret = mess3pts.exec_()
                    return

        #copie des entités sélectionnées dans une couche "memory". Evite les problèmes avec les types de couches "non  éditables" (comme les GPX).
        coucheactive=self.iface.activeLayer()
        entselect=[QgsGeometry(feature.geometry()) for feature in coucheactive.selectedFeatures()]
        if entselect[0].type() == QGis.Line:
            typegeom='LineString'
        elif entselect[0].type() == QGis.Point:
            typegeom='Point'
        elif entselect[0].type() == QGis.Polygon:
            typegeom='Polygon'
        else: 
            print "ce ne sont pas des points, des lignes ou des polygones"
        self.iface.actionCopyFeatures().trigger()
        if self.iface.activeLayer().crs().authid() == u'EPSG:4326':
           memlayer=QgsVectorLayer("{zr_typegeom}?crs=epsg:4326".format(zr_typegeom = typegeom), "memlayer", "memory")
        if self.iface.activeLayer().crs().authid() == u'EPSG:2154':
           memlayer=QgsVectorLayer("{zr_typegeom}?crs=epsg:2154".format(zr_typegeom = typegeom), "memlayer", "memory")
        QgsMapLayerRegistry.instance().addMapLayer(memlayer, False)
        root = QgsProject.instance().layerTreeRoot()
        memlayerNode = QgsLayerTreeLayer(memlayer)
        root.insertChildNode(0, memlayerNode)
        self.iface.setActiveLayer(memlayer)
        memlayer.startEditing()
        self.iface.actionPasteFeatures().trigger()
        memlayer.commitChanges()

        #lancement de convert_geoms.py pour transformer les entités sélectionnées dans le type d'entités choisi.

                                #compréhension de liste : [fonction for x in liste]
        geom2=convert_geometries([QgsGeometry(feature.geometry()) for feature in memlayer.selectedFeatures()],geom_output)

        #export de la géométrie en WKT et transformation de la projection si les données ne sont pas saisies en Lambert 93
        if memlayer.crs().authid() == u'EPSG:2154':
            thegeom='st_setsrid(st_geometryfromtext (\'{zr_geom2}\'), 2154)'.format(zr_geom2=geom2.exportToWkt())
        elif memlayer.crs().authid() == u'EPSG:4326':
            thegeom='st_transform(st_setsrid(st_geometryfromtext (\'{zr_geom2}\'),4326), 2154)'.format(zr_geom2=geom2.exportToWkt())
        else :
            print u'La projection de la couche active n\'est pas supportée'

        #lancement de la fonction qui vérifie si l'opération fait partie d'un chantier de volontaires.
        self.recupIdChantvol()
        #lancement de la requête SQL qui introduit les données géographiques et du formulaire dans la base de données.
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.{zr_nomtable} (sortie, plangestion, code_gh, descriptio, chantfini, the_geom, ope_chvol) values ({zr_sortie}, '{zr_plangestion}', '{zr_code_gh}', '{zr_libelle}', '{zr_chantfini}', {zr_the_geom}, '{zr_opechvol}')""".format (zr_nomtable=self.nom_table,\
        zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_plangestion = self.ui.opprev.currentItem().text().split("/")[-1],\
        zr_code_gh = self.ui.opprev.currentItem().text().split("/")[1],\
#        zr_ope_typ = self.ui.opreal.currentItem().text().replace("\'","\'\'"),\
        zr_libelle = self.ui.descriptio.toPlainText().replace("\'","\'\'"),\
        zr_chantfini = str(self.ui.chantfini.isChecked()).lower(),\
        zr_the_geom = thegeom,\
        #geom2.exportToWkt(),\
        #st_transform(st_setsrid(st_geometryfromtext ('{zr_the_geom}'),4326), 2154) si besoin de transformer la projection
        zr_opechvol = self.id_opechvol)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête sauver Ope ratée')
#            print unicode(query)
        self.rempliJoinOpe()
        self.iface.setActiveLayer(coucheactive)
        QgsMapLayerRegistry.instance().removeMapLayer(memlayer.id())
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)
        self.close



    def rempliJoinOpe(self):
    #remplissage des tables join_operateur et join_operations avec les prestataires et eles types d'opés sélectionnés par l'utilisateur
        #récupération de id_oper dans la table nom_table pour le remettre dans join_operateurs et join_operations
        queryidoper = QtSql.QSqlQuery(self.db)
        qidoper = u"""select id_oper from bdtravaux.{zr_nomtable} order by id_oper desc limit 1""".format (zr_nomtable=self.nom_table)
        ok2=queryidoper.exec_(qidoper)
        if not ok2:
            QtGui.QMessagebox.warning(self, 'Alerte', u'Pas trouvé id de l opération')
        queryidoper.next()
        self.id_oper = queryidoper.value(0)

        #remplissage de la table join_operateurs : id_oper et noms du (des) prestataire(s)
        for item in xrange (len(self.ui.prestataire.selectedItems())):
            querypresta = QtSql.QSqlQuery(self.db)
            qpresta = u"""insert into bdtravaux.join_operateurs (id_joinop, operateurs) values ({zr_idjoinop}, '{zr_operateur}')""".format (zr_idjoinop = self.id_oper, zr_operateur = self.ui.prestataire.selectedItems()[item].text().replace("\'","\'\'"))
            ok3 = querypresta.exec_(qpresta)
            if not ok3:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des prestas en base ratée')
                querypresta.next()

        #remplissage de la table join_operation : id_oper et noms du (des) type(s) d'opération
        for item in xrange (len(self.ui.opreal.selectedItems())):
            querytypope = QtSql.QSqlQuery(self.db)
            qtypope = u"""insert into bdtravaux.join_typoperation (id_jointyp, typoperation) values ({zr_idjointyp}, '{zr_typoperation}')""".format (zr_idjointyp = self.id_oper, zr_typoperation = self.ui.opreal.selectedItems()[item].text().replace("\'","\'\'"))
            ok4 = querytypope.exec_(qtypope)
            # print qtypope
            if not ok4:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des types d opérations en base ratée')
                querytypope.next()



    def recupIdChantvol(self):
        #récupération de l'id du chantier du volontaire si l'opération en fait partie
        if self.ui.chx_opechvol.isChecked():
            queryopechvol = QtSql.QSqlQuery(self.db)
            queryvol = u"""select id_chvol from bdtravaux.ch_volont where sortie={zr_sortie}""".format(zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
            ok = queryopechvol.exec_(queryvol)
            if not ok :
                QtGui.QMessageBox.warning(self, 'Alerte', u'Pas trouvé Id du chantier de volontaire')
            queryopechvol.next()
            self.id_opechvol = queryopechvol.value(0)
            if self.id_opechvol==None :
                self.id_opechvol='0'
        else:
            self.id_opechvol='0'



    def creatComposer(self):
        #Intégration en base de la dernière opération saisie
        self.sauverOpeChoi()
        #Création et remplissage de l'objet id_sortie avec l'identifiant de la sortie courante, à partir de la combobox "sortie"
        id_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        print "id_sortie="+str(id_sortie)
        #lancement de la fonction Composer dans le module composeurClass avec le paramètre id_sortie
        self.obj_compo=composerClass()
        self.obj_compo.Composer(id_sortie)
        # Afficher le formulaire "bdtravauxdialog.py" devant iface, et l'activer.
        self.obj_compo.composerView.composerViewHide.connect(self.raiseModule)
        #lancement de la fonction afterComposeurClose dans le module composerClass pour effacer les couches ayant servi au composeur, et réafficher les autres.
        self.obj_compo.composerView.composerViewHide.connect(self.obj_compo.afterComposerClose)



    def raiseModule(self):
        self.raise_()
        self.activateWindow()

