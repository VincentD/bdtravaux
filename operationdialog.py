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
        self.db.setHostName("127.0.0.1") 
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
        self.uri.setConnection("127.0.0.1", "5432", "sitescsn", "postgres", "postgres")

        #Initialisations
        self.ui.chx_opechvol.setVisible(False)
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)

        #Mise à jour du label "lbl_futopeid", affichant l'id de la future opération.
        queryfutopeid = QtSql.QSqlQuery(self.db)
        if queryfutopeid.exec_(u"""select last_value+1 from bdtravaux.operation_lgnpolypts_operation_id_seq"""):
            while queryfutopeid.next():
                self.ui.lbl_futopeid.setText(str(queryfutopeid.value(0)))

        # Connexions signaux-slots
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'), self.sauverOpeChoi)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.bbx_edokannul, QtCore.SIGNAL('accepted()'), self.sauverOpeModifs)
        self.connect(self.ui.bbx_edokannul, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.compoButton, QtCore.SIGNAL('clicked()'), self.creatComposer)
        self.connect(self.ui.sortie, QtCore.SIGNAL('currentIndexChanged(int)'), self.actu_gestprev_opechvol_edope)
        # Si l'une des listes de choix est cliquée, connexion à la fonction activBoutons, qui vérifie qu'un item est sélectionné dans chaque pour donner accès aux boutons "OK" et "Dernier - Editer CR".
        self.connect(self.ui.opprev, QtCore.SIGNAL('itemSelectionChanged()'), self.activBoutons)
        self.connect(self.ui.opreal, QtCore.SIGNAL('itemSelectionChanged()'), self.activBoutons)
        self.connect(self.ui.prestataire, QtCore.SIGNAL('itemSelectionChanged()'), self.activBoutons)
        self.connect(self.ui.cbx_edoperation, QtCore.SIGNAL('currentIndexChanged(int)'), self.fillEditOpeControls)
        self.connect(self.ui.pbt_supprope, QtCore.SIGNAL('clicked()'), self.supprOpe)
        self.connect(self.ui.pbt_edgeom, QtCore.SIGNAL('clicked()'), self.modifGeom)



#####################
# Actualisation des listes de choix dans les Tab "saisie" et "modification" au démarrage du module

    def actu_cbbx(self):
        self.ui.sortie.clear()
        # Remplir la combobox "sortie" avec les champs date_sortie+site de la table "sortie" et le champ sal_initia de la table "join_salaries"
        query = QtSql.QSqlQuery(self.db)  # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        querySortie=u"""select sortie_id, date_sortie, codesite, array_to_string(array(select distinct sal_initia from bdtravaux.join_salaries where id_joinsal=sortie_id), '; ') as salaries from bdtravaux.sortie order by date_sortie DESC"""
        ok = query.exec_(querySortie)
        while query.next():
            self.ui.sortie.addItem(query.value(1).toPyDate().strftime("%Y-%m-%d") + " / " + str(query.value(2)) + " / "+ str(query.value(3)), int(query.value(0)))
        # 1er paramètre = ce qu'on affiche, 
        # 2ème paramètre = ce qu'on garde en mémoire pour plus tard
        # query.value(0) = le 1er élément renvoyé par le "select" d'une requête SQL. Et ainsi de suite...
        if not ok :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête remplissage sortie ratée')
        self.ui.sortie.setCurrentIndex(0)




    def actu_listeschoix(self):
        self.ui.opreal.clear()
        self.ui.lst_edtypope.clear()
        queryopes = QtSql.QSqlQuery(self.db)
        if queryopes.exec_('select * from bdtravaux.list_operations_cen order by operations'):
            while queryopes.next():
                self.ui.opreal.addItem(unicode(queryopes.value(1)))
                self.ui.lst_edtypope.addItem(unicode(queryopes.value(1)))

        self.ui.prestataire.clear()
        self.ui.lst_edpresta.clear()
        queryoper = QtSql.QSqlQuery(self.db)
        if queryoper.exec_('select * from bdtravaux.list_operateur order by nom_oper'):
            while queryoper.next():
                self.ui.prestataire.addItem(unicode(queryoper.value(1)))
                self.ui.lst_edpresta.addItem(unicode(queryoper.value(1)))



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



    def activBoutons(self):
        opprevlist = self.ui.opprev.selectedItems()
        opreallist = self.ui.opreal.selectedItems()
        prestalist = self.ui.prestataire.selectedItems()
        if len(opprevlist)!=0 and len(opreallist)!=0 and len(prestalist)!=0 :
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(1)
            self.ui.compoButton.setEnabled(1)




