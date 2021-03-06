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
from bdt_convert_geoms import convert_geometries
from bdt_composeur import composerClass
from bdt_matosassur_dialog import matosAssurDialog


class OperationDialog(QtGui.QDialog):
    def __init__(self, iface):
        
        QtGui.QDialog.__init__(self)
        # Configure l'interface utilisateur issue de QTDesigner.
        self.ui = Ui_operation()
        self.ui.setupUi(self)
        # Référencement de iface dans l'interface (iface = interface de QGIS)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # Connexion à la base de données. Type de BD, hôte, utilisateur, mot de passe...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        self.db.setHostName("192.168.0.10") 
        self.db.setPort(5432) 
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
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.lst_edopeprev.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setText("OK Modif")
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
        # Remplir la combobox "sortie" avec les champs date_sortie+site+redacteur+sortie_id de la table "sortie" et les champs sal_initia de la table "join_salaries"
        query = QtSql.QSqlQuery(self.db)  # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        querySortie=u"""select sortie_id, date_sortie, codesite, (SELECT string_agg(left(word, 1), '') FROM (select unnest(string_to_array(btrim(redacteur,'_'), ' ')) FROM bdtravaux.sortie b WHERE b.sortie_id=a.sortie_id) t(word)) as redacinit, array_to_string(array(select distinct sal_initia from bdtravaux.join_salaries where id_joinsal=sortie_id), '; ') as salaries from bdtravaux.sortie a order by date_sortie DESC """

        ok = query.exec_(querySortie)
        while query.next():
            self.ui.sortie.addItem(query.value(1).toPyDate().strftime("%Y-%m-%d") + " / " + str(query.value(2)) + " / "+ str(query.value(3)) + " - "+ str(query.value(4)) + " / "+str(query.value(0)), int(query.value(0)))
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
                if self.sansgeom == 'True':
                    matosassur = queryopes.value(2)
                    if matosassur == True:
                        self.ui.opreal.item(self.ui.opreal.count()-1).setHidden(True)
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
                self.ui.trsf_geom.setCurrentIndex(2)
            elif self.iface.activeLayer().geometryType() == QGis.Line:
                geometrie="ligne"
                self.ui.trsf_geom.setCurrentIndex(1)
            elif self.iface.activeLayer().geometryType() == QGis.Point:
                geometrie="point"
                self.ui.trsf_geom.setCurrentIndex(0)
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

            # 0. Mise à jour du label "lbl_opeid", affichant l'id de l'opération sélectionnée
            self.ui.cbx_edoperation.setCurrentIndex(0)
            self.ui.lbl_opeid.setText(str(self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex())))

            # 1. opprev et lst_edopeprev : Actualise les listes des opérations de gestion prévues en base de données (liste de l'onglet "saisie" et liste de l'onglet "modification") et filtre selon le code du site
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
            
            # Récupération des données de gestion prévue en fonction du code du site.
            query = QtSql.QSqlQuery(self.db)
            if query.exec_(u"""select prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_annprev, prev_pdg from (select * from bdtravaux.list_gestprev_surf UNION select * from bdtravaux.list_gestprev_lgn UNION select * from bdtravaux.list_gestprev_pts) as gestprev where (prev_codesite='{zr_codesite}' or prev_codesite='000') and prev_pdgec='t' group by prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_annprev, prev_pdg order by prev_codesite , prev_pdg , prev_codeope""".format (zr_codesite = self.codedusite)):
                while query.next():
                    self.ui.opprev.addItem(unicode(query.value(0)) + " / " + unicode(query.value(1)) + " / "+ unicode(query.value(2)) + " / "+ unicode(query.value(3)) + " / "+ unicode(query.value(4)) + " / " + unicode(query.value(5)))
                    self.ui.lst_edopeprev.addItem(unicode(query.value(0)) + " / " + unicode(query.value(1)) + " / "+ unicode(query.value(2)) + " / "+ unicode(query.value(3)) + " / "+ unicode(query.value(4)) + " / " + unicode(query.value(5)))


            # mise à jour du label "lbl_idsortiesel", affichant l'id de la sortie sélectionnée
            self.ui.lbl_idsortiesel.setText(str(self.ui.sortie.itemData(self.ui.sortie.currentIndex())))

            # 2. cbx_edoperation : Actualise la combobox de choix de l'opération à modifier. La liste est filtrée selon la sortie sélectionnée.
            self.blocFillEdOpContr = '0'            
            self.ui.cbx_edoperation.clear()
            queryope = QtSql.QSqlQuery(self.db)
            if queryope.exec_(u"""SELECT operation_id, array_to_string(array(select distinct codeope from bdtravaux.join_opeprevues where id_joinprev=id_oper), '; ') as codeope,array_to_string(array(select distinct pdg from bdtravaux.join_opeprevues where id_joinprev=id_oper), '; ') as pdg, CASE WHEN geometrytype(the_geom) IN ('MULTIPOINT', 'POINT') THEN 'pts' WHEN geometrytype(the_geom) IN ('MULTILINESTRING', 'LINESTRING') THEN 'lgn' WHEN geometrytype(the_geom) IN ('MULTIPOLYGON', 'POLYGON') THEN 'surf' END as typ_graph, LEFT(array_to_string(array(select distinct typoperation from bdtravaux.join_typoperation where id_jointyp=id_oper), '; '),45)||'...'::text as typope, LEFT(descriptio,45)||'...'::text as descr, chantfini FROM (SELECT * FROM bdtravaux.operation_poly UNION SELECT * FROM bdtravaux.operation_lgn UNION SELECT * FROM bdtravaux.operation_pts) as gestreal WHERE sortie = {zr_sortie} OR operation_id='0' ORDER BY operation_id""".format(zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))):
                while queryope.next():
                     self.ui.cbx_edoperation.addItem(unicode(queryope.value(1)) + " / " + unicode(queryope.value(2)) + " / "+ unicode(queryope.value(3)) + " / "+ unicode(queryope.value(4)) + " / "+ unicode(queryope.value(5)), int(queryope.value(0)))
            self.blocFillEdOpContr = '1'

            # Rendre le premier item de cbx_edoperation ("choisissez une opération...") non sélectionnable
            self.ui.cbx_edoperation.model().item(0).setEnabled(False)

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

        # Activation de la liste lst_edopeprev si et seulement si l'index courant de la cbx_edoperation != 0. Permet de na pas modifier l'item 0 : "Choisissez une opération" par erreur:
            if self.ui.cbx_edoperation.currentIndex() != 0 :
                #print "une operation selectionnee"
                self.ui.lst_edopeprev.setEnabled(1)
            else :
                #print "aucune operation selectionnee"
                self.ui.lst_edopeprev.setEnabled(0)



        # Mise à jour du label "lbl_opeid", affichant l'id de l'opération sélectionnée
            self.ui.lbl_opeid.setText(str(self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex())))

        # Vidage des listes lst_edopeprev, lst_edtypope et lst_edpresta, poue sélectionner le nouveaux items
            self.ui.lst_edopeprev.clearSelection()
            self.ui.lst_edtypope.clearSelection()
            self.ui.lst_edpresta.clearSelection()
            
        # Requête pour le remplissage des contrôles du Tab "Modifications" du module "Opérations"
            queryfillope = QtSql.QSqlQuery(self.db)
            qfillope = u"""SELECT array_to_string(array(select distinct typoperation from bdtravaux.join_typoperation where id_jointyp=id_oper), '; ') as typope, array_to_string(array(select distinct operateurs from bdtravaux.join_operateurs where id_joinop=id_oper), '; ') as presta, descriptio, chantfini, array_to_string(array(select distinct codeope||' '||lblope||' '||pdg||' '||anneeprev from bdtravaux.join_opeprevues where id_joinprev=id_oper), ';') as opeprev, CASE WHEN geometrytype(the_geom) IN ('MULTIPOINT', 'POINT') THEN 'pts' WHEN geometrytype(the_geom) IN ('MULTILINESTRING', 'LINESTRING') THEN 'lgn' WHEN geometrytype(the_geom) IN ('MULTIPOLYGON', 'POLYGON') THEN 'surf' END as typ_graph FROM (SELECT * FROM bdtravaux.operation_poly UNION SELECT * FROM bdtravaux.operation_lgn UNION SELECT * FROM bdtravaux.operation_pts) as gestreal WHERE operation_id={zr_ope}""".format(zr_ope = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
            ok6 = queryfillope.exec_(qfillope)
            if not ok6 :
                QtGui.QMessageBox.warning(self, 'Alerte', u'Requête pour le remplissage des contrôles dans le module operations ratée')
            queryfillope.next()
            self.ui.txt_eddescr.setText(unicode(queryfillope.value(2)))
            self.ui.chx_edopeterm.setChecked(bool(queryfillope.value(3)))

        #Sélection d'items dans une liste (type d'opération réalisé)
            list_typope = queryfillope.value(0).split("; ")
            for y in xrange (self.ui.lst_edtypope.count()):
                typope=self.ui.lst_edtypope.item(y)
                for x in list_typope:
                    if unicode(typope.text())==x:
                        typope.setSelected(True) 
            self.ui.lst_edtypope.scrollTo(self.ui.lst_edtypope.currentIndex())

        #Sélection d'items dans une liste (prestataires)
            list_presta = queryfillope.value(1).split("; ")
            for y in xrange (self.ui.lst_edpresta.count()):
                presta=self.ui.lst_edpresta.item(y)
                for x in list_presta:
                    if unicode(presta.text())==x:
                        presta.setSelected(True) 
        
        #Sélection d'items dans une liste (opérations prévues)
            list_prevbd = queryfillope.value(4).split(";")
            for y in xrange (self.ui.lst_edopeprev.count()):
                prevu_lst=unicode(self.ui.lst_edopeprev.item(y).text().split("/ ")[1]+self.ui.lst_edopeprev.item(y).text().split("/ ")[3]+self.ui.lst_edopeprev.item(y).text().split("/ ")[5]+self.ui.lst_edopeprev.item(y).text().split(" /")[4])
                for x in list_prevbd:
                    if unicode(prevu_lst)==x:
                        self.ui.lst_edopeprev.item(y).setSelected(True)


        # désignation de la table dans laquelle on va modifier / supprimer des données
            self.typgeom = str(queryfillope.value(5))
            if self.typgeom == 'pts':
                self.tablemodif = 'operation_pts'
            elif self.typgeom == 'lgn':
                self.tablemodif = 'operation_lgn'
            elif self.typgeom == 'surf':
                self.tablemodif = 'operation_poly'
            else:
                self.tablemodif = 'operation_poly'
                #print "pas trouve la geometrie"
            #print str(self.tablemodif)

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
            # Fonction à lancer quand les boutons "OK" ou "Dernier - Editer CR" sont cliqués.

        self.erreurSaisieBase = '0'

        
            # Lance sauverOpe ou sauvOpeSanGeom si géométrie présente ou non        
        if self.sansgeom=='True':
            self.sauvOpeSansGeom()
        else:
            self.sauverOpe()



    def sauvOpeSansGeom(self):
        # Entre en base les infos saisies dans le formulaire par l'utilisateur
        self.recupIdChantvol()
        self.recupAnneeSortie()
        self.rempliJoin()
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u'insert into bdtravaux.operation_poly (sortie, descriptio, chantfini, ope_chvol, anneereal) values ({zr_sortie}, \'{zr_libelle}\', \'{zr_chantfini}\',{zr_opechvol}, \'{zr_anneereal}\')'.format (\
        zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_libelle= self.ui.descriptio.toPlainText().replace("\'","\'\'"),\
        zr_chantfini= str(self.ui.chantfini.isChecked()).lower(),\
        zr_opechvol = self.id_opechvol,\
        zr_anneereal = self.annsortie)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête sansgeom ratée')
            self.erreurSaisieBase = '1'
        self.nom_table='operation_poly'
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)
        if self.erreurSaisieBase == '0':
            QtGui.QMessageBox.information(self, 'Information', u'Données correctement saisies dans la base')
        else : 
            QtGui.QMessageBox.warning(self, 'Alerte', u'Il y a eu une erreur lors de la saisie. Données non saisies en base.')
        self.close()



    def sauverOpe(self):
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
        memlayer.commitChanges()
        memlayer.selectAll()

        #lancement de convert_geoms.py pour transformer les entités sélectionnées dans le type d'entités choisi.

                                #compréhension de liste : [fonction for x in liste]
        geom2=convert_geometries([QgsGeometry(feature.geometry()) for feature in memlayer.selectedFeatures()],geom_output)
        #export de la géométrie en WKT et transformation de la projection si les données ne sont pas saisies en Lambert 93
        if memlayer.crs().authid() == u'EPSG:2154':
            thegeom='st_setsrid(st_geometryfromtext (\'{zr_geom2}\'), 2154)'.format(zr_geom2=geom2.exportToWkt())
        elif memlayer.crs().authid() == u'EPSG:4326':
            thegeom='st_transform(st_setsrid(st_geometryfromtext (\'{zr_geom2}\'),4326), 2154)'.format(zr_geom2=geom2.exportToWkt())
        else :
            print u'La projection de la couche active n\'est pas supportee'


        #Récupération de la liste des types d'opérations sélectionnés, afin de vérifier s'il y a pose/retrait... de matériel à assurer.
        #Dans ce cas, entrée dans le module "MatosAssur"
        listopreal=[]
        for item in range(len(self.ui.opreal.selectedItems())):
            listopreal.append("\'"+self.ui.opreal.selectedItems()[item].text().replace("\'","\'\'")+"\'")
        txtopreal = ','.join(listopreal)
        
        querymatassur = QtSql.QSqlQuery(self.db)
        if querymatassur.exec_( u"""SELECT id_opes, operations, matosassur FROM bdtravaux.list_operations_cen WHERE operations IN ({zr_opes})""".format(zr_opes = txtopreal)) :
            while querymatassur.next():
                self.matassur = querymatassur.value(2)
                print self.matassur
                if self.matassur == True :
                    print 'on entre dans matassur'
                    #Création et remplissage de l'objet id_sortie avec l'identifiant de la sortie courante, à partir de la combobox "sortie"
                    id_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex())
                    print "id_sortie="+str(id_sortie)
                    #lancement deu module matosAssurDialog avec le paramètre id_sortie
                    self.obj_assur=matosAssurDialog(id_sortie,thegeom)
                    self.obj_assur.show()
                    result = self.obj_assur.exec_()
                    if result == 1:
                        pass
                else:
                    print 'opé non assurée'
       

        #lancement de la fonction qui vérifie si l'opération fait partie d'un chantier de volontaires.
        self.recupIdChantvol()
        self.recupAnneeSortie()
        
        #Lancement de la fonction qui introduit les données du formulaire dans les tables annexes.
        #Elles sont remplies avant la table "opération", pour avoir déjà les données quand le trigger "After Insert" de cette dernière viendra les chercher.
        self.rempliJoin() 
        
        #lancement de la requête SQL qui introduit les données géographiques et du formulaire dans les tables "operations_xxx".
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.{zr_nomtable} (sortie, descriptio, chantfini, the_geom, ope_chvol, anneereal) values ({zr_sortie}, '{zr_libelle}', '{zr_chantfini}', {zr_the_geom}, '{zr_opechvol}', '{zr_anneereal}')""".format (zr_nomtable=self.nom_table,\
        zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_libelle = self.ui.descriptio.toPlainText().replace("\'","\'\'"),\
        zr_chantfini = str(self.ui.chantfini.isChecked()).lower(),\
        zr_the_geom = thegeom,\
        zr_opechvol = self.id_opechvol,\
        zr_anneereal = self.annsortie)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête sauver Ope ratée')
            self.erreurSaisieBase = '1'
        self.iface.setActiveLayer(coucheactive)
        QgsMapLayerRegistry.instance().removeMapLayer(memlayer.id())
        self.ui.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)
        self.ui.compoButton.setEnabled(0)
        if self.erreurSaisieBase == '0':
            QtGui.QMessageBox.information(self, 'Information', u'Données correctement saisies dans la base')
        else : 
            QtGui.QMessageBox.warning(self, 'Alerte', u'Il y a eu une erreur lors de la saisie. Données non saisies en base.')
        self.close()



    def rempliJoin(self):
        #print 'remplijoin'
    #remplissage des tables join_operateur, join_operations et join_opeprevues avec les prestas, les types d'opés et les GH sélect par l'utilisateur
        #récupération de id_oper dans la table nom_table pour le remettre dans join_operateurs, join_operations et join_opeprevues
        queryidoper = QtSql.QSqlQuery(self.db)
        qidoper = u"""select id_oper as id_oper from (select * from bdtravaux.operation_poly union select * from bdtravaux.operation_lgn union select * from bdtravaux.operation_pts) tab order by id_oper desc limit 1"""
        ok2=queryidoper.exec_(qidoper)
        if not ok2:
            QtGui.QMessagebox.warning(self, 'Alerte', u'Pas trouvé id de l opération')
            self.erreurSaisieBase = '1'
        queryidoper.next()
        self.id_oper = queryidoper.value(0)+1
        # "+1" car les tables annexes sont remplies avant "operation_xxx" -> l'id_oper correspondant n'existe pas encore dans "operation_xxx"

        #remplissage de la table join_operateurs : id_oper, noms et types du (des) prestataire(s)
        for item in xrange (len(self.ui.prestataire.selectedItems())):
            # récupération du type d'opérateur en fonction du nom de l'opérateur
            query_typpresta = QtSql.QSqlQuery(self.db)
            qtyppresta = u"""select distinct typ_oper from bdtravaux.list_operateur where nom_oper = '{zr_operateurs}'""".format(zr_operateurs = self.ui.prestataire.selectedItems()[item].text().replace("\'","\'\'"))
            oktyp=query_typpresta.exec_(qtyppresta)
            if not oktyp:
                QtGui.QMessagebox.warning(self, 'Alerte', u'Pas trouvé le type d opérateur')
                self.erreurSaisieBase = '1'
            query_typpresta.next()
            self.typoptr = query_typpresta.value(0)
            #requête de remplissage de la table join_operateur
            querypresta = QtSql.QSqlQuery(self.db)
            qpresta = u"""insert into bdtravaux.join_operateurs (id_joinop, operateurs, typ_optr) values ({zr_idjoinop}, '{zr_operateur}', '{zr_typoptr}')""".format (zr_idjoinop = self.id_oper, zr_operateur = self.ui.prestataire.selectedItems()[item].text().replace("\'","\'\'"), zr_typoptr = unicode(self.typoptr))
            ok3 = querypresta.exec_(qpresta)
            if not ok3:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des prestas en base ratée')
                self.erreurSaisieBase = '1'

        #remplissage de la table join_operation : id_oper et noms du (des) type(s) d'opération
        for item in xrange (len(self.ui.opreal.selectedItems())):
            querytypope = QtSql.QSqlQuery(self.db)
            qtypope = u"""insert into bdtravaux.join_typoperation (id_jointyp, typoperation) values ({zr_idjointyp}, '{zr_typoperation}')""".format (zr_idjointyp = self.id_oper, zr_typoperation = self.ui.opreal.selectedItems()[item].text().replace("\'","\'\'"))
            ok4 = querytypope.exec_(qtypope)
            if not ok4:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie des types d opérations en base ratée')
                self.erreurSaisieBase = '1'

        #remplissage de la table join_opeprevues : id_oper, code GH, ype d'opé, libelle de l'opé, année prévue et pdg où l'opé est prévue
        for item in xrange (len(self.ui.opprev.selectedItems())):
            queryopeprev = QtSql.QSqlQuery(self.db)
            qopeprev = u"""insert into bdtravaux.join_opeprevues (id_joinprev, codeope, typeope, lblope, anneeprev, pdg) values ({zr_idjoinprev}, '{zr_codeope}', '{zr_typeope}', '{zr_lblope}', '{zr_anneeprev}', '{zr_pdg}')""".format (\
            zr_idjoinprev = self.id_oper,\
            zr_codeope = self.ui.opprev.selectedItems()[item].text().split(" / ")[1].replace("\'","\'\'"),\
            zr_typeope = self.ui.opprev.selectedItems()[item].text().split(" / ")[2].replace("\'","\'\'"),\
            zr_lblope = self.ui.opprev.selectedItems()[item].text().split(" / ")[3].replace("\'","\'\'"),\
            zr_anneeprev = self.ui.opprev.selectedItems()[item].text().split(" / ")[4].replace("\'","\'\'"),\
            zr_pdg = self.ui.opprev.selectedItems()[item].text().split(" / ")[5].replace("\'","\'\'"))
            ok5 = queryopeprev.exec_(qopeprev)
            if not ok5:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Saisie en base des opérations prévues ratée')
                self.erreurSaisieBase = '1'


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


    def recupAnneeSortie(self):
        #récupération de l'année de la sortie à laquelle appartient l'opération
        queryannsort = QtSql.QSqlQuery(self.db)
        queryannso = u"""select left(date_sortie::text,4) from bdtravaux.sortie where sortie_id={zr_sortie}""".format(zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        ok = queryannsort.exec_(queryannso)
        if not ok :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Pas trouvé année opération')
        queryannsort.next()
        self.annsortie = queryannsort.value(0)
#        print 'annsortie='+str(self.annsortie)


######################
# Sauvegarde en base des données modifiées par l'utilisateur (Tab "modification")

    def sauverOpeModifs(self):
    # sauvegarde des modifications d'une opération

        self.erreurModifBase = '0'

        # la table operation_XXX est modifiée en dernier, pour que les tables annexes présentent déjà les données modifiées quand le trigger viendra les chercher  
        # pour les intégrer aux tables "synthese_XXX".

        # mise à jour de la table join_typoperation
            #suppression des types d'opération appartenant à l'opération modifiée
        querysupprtyp = QtSql.QSqlQuery(self.db)
        qsupprtyp = u"""DELETE FROM bdtravaux.join_typoperation WHERE id_jointyp = {zr_idoper}""".format(\
        zr_idoper = self.id_oper_modif)
        ok3 = querysupprtyp.exec_(qsupprtyp)
        if not ok3 :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression des types d opération en base ratée')
            self.erreurModifBase = '1'
        #print "types opes en trop supprimes"
        #print qsupprtyp

            #ajout de la liste de types d'opération modifiée
        for item in xrange (len(self.ui.lst_edtypope.selectedItems())):
            querymodiftyp = QtSql.QSqlQuery(self.db)
            qmodtyp = u"""insert into bdtravaux.join_typoperation (id_jointyp, typoperation) values ({zr_idjointyp}, '{zr_typope}')""".format (\
            zr_idjointyp = self.id_oper_modif,\
            zr_typope = self.ui.lst_edtypope.selectedItems()[item].text().replace("\'","\'\'"))
            ok4 = querymodiftyp.exec_(qmodtyp)
            if not ok4:
               QtGui.QMessageBox.warning(self, 'Alerte', u'Ajout des nvx types d opés en base ratée')
               self.erreurModifBase = '1'
            querymodiftyp.next()
            #print "types opes ajoutes"       
            #print qmodtyp

        # mise à jour de la table join_operateur
            #suppression des opérateurs appartenant à l'opération modifiée
        querysupprprest = QtSql.QSqlQuery(self.db)
        qsupprprest = u"""DELETE FROM bdtravaux.join_operateurs WHERE id_joinop = {zr_idoper}""".format(\
        zr_idoper = self.id_oper_modif)
        ok5 = querysupprprest.exec_(qsupprprest)
        if not ok5 :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression des opérateurs en base ratée')
            self.erreurModifBase = '1'
        #print "operateurs en trop supprimes"
        #print qsupprprest

            #ajout de la liste des opérateurs modifiée
        for item in xrange (len(self.ui.lst_edpresta.selectedItems())):
            #print item
                # récupération du type d'opérateur en fonction du nom de l'opérateur
            query_typprestamod = QtSql.QSqlQuery(self.db)
            qtypprestamod = u"""select distinct typ_oper from bdtravaux.list_operateur where nom_oper = '{zr_operateurs}'""".format (zr_operateurs = self.ui.lst_edpresta.selectedItems()[item].text().replace("\'","\'\'"))
            # print qtypprestamod
            oktypm=query_typprestamod.exec_(qtypprestamod)
            if not oktypm:
                QtGui.QMessagebox.warning(self, 'Alerte', u'Pas trouvé les types d opérateurs à rajouter')
                self.erreurModifBase = '1'
            query_typprestamod.next()
            self.typoptrmod = query_typprestamod.value(0)
                #requête d'ajout des données (id_joinop, operateurs et typ_optr)
            querymodifprest = QtSql.QSqlQuery(self.db)
            qmodprest = u"""insert into bdtravaux.join_operateurs (id_joinop, operateurs, typ_optr) values ({zr_idjoinop}, '{zr_presta}', '{zr_typoptr}')""".format (\
            zr_idjoinop = self.id_oper_modif,\
            zr_presta = self.ui.lst_edpresta.selectedItems()[item].text().replace("\'","\'\'"),\
            zr_typoptr = self.typoptrmod.replace("\'","\'\'"))
            ok6 = querymodifprest.exec_(qmodprest)
            if not ok6:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Ajout des nvx opérateurs en base ratée')
                self.erreurModifBase = '1'
            querymodifprest.next()
            #print 'operateurs ajoutes'       
            #print qmodprest

        # mise à jour de la table join_opeprevues
            #suppression des opérations prévues correspondant à l'opération modifiée
        querysuppropeprev = QtSql.QSqlQuery(self.db)
        qsuppropeprev = u"""DELETE FROM bdtravaux.join_opeprevues WHERE id_joinprev = {zr_idoper}""".format(\
        zr_idoper = self.id_oper_modif)
        ok7 = querysuppropeprev.exec_(qsuppropeprev)
        if not ok7 :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression des opérations prévues en base ratée')
            self.erreurModifBase = '1'
        #print 'operations prevues en trop supprimees'
        #print qsuppropeprev

            #ajout de la liste des opérations prévues modifiée
        for item in xrange (len(self.ui.lst_edopeprev.selectedItems())):
            print str(xrange (len(self.ui.lst_edopeprev.selectedItems())))
            querymodifopeprev = QtSql.QSqlQuery(self.db)
            qmodopeprev =u"""insert into bdtravaux.join_opeprevues (id_joinprev, codeope, typeope, lblope, anneeprev, pdg) values ({zr_idjoinprev}, '{zr_codeope}', '{zr_typeope}', '{zr_lblope}', '{zr_anneeprev}', '{zr_pdg}')""".format (\
            zr_idjoinprev = self.id_oper_modif,\
            zr_codeope = self.ui.lst_edopeprev.selectedItems()[item].text().split(" / ")[1].replace("\'","\'\'"),\
            zr_typeope = self.ui.lst_edopeprev.selectedItems()[item].text().split(" / ")[2].replace("\'","\'\'"),\
            zr_lblope = self.ui.lst_edopeprev.selectedItems()[item].text().split(" / ")[3].replace("\'","\'\'"),\
            zr_anneeprev = self.ui.lst_edopeprev.selectedItems()[item].text().split(" / ")[4].replace("\'","\'\'"),\
            zr_pdg = self.ui.lst_edopeprev.selectedItems()[item].text().split(" / ")[5].replace("\'","\'\'"))
            ok7 = querymodifopeprev.exec_(qmodopeprev)
            if not ok7:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Ajout des nvlles données de gestion prévue en base ratée')
                self.erreurModifBase = '1'
#            querymodifopeprev.next()
            #print 'operations prevues ajoutees'
            #print qmodopeprev


        # mise à jour de la table "operation_xxx". Elle est mise à jour en dernier pour que les tables annexes présentent déjà les valeurs modifiées lorsque le trigger modsynthese viendra les 
        # chercher pour les intégrer aux tables "synthese_XXX"
        querysavemodope = QtSql.QSqlQuery(self.db)
        qsavmodo = u"""UPDATE bdtravaux.{zr_table} SET descriptio = '{zr_descr}' , chantfini='{zr_chantfini}' WHERE operation_id={zr_opeid}""".format (\
        zr_table = self.tablemodif,\
        zr_descr = self.ui.txt_eddescr.toPlainText().replace("\'","\'\'"),\
        zr_chantfini = str(self.ui.chx_edopeterm.isChecked()).lower(),\
        zr_opeid = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
        ok = querysavemodope.exec_(qsavmodo)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Mise à jour opération ratée')
            self.erreurModifBase = '1'
        #print qsavmodo


        # Désactivation des bouton "OK", "modif Geom" et "Supprimer" jusqu'à la prochaine sélection d'une opération
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)

        #Désactivation de la lst_edopeprev jusqu'à la prochaine sélection d'une opération
        self.ui.lst_edopeprev.setEnabled(0)

        self.db.close()
        self.db.removeDatabase("sitescsn")
        if self.erreurModifBase == '0':
            QtGui.QMessageBox.information(self, 'Information', u'Modification des données réussie')
        else :QtGui.QMessageBox.warning(self, 'Alerte', u'Modification des données non effectuée')
            
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
        #Désactivation de la lst_edopeprev jusqu'à la prochaine sélection d'une opération
        self.ui.lst_edopeprev.setEnabled(0)

        self.timeoutTimer = QtCore.QTimer() # attendre une seconde (pour que QGIS ait le temps d'enregistrer la couche), puis la supprimer.
        self.timeoutTimer.singleShot(1000, self.removeModifiedLayer)

    def removeModifiedLayer(self):
        QgsMapLayerRegistry.instance().removeMapLayer(self.opeModif.id()) # retrait de la couche





######################"
# Suppression d'opérations

    def supprOpe(self):

        self.opeSupprOk = '0'
        # suppression des données dans la table "join_operateurs"        
        querysupprprest = QtSql.QSqlQuery(self.db)
        qsupprprest = u"""DELETE FROM bdtravaux.join_operateurs WHERE id_joinop = {zr_idjoinop}""".format(\
        zr_idjoinop = self.id_oper_modif)
        ok1 = querysupprprest.exec_(qsupprprest)
        if not ok1:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression prestataires ratée')
            self.opeSupprOk = '1'

        # suppression des données dans la table "join_typoperation"        
        querysupprtyp = QtSql.QSqlQuery(self.db)
        qsupprtyp = u"""DELETE FROM bdtravaux.join_typoperation WHERE id_jointyp = {zr_idjointyp}""".format(\
        zr_idjointyp = self.id_oper_modif)
        ok2 = querysupprtyp.exec_(qsupprtyp)
        if not ok2:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression types opération ratée')
            self.opeSupprOk = '1'

        # suppression des données dans la table "join_opeprevues"
        querysupprprev = QtSql.QSqlQuery(self.db)
        qsupprprev = u"""DELETE FROM bdtravaux.join_opeprevues WHERE id_joinprev = {zr_idjoinprev}""".format(\
        zr_idjoinprev = self.id_oper_modif)
        ok3 = querysupprprev.exec_(qsupprprev)
        if not ok3:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression types opération ratée')
            self.opeSupprOk = '1'

        # suppression des données dans la table "operation_xxx"        
        querysupprope = QtSql.QSqlQuery(self.db)
        qsupprope = u"""DELETE FROM bdtravaux.{zr_table} WHERE operation_id={zr_opeid}""".format(\
        zr_table = self.tablemodif,
        zr_opeid = self.ui.cbx_edoperation.itemData(self.ui.cbx_edoperation.currentIndex()))
        ok4 = querysupprope.exec_(qsupprope)
        if not ok4:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Suppression opération ratée')
            self.opeSupprOk = '1'

        # Désactivation des bouton "OK", "modif Geom" et "Supprimer" jusqu'à la prochaine sélection d'une opération
        self.ui.pbt_supprope.setEnabled(0)
        self.ui.pbt_edgeom.setEnabled(0)
        self.ui.bbx_edokannul.button(QtGui.QDialogButtonBox.Ok).setEnabled(0)

        #Désactivation de la lst_edopeprev jusqu'à la prochaine sélection d'une opération
        self.ui.lst_edopeprev.setEnabled(0)

        if self.opeSupprOk == '0':
            QtGui.QMessageBox.information(self, 'Information', u'Suppression opération réussie')
        else :
            QtGui.QMessageBox.warning(self, 'Alerte', u'Opération non ou partiellement supprimée')
        self.db.close()
        self.db.removeDatabase("sitescsn")
        self.close()


######################
# Lancement du composeur au clic sur le bouton "Dernier - Editer CR"


    def creatComposer(self):
        #Intégration en base de la dernière opération saisie
        self.sauverOpeChoi()
        #Création et remplissage de l'objet id_sortie avec l'identifiant de la sortie courante, à partir de la combobox "sortie"
        id_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        # id_site n'est utilisé que pour l'impression des bordereaux de terrain. On le créée juste ici avec une valeur fausse car le module "composeur" le réclame en paramètre.
        id_site = '000'
        #print "id_sortie="+str(id_sortie)
        #lancement de la fonction Composer dans le module composeurClass avec le paramètre id_sortie
        self.obj_compo=composerClass()
        self.obj_compo.Composer(id_sortie, id_site)
        # Afficher le formulaire "bdtravauxdialog.py" devant iface, et l'activer.
        self.obj_compo.composerView.composerViewHide.connect(self.raiseModule)
        #connexion de l'évènement "fermeture du composeur" au lancement de la fonction afterComposeurClose dans le module composerClass, afin d'effacer les couches ayant servi au composeur, et réafficher les autres.
        self.obj_compo.composerView.composerViewHide.connect(self.obj_compo.afterComposerClose)



    def raiseModule(self):
        self.raise_()
        self.activateWindow()