######################"
# Actualisation des combobox et listes de choix lorsque l'utilisateur choisit une sortie

    def actu_gestprev_opechvol_edope(self):
        if self.ui.sortie.itemData(self.ui.sortie.currentIndex())==None :
            return
        else :
            # Quand l'utilisateur sélectionne une sortie, actualisation des contrôles "opprev", "lst_edopeprev", "cbx_edoperation" et gestion de la case à cocher "chx_opechvol".
            # opprev et lst_edopeprev : Actualise les listes des opérations de gestion prévues en base de données (liste de l'onglet "saisie" et liste de l'onglet "modification") et filtre selon le code du site
            self.ui.opprev.clear()
            self.ui.lst_edopeprev.clear()
            #Récupération du code du site et de chantvol
            querycodesite = QtSql.QSqlQuery(self.db)
            qcodesite = u"""select codesite,chantvol from bdtravaux.sortie where sortie_id = {zr_sortie_id}""".format \
            (zr_sortie_id = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
            ok2 = querycodesite.exec_(qcodesite)
            if not ok2:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Requête recupCodeSite ratée')
            querycodesite.next()
            self.codedusite=querycodesite.value(0)
            self.chantvol=querycodesite.value(1)

            query = QtSql.QSqlQuery(self.db)
            if query.exec_(u"""select prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_annprev, prev_pdg from (select * from bdtravaux.list_gestprev_surf UNION select * from bdtravaux.list_gestprev_lgn UNION select * from bdtravaux.list_gestprev_pts) as gestprev where prev_codesite='{zr_codesite}' or prev_codesite='000' group by prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_annprev, prev_pdg order by prev_codesite , prev_pdg , prev_codeope""".format (zr_codesite = self.codedusite)):
                while query.next():
                    self.ui.opprev.addItem(unicode(query.value(0)) + " / " + unicode(query.value(1)) + " / "+ unicode(query.value(2)) + " / "+ unicode(query.value(3)) + " / "+ unicode(query.value(4)) + " / " + unicode(query.value(5)))
                    self.ui.lst_edopeprev.addItem(unicode(query.value(0)) + " / " + unicode(query.value(1)) + " / "+ unicode(query.value(2)) + " / "+ unicode(query.value(3)) + " / "+ unicode(query.value(4)) + " / " + unicode(query.value(5)))


            # mise à jour du label "lbl_idsortiesel", affichant l'id de la sortie sélectionnée
            self.ui.lbl_idsortiesel.setText(str(self.ui.sortie.itemData(self.ui.sortie.currentIndex())))

            # cbx_edoperation : Actualise la combobox de choix de l'opération à modifier. La liste est filtrée selon la sortie sélectionnée.
            self.blocFillEdOpContr = '0'            
            self.ui.cbx_edoperation.clear()
            queryope = QtSql.QSqlQuery(self.db)
            if queryope.exec_(u"""SELECT operation_id, plangestion, code_gh, CASE WHEN geometrytype(the_geom) IN ('MULTIPOINT', 'POINT') THEN 'pts' WHEN geometrytype(the_geom) IN ('MULTILINESTRING', 'LINESTRING') THEN 'lgn' WHEN geometrytype(the_geom) IN ('MULTIPOLYGON', 'POLYGON') THEN 'surf' END as typ_graph, LEFT(array_to_string(array(select distinct typoperation from bdtravaux.join_typoperation where id_jointyp=id_oper), '; '),45)||'...'::text as typope, LEFT(descriptio,45)||'...'::text as descr, chantfini FROM (SELECT * FROM bdtravaux.operation_poly UNION SELECT * FROM bdtravaux.operation_lgn UNION SELECT * FROM bdtravaux.operation_pts) as gestreal WHERE sortie = {zr_sortie} OR operation_id='0' ORDER BY operation_id""".format(zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))):
                while queryope.next():
                     self.ui.cbx_edoperation.addItem(unicode(queryope.value(1)) + " / " + unicode(queryope.value(2)) + " / "+ unicode(queryope.value(3)) + " / "+ unicode(queryope.value(4)) + " / "+ unicode(queryope.value(5)), int(queryope.value(0)))
            self.blocFillEdOpContr = '1'

            # chx_opechvol : Si la sortie contient un chantier de volontaire, la case à cocher "Chantier de volontaire" apparaît pour indiquer si l'opération courante fait partie ou non du chantier de volontaire. Sinon, la case à cocher est cachée.
            if self.chantvol == True:
                self.ui.chx_opechvol.setVisible(True)
                self.ui.chx_opechvol.setChecked(True)
            else :
                self.ui.chx_opechvol.setVisible(False)
            # la liste "opprev" vient de changer. Les boutons "OK - Annuler" et "Dernier - Editer CR" sont inactifs jusqu'à ce qu'un nouvel item    soit sélectionné dans "opprev".
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
            self.ui.compoButton.setEnabled(0)



######################"
# Actualisation des combobox et listes de choix lorsque l'utilisateur choisit une opération (Tab "modification")


    def fillEditOpeControls(self):

        if self.blocFillEdOpContr == '1':

        # activation des boutons "supprimer", "OK" et "modif graphique" pour suppression ou modification de l'opération sélectionnée
            self.ui.pbt_supprope.setEnabled(1)
            self.ui.pbt_edgeom.setEnabled(1)
            self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(1)

        # Mise à jour du label "lbl_opeid", affichant l'id de l'opération sélectionnée
            self.ui.lbl_opeid.setText(str(self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex())))

        # Remplissage des contrôles du Tab "Modifications" du module "Opérations"
            queryfillope = QtSql.QSqlQuery(self.db)
            qfillope = u"""SELECT array_to_string(array(select distinct typoperation from bdtravaux.join_typoperation where id_jointyp=id_oper), '; ') as typope, array_to_string(array(select distinct operateurs from bdtravaux.join_operateurs where id_joinop=id_oper), '; ') as presta, descriptio, chantfini, plangestion, code_gh, CASE WHEN geometrytype(the_geom) IN ('MULTIPOINT', 'POINT') THEN 'pts' WHEN geometrytype(the_geom) IN ('MULTILINESTRING', 'LINESTRING') THEN 'lgn' WHEN geometrytype(the_geom) IN ('MULTIPOLYGON', 'POLYGON') THEN 'surf' END as typ_graph FROM (SELECT * FROM bdtravaux.operation_poly UNION SELECT * FROM bdtravaux.operation_lgn UNION SELECT * FROM bdtravaux.operation_pts) as gestreal WHERE operation_id={zr_ope}""".format(zr_ope = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
            ok6 = queryfillope.exec_(qfillope)
            if not ok6 :
                QtGui.QMessageBox.warning(self, 'Alerte', u'Remplissage des contrôles dans le module operations raté')
            queryfillope.next()
            self.ui.txt_eddescr.setText(unicode(queryfillope.value(2)))
            print bool(queryfillope.value(3))
            self.ui.chx_edopeterm.setChecked(bool(queryfillope.value(3)))

        #Sélection d'items dans une liste (type d'opération réalisé)
            list_typope = queryfillope.value(0).split("; ")
            for y in xrange (self.ui.lst_edtypope.count()):
                typope=self.ui.lst_edtypope.item(y)
                for x in list_typope:
                    if unicode(typope.text())==x:
                        typope.setSelected(True) 

        #Sélection d'items dans une liste (prestataires)
            list_presta = queryfillope.value(1).split("; ")
            for y in xrange (self.ui.lst_edpresta.count()):
                presta=self.ui.lst_edpresta.item(y)
                for x in list_presta:
                    if unicode(presta.text())==x:
                        presta.setSelected(True) 
        
        #Sélection d'items dans une liste (opérations prévues)
            prevu_bd = " "+str(queryfillope.value(4))+" "+str(queryfillope.value(5))+" "
            for y in xrange (self.ui.lst_edopeprev.count()):
                prevu_lst=self.ui.lst_edopeprev.item(y).text().split("/")[4]+self.ui.lst_edopeprev.item(y).text().split("/")[1]
                if prevu_bd==prevu_lst:
                    self.ui.lst_edopeprev.item(y).setSelected(True)

        # désignation de la table dans laquelle on va modifier / supprimer des données
            self.typgeom = str(queryfillope.value(6))
            if self.typgeom == 'pts':
                self.tablemodif = 'operation_pts'
            elif self.typgeom == 'lgn':
                self.tablemodif = 'operation_lgn'
            elif self.typgeom == 'surf':
                self.tablemodif = 'operation_poly'
            else:
                self.tablemodif = 'operation_poly'
                print "pas trouvé la géométrie"

        # récupération de l'identifiant de l'opération "id_oper". Servira à sélectionner les données à modifier / supprimer dans les tables join_typeoperation et join_operateur
            queryjoinid = QtSql.QSqlQuery(self.db)
            qjoinid = u"""SELECT id_oper FROM bdtravaux.{zr_table} ope LEFT JOIN bdtravaux.join_typoperation typ ON (ope.id_oper = typ.id_jointyp) WHERE operation_id = {zr_opeid}""".format(\
            zr_table = self.tablemodif,
            zr_opeid = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
            ok2 = queryjoinid.exec_(qjoinid)
            if not ok2 :
                QtGui.QMessageBox.warning(self, 'Alerte', u'Récup id_oper ratée')
            queryjoinid.next()
            self.id_oper_modif = queryjoinid.value(0)




######################"
# Sauvegarde en base des nouvelles données saisies par l'utilisateur (Tab "saisie")


    def sauverOpeChoi(self):
        if self.sansgeom=='True':
            self.sauvOpeSansGeom()
        else:
            self.sauverOpe()



    def sauvOpeSansGeom(self):
        self.recupIdChantvol()
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u'insert into bdtravaux.operation_poly (sortie, descriptio, chantfini, ope_chvol) values ({zr_sortie}, \'{zr_libelle}\', \'{zr_chantfini}\',{zr_opechvol})'.format (\
        zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_libelle= self.ui.descriptio.toPlainText().replace("\'","\'\'"),\
        zr_chantfini= str(self.ui.chantfini.isChecked()).lower(),\
        zr_opechvol = self.id_opechvol)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête sansgeom ratée')
        self.nom_table='operation_poly'
        self.rempliJoin()
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

        # Création de la couche memlayer et début de la session d'édition
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

        # Pour chaque entité sélectionnée, si elle est multipartie, on ajoute chacune de ses parties individuellement à la couche memlayer. Sinon, on l'ajoute directement à "memlayer". Puis, on clot la session d'édition et on sélectionne toutes les entités de memlayer.
        for feature in coucheactive.selectedFeatures() :
            geom = feature.geometry()
            temp_feature = QgsFeature(feature)
            # check if feature geometry is multipart
            if geom.isMultipart():
                # if feature is multipart creates a new feature using the geometry of each part
                for part in geom.asGeometryCollection ():
                    temp_feature.setGeometry(part)
                    memlayer.dataProvider().addFeatures([temp_feature])
                    memlayer.updateExtents()
                # if feature is singlepart, simply adds it to the layer memory
            else :
                temp_feature.setGeometry(geom)
                memlayer.dataProvider().addFeatures([temp_feature])
                memlayer.updateExtents()
        memlayer.commitChanges()
        print "memlayercount="+str(memlayer.featureCount())
        memlayer.commitChanges()
        memlayer.selectAll()

#        self.iface.actionCopyFeatures().trigger()
#        self.iface.actionPasteFeatures().trigger()


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
        query = u"""insert into bdtravaux.{zr_nomtable} (sortie, descriptio, chantfini, the_geom, ope_chvol) values ({zr_sortie}, '{zr_libelle}', '{zr_chantfini}', {zr_the_geom}, '{zr_opechvol}')""".format (zr_nomtable=self.nom_table,\
        zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_libelle = self.ui.descriptio.toPlainText().replace("\'","\'\'"),\
        zr_chantfini = str(self.ui.chantfini.isChecked()).lower(),\
        zr_the_geom = thegeom,\
        #geom2.exportToWkt(),\
        #st_transform(st_setsrid(st_geometryfromtext ('{zr_the_geom}'),4326), 2154) si besoin de transformer la projection
        zr_opechvol = self.id_opechvol)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête sauver Ope ratée')
        self.rempliJoin()
        self.iface.setActiveLayer(coucheactive)
        QgsMapLayerRegistry.instance().removeMapLayer(memlayer.id())
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)
        self.close



    def rempliJoin(self):
    #remplissage des tables join_operateur, join_operations et join_opeprevues avec les prestas, les types d'opés et les GH sélect par l'utilisateur
        #récupération de id_oper dans la table nom_table pour le remettre dans join_operateurs, join_operations et join_opeprevues
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

        #remplissage de la table join_operation : id_oper et noms du (des) type(s) d'opération
        for item in xrange (len(self.ui.opreal.selectedItems())):
            querytypope = QtSql.QSqlQuery(self.db)
            qtypope = u"""insert into bdtravaux.join_typoperation (id_jointyp, typoperation) values ({zr_idjointyp}, '{zr_typoperation}')""".format (zr_idjointyp = self.id_oper, zr_typoperation = self.ui.opreal.selectedItems()[item].text().replace("\'","\'\'"))
            ok4 = querytypope.exec_(qtypope)
            if not ok4:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des types d opérations en base ratée')

        #remplissage de la table join_opeprevues : id_oper, code GH, ype d'opé, libelle de l'opé, année prévue et pdg où l'opé est rpévue
        for item in xrange (len(self.ui.opprev.selectedItems())):
            queryopeprev = QtSql.QSqlQuery(self.db)
            qopeprev = u"""insert into bdtravaux.join_opeprevues (id_joinprev, codeope, typeope, lblope, anneeprev, pdg, anneetheo, libopepdg) values ({zr_idjoinprev}, '{zr_codeope}', '{zr_typeope}', '{zr_lblope}', '{zr_anneeprev}', '{zr_pdg}')""".format (\
            zr_idjoinprev = self.id_oper,\
            zr_codeope = self.ui.opprev.selectedItems()[item].text().split(" / ")[1].replace("\'","\'\'"),\
            zr_typeope = self.ui.opprev.selectedItems()[item].text().split(" / ")[2].replace("\'","\'\'"),\
            zr_lblope = self.ui.opprev.selectedItems()[item].text().split(" / ")[3].replace("\'","\'\'"),\
            zr_anneeprev = self.ui.opprev.selectedItems()[item].text().split(" / ")[4].replace("\'","\'\'"),\
            zr_pdg = self.ui.opprev.selectedItems()[item].text().split(" / ")[5].replace("\'","\'\'"))
            ok5 = queryopeprev.exec_(qopeprev)
            if not ok5:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie en base des opérations prévues ratée')



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



######################
# Sauvegarde en base des données modifiées par l'utilisateur (Tab "modification")

    def sauverOpeModifs(self):
    # sauvegarde des modifications d'une opération

        # mise à jour de la table "operation_xxx"
        querysavemodope = QtSql.QSqlQuery(self.db)
        qsavmodo = u"""UPDATE bdtravaux.{zr_table} SET descriptio = '{zr_descr}' , plangestion = '{zr_plangestion}' , code_gh = '{zr_codegh}' , chantfini='{zr_chantfini}' WHERE operation_id={zr_opeid}""".format (\
        zr_table = self.tablemodif,\
        zr_descr = self.ui.txt_eddescr.toPlainText().replace("\'","\'\'"),\
        zr_plangestion = self.ui.lst_edopeprev.selectedItems()[0].text().split(" / ")[4],\
        zr_codegh = self.ui.lst_edopeprev.selectedItems()[0].text().split(" / ")[1],\
        zr_chantfini = str(self.ui.chx_edopeterm.isChecked()).lower(),\
        zr_opeid = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
        ok = querysavemodope.exec_(qsavmodo)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Mise à jour opération ratée')

        # mise à jour de la table join_typoperation
            #suppression des types d'opération appartenant à l'opération modifiée
        querysupprtyp = QtSql.QSqlQuery(self.db)
        qsupprtyp = u"""DELETE FROM bdtravaux.join_typoperation WHERE id_jointyp = {zr_idoper}""".format(\
        zr_idoper = self.id_oper_modif)
        ok3 = querysupprtyp.exec_(qsupprtyp)
        if not ok3 :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression des types d opération en base ratée')
        print "types opés en trop supprimes"

            #ajout de la liste de types d'opération modifiée
        for item in xrange (len(self.ui.lst_edtypope.selectedItems())):
            querymodiftyp = QtSql.QSqlQuery(self.db)
            qmodtyp = u"""insert into bdtravaux.join_typoperation (id_jointyp, typoperation) values ({zr_idjointyp}, '{zr_typope}')""".format (\
            zr_idjointyp = self.id_oper_modif,\
            zr_typope = self.ui.lst_edtypope.selectedItems()[item].text().replace("\'","\'\'"))
            ok4 = querymodiftyp.exec_(qmodtyp)
            if not ok4:
               QtGui.QMessageBox.warning(self, 'Alerte', u'Ajout des nvx types d opés en base ratée')
            querymodiftyp.next()
            print "types opés ajoutés"       

        # mise à jour de la table join_operateur
            #suppression des opérateurs appartenant à l'opération modifiée
        querysupprprest = QtSql.QSqlQuery(self.db)
        qsupprprest = u"""DELETE FROM bdtravaux.join_operateurs WHERE id_joinop = {zr_idoper}""".format(\
        zr_idoper = self.id_oper_modif)
        ok5 = querysupprprest.exec_(qsupprprest)
        if not ok5 :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression des opérateurs en base ratée')
        print "opérateurs en trop supprimes"

            #ajout de la liste des opérateurs modifiée
        for item in xrange (len(self.ui.lst_edpresta.selectedItems())):
            querymodifprest = QtSql.QSqlQuery(self.db)
            qmodprest = u"""insert into bdtravaux.join_operateurs (id_joinop, operateurs) values ({zr_idjoinop}, '{zr_presta}')""".format (\
            zr_idjoinop = self.id_oper_modif,\
            zr_presta = self.ui.lst_edpresta.selectedItems()[item].text().replace("\'","\'\'"))
            ok6 = querymodifprest.exec_(qmodprest)
            if not ok6:
               QtGui.QMessageBox.warning(self, 'Alerte', u'Ajout des nvx opéretaurs en base ratée')
            querymodifprest.next()
            print "opérateurs ajoutés"       

        # Désactivation des bouton "OK", "modif Geom" et "Supprimer" jusqu'à la prochaine sélection d'une opération
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)

        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.close()


    def modifGeom(self):
        root = QgsProject.instance().layerTreeRoot()
        reqwhere="""operation_id="""+str(self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))+""" and the_geom IS NOT NULL""" 
        self.uri.setDataSource("bdtravaux", str(self.tablemodif), "the_geom", reqwhere, "operation_id") # schéma, table, col géom , requête, pkey
        self.opeModif=QgsVectorLayer(self.uri.uri(), u'modifications', "postgres") # nom qui sera affiché ds QGIS, type de base
        # Intégration dans le MapLayerRegistry pour pouvoir l'utiliser, MAIS sans l'importer dans l'arbo (d'où le False)
        QgsMapLayerRegistry.instance().addMapLayer(self.opeModif, False)
        # Intégration de la couche dans l'arboresecnce, à l'index 0 (c'est à dire en haut de l'arborescence)
        root.insertLayer(0, self.opeModif)
        self.iface.setActiveLayer(self.opeModif) # couche active
        symbols = self.opeModif.rendererV2().symbols() # définit la symbologie de la couche
        symbol = symbols[0]
        symbol.setColor(QtGui.QColor.fromRgb(255,0,0))
        if self.tablemodif == 'operation_poly': # si polygon, alors transparence
            self.opeModif.setLayerTransparency(50)
        self.iface.legendInterface().refreshLayerSymbology(self.opeModif)
        self.iface.actionZoomToLayer().trigger() # zoome sur la couche
        self.lower() # le module "opération" passe en arrière-plan
        self.connect(self.opeModif, QtCore.SIGNAL('editingStopped()'), self.sauvModifGeom) # quand modifs sauvées, lancer la suite 

    def sauvModifGeom(self):
        self.raise_() # le formulaire "opérations" passe en avant-plan
        # Désactivation des bouton "OK", "modif Geom" et "Supprimer" jusqu'à la prochaine sélection d'une opération
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.timeoutTimer = QtCore.QTimer() # attendre une seconde (pour que QGIS ait le temps d'enregistrer la couche), puis la supprimer.
        self.timeoutTimer.singleShot(1000, self.removeModifiedLayer)

    def removeModifiedLayer(self):
        QgsMapLayerRegistry.instance().removeMapLayer(self.opeModif.id()) # retrait de la couche





######################"
# Suppression d'opérations

    def supprOpe(self):

        # suppression des données dans la table "join_operateurs"        
        querysupprprest = QtSql.QSqlQuery(self.db)
        qsupprprest = u"""DELETE FROM bdtravaux.join_operateurs WHERE id_joinop = {zr_idjoinop}""".format(\
        zr_idjoinop = self.id_oper_modif)
        ok1 = querysupprprest.exec_(qsupprprest)
        if not ok1:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression prestataires ratée')

        # suppression des données dans la table "join_typoperation"        
        querysupprtyp = QtSql.QSqlQuery(self.db)
        qsupprtyp = u"""DELETE FROM bdtravaux.join_typoperation WHERE id_jointyp = {zr_idjointyp}""".format(\
        zr_idjointyp = self.id_oper_modif)
        ok2 = querysupprtyp.exec_(qsupprtyp)
        if not ok2:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression types opération ratée')

        # suppression des données dans la table "operation_xxx"        
        querysupprope = QtSql.QSqlQuery(self.db)
        qsupprope = u"""DELETE FROM bdtravaux.{zr_table} WHERE operation_id={zr_opeid}""".format(\
        zr_table = self.tablemodif,
        zr_opeid = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
        ok3 = querysupprope.exec_(qsupprope)
        if not ok3:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression opération ratée')

        # Désactivation des bouton "OK", "modif Geom" et "Supprimer" jusqu'à la prochaine sélection d'une opération
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)

        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.close()




######################"
# Lancement du composeur au clic sur le bouton "Dernier - Editer CR"


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

