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

from PyQt4 import QtCore, QtGui, QtSql, QtXml
from qgis.core import *
from qgis.gui import *
from ui_operation import Ui_operation
from convert_geoms import convert_geometries
import sys
import inspect
import re


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
        self.db.setHostName("192.168.0.103") 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Connexion échouée')

        #Definition de URI pour extraire des couches des tables PG. Uri est utilisé dans les fonctions "afficher" et "composeur".
        #QgsDataSourceUri() permet d'aller chercher une table d'une base de données PostGis (cf. PyQGIS cookbook)
        self.uri = QgsDataSourceURI()
        # configure l'adresse du serveur (hôte), le port, le nom de la base de données, l'utilisateur et le mot de passe.
        self.uri.setConnection("192.168.0.103", "5432", "sitescsn", "postgres", "postgres")

        #Initialisations
        self.ui.chx_opechvol.setVisible(False)

        # Connexions aux boutons
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'), self.sauverOpeChoi)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.compoButton, QtCore.SIGNAL('clicked()'), self.composeur)
        self.connect(self.ui.sortie, QtCore.SIGNAL('currentIndexChanged(int)'), self.actu_gestprev_chxopechvol)



    def actu_cbbx(self):
        self.ui.sortie.clear()
        # Remplir la combobox "sortie" avec les champs date_sortie+site+redacteur de la table "sortie" issus de la table "sites"
        query = QtSql.QSqlQuery(self.db)
        # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        if query.exec_('select sortie_id, date_sortie, codesite, redacteur from bdtravaux.sortie order by date_sortie DESC LIMIT 30'):
            while query.next():
                self.ui.sortie.addItem(query.value(1).toPyDate().strftime("%Y-%m-%d") + " / " + str(query.value(2)) + " / "+ str(query.value(3)), int(query.value(0)))
        # 1er paramètre = ce qu'on affiche, 
        # 2ème paramètre = ce qu'on garde en mémoire pour plus tard
        # query.value(0) = le 1er élément renvoyé par le "select" d'une requête SQL. Et ainsi de suite...
        # pour la date : plus de "toString()" dans l'API de QGIS 2.0 => QDate retransformé en PyQt pour utiliser "strftime"
        # afin de le transformer en chaîne de caractères.



    def actu_lblgeom(self):
        # Indiquer le nombre d'entités sélectionnées dans le contrôle lbl_geo et le type de géométrie.
        # En premier lieu, on compare la constante renvoyée par geometrytype() à celle renvoyée par les constantes de QGis pour 
        # obtenir une chaîne de caractère : geometryType() ne renvoie que des constantes (0, 1 ou 2). Il faut donc ruser...
        if not self.iface.activeLayer():
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
        # Actualise la liste des opérations de gestion prévues en base de données et filtre selon le code du site
        self.ui.opprev.clear()
        self.recupDonnSortie()
        query = QtSql.QSqlQuery(self.db)
        if query.exec_(u"""select prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_pdg from (select * from bdtravaux.list_gestprev_surf UNION select * from bdtravaux.list_gestprev_lgn UNION select * from bdtravaux.list_gestprev_pts) as gestprev where prev_codesite='{zr_codesite}' or prev_codesite='000' group by prev_codesite, prev_codeope, prev_typeope, prev_lblope, prev_pdg order by prev_codesite , prev_pdg , prev_codeope""".format (zr_codesite = self.codedusite)):
            print query
            while query.next():
                self.ui.opprev.addItem(unicode(query.value(0)) + " / " + unicode(query.value(1)) + " / "+ unicode(query.value(2)) + " / "+ unicode(query.value(3)) + " / "+ unicode(query.value(4)))
        if self.chantvol == True:
            self.ui.chx_opechvol.setVisible(True)
            self.ui.chx_opechvol.setChecked(True)
        else :
            self.ui.chx_opechvol.setVisible(False)



    def sauverOpeChoi(self):
        if self.sansgeom=='True':
            print 'sansgeomtrue'
            self.sauvOpeSansGeom()
        else:
            print 'avecgeomtrue'
            self.sauverOpe()



    def sauvOpeSansGeom(self):
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.operation_poly (sortie, plangestion, code_gh, typ_operat, operateur, descriptio, chantfini) values ({zr_sortie}, '{zr_plangestion}', '{zr_code_gh}', '{zr_ope_typ}', '{zr_opera}', '{zr_libelle}', '{zr_chantfini}')""".format (\
        zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_plangestion = self.self.ui.opprev.currentItem().text().split("/")[-1],\
        zr_code_gh = self.self.ui.opprev.currentItem().text().split("/")[1],\
        zr_ope_typ= self.ui.opreal.currentItem().text(),\
        zr_opera= self.ui.prestataire.currentItem().text(),\
        zr_libelle= self.ui.descriptio.toPlainText(),\
        zr_chantfini= str(self.ui.chantfini.isChecked()).lower())
        print query
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
        self.close



    def sauverOpe(self):
        # Fonction à lancer quans les boutons "OK" ou "Dernier - Editer CR" sont cliqué
        # Entre en base les infos sélectionnées dans QGIS, et saisies dans le formulaire par l'utilisateur
        # Gère les erreurs "pas assez de points sélectionnés pour construire une ligne ou un polygone"
        # Gère également la transformation géométrique, via le module convert_geoms
        # Récupération de la géométrie finale. On en déduit la table où sera stockée l'information, et on gère les erreurs 
        # "pas assez de points pour faire la transformation"
        geom_cbbx=self.ui.trsf_geom.itemText(self.ui.trsf_geom.currentIndex())
        if geom_cbbx == 'Points' :
            geom_output=QGis.Point
            nom_table='operation_pts'
        elif geom_cbbx == 'Lignes':
            geom_output=QGis.Line
            nom_table='operation_lgn'
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
            nom_table='operation_poly'
            if self.iface.activeLayer().geometryType()==0:
                if self.iface.activeLayer().selectedFeatureCount()<3:
                    mess3pts=QtGui.QMessageBox()
                    mess3pts.setText(u'Pas assez de points sélectionnés')
                    mess3pts.setInformativeText(u'Il faut au moins 3 points pour faire un polygone. Merci d\'en sélectionner plus')
                    mess3pts.setIcon(QtGui.QMessageBox.Warning)
                    mess3pts.setStandardButtons(QtGui.QMessageBox.Ok)
                    ret = mess3pts.exec_()
                    return
        #lancement de convert_geoms.py pour transformer les entités sélectionnées dans le type d'entités choisi.
        liste=[feature.geometry() for feature in self.iface.activeLayer().selectedFeatures()]
        coucheactive=self.iface.activeLayer()
        #compréhension de liste : [fonction for x in liste]
        geom2=convert_geometries([QgsGeometry(feature.geometry()) for feature in self.iface.activeLayer().selectedFeatures()],geom_output)
        #récupération de l'id du chantier du volontaire si l'opération en fait partie
        if self.ui.chx_opechvol.isChecked():
            queryopechvol = QtSql.QSqlQuery(self.db)
            queryvol = u"""select id_chvol from bdtravaux.ch_volont where sortie={zr_sortie}""".format(zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
            ok = queryopechvol.exec_(queryvol)
            if not ok :
                QtGui.QMessageBox.warning(self, 'Alerte', u'Pas trouvé Id du chantier de volontaire')
            queryopechvol.next()
            id_opechvol = queryopechvol.value(0)
            print id_opechvol
        #lancement de la requête SQL qui introduit les données géographiques et du formulaire dans la base de données.
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.{zr_nomtable} (sortie, plangestion, code_gh, typ_operat, operateur, descriptio, chantfini, the_geom, ope_chvol) values ({zr_sortie}, '{zr_plangestion}', '{zr_code_gh}', '{zr_ope_typ}', '{zr_opera}', '{zr_libelle}', '{zr_chantfini}', st_setsrid(st_geometryfromtext ('{zr_the_geom}'),2154), {zr_opechvol})""".format (zr_nomtable=nom_table,\
        zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_plangestion = self.ui.opprev.currentItem().text().split("/")[-1],\
        zr_code_gh = self.ui.opprev.currentItem().text().split("/")[1],\
        zr_ope_typ = self.ui.opreal.currentItem().text(),\
        zr_opera = self.ui.prestataire.currentItem().text(),\
        zr_libelle = self.ui.descriptio.toPlainText(),\
        zr_chantfini = str(self.ui.chantfini.isChecked()).lower(),\
        zr_the_geom = geom2.exportToWkt(),\
        #st_transform(st_setsrid(st_geometryfromtext ('{zr_the_geom}'),4326), 2154) si besoin de transformer la projection
        zr_opechvol = id_opechvol)
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
            print query
        self.iface.setActiveLayer(coucheactive)
        self.close



    def recupDonnSortie(self):
        #recup de données en fction de l'Id de la sortie. Pr afficher le site dans affiche(), les txts des étiqu dans composeur() et mettre à jour "opprev" et "chx_opechvol" au lancement du module, et qd une nouvelle sortie est sélectionnée.
        querycodesite = QtSql.QSqlQuery(self.db)
        qcodesite = u"""select codesite, redacteur, date_sortie, chantvol, sortcom, objvisite, objvi_autr, natfaune, natflore, natautre from bdtravaux.sortie where sortie_id = {zr_sortie_id}""".format \
        (zr_sortie_id = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        ok2 = querycodesite.exec_(qcodesite)
        if not ok2:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête recupDonnSortie ratée')
        querycodesite.next()
        self.codedusite=querycodesite.value(0)
        self.redacteur=querycodesite.value(1)
        self.datesortie=querycodesite.value(2).toPyDate().strftime("%Y-%m-%d")
        self.chantvol=querycodesite.value(3)
        self.sortcom=querycodesite.value(4)
        self.objvisite=querycodesite.value(5)
        self.objautre=querycodesite.value(6)
        self.natfaune=querycodesite.value(7)
        self.natflore=querycodesite.value(8)
        self.natautre=querycodesite.value(9)



    def recupDonnChVolont(self):
        # recup des données d'un chantier de volontaires en fction de l'Id de la sortie (et de l'opé). Pour afficher les textes ds composeur().
        querycodevolont = QtSql.QSqlQuery(self.db)
        qchvolont = u"""select nb_jours, nb_heur_ch, nb_heur_de, partenaire, heberg, j1_enc_am, j1_enc_pm, j1_tot_am, j1_tot_pm, j1adcen_am, j1adcen_pm, j1_blon_am, j1_blon_pm, j2_enc_am, j2_enc_pm, j2_tot_am, j2_tot_pm, j2adcen_am, j2adcen_pm, j2_blon_am, j2_blon_pm, sem_enc, sem_ben from bdtravaux.ch_volont where sortie={zr_sortie}""".format(zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        print qchvolont
        ok = querycodevolont.exec_(qchvolont)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête Chvolotaires ratée')
        querycodevolont.next()
        self.cv_nb_jours = querycodevolont.value(0)
        self.cv_nb_heur_ch = querycodevolont.value(1)
        self.cv_nb_heur_de = querycodevolont.value(2)
        self.cv_partenaire = querycodevolont.value(3)
        self.cv_heberg = querycodevolont.value(4)
        self.cv_j1_enc_am = querycodevolont.value(5)
        self.cv_j1_enc_pm = querycodevolont.value(6)
        self.cv_j1_tot_am = querycodevolont.value(7)
        self.cv_j1_tot_pm = querycodevolont.value(8)
        self.cv_j1adcen_am = querycodevolont.value(9)
        self.cv_j1adcen_pm = querycodevolont.value(10)
        self.cv_j1_blon_am = querycodevolont.value(11)
        self.cv_j1_blon_pm = querycodevolont.value(12)
        self.cv_j2_enc_am = querycodevolont.value(13)
        self.cv_j2_enc_pm = querycodevolont.value(14)
        self.cv_j2_tot_am = querycodevolont.value(15)
        self.cv_j2_tot_pm = querycodevolont.value(16)
        self.cv_j2adcen_am = querycodevolont.value(17)
        self.cv_j2adcen_pm = querycodevolont.value(18)
        self.cv_j2_blon_am = querycodevolont.value(19)
        self.cv_j2_blon_pm = querycodevolont.value(20)
        self.cv_sem_enc = querycodevolont.value(21)
        self.cv_sem_ben = querycodevolont.value(22)
        if self.cv_partenaire is None:
            print 'pas de partenaire'



    def affiche(self):
        #fonction affichant dans QGIS les entités de la sortie en cours, présentes en base.
        #uri = QgsDataSourceURI()
        #uri.setConnection("127.0.0.1", "5432", "sitescsn", "postgres", "postgres")
        # les 4 lignes ci-dessus ont été intégrées au constructeur de la classe operationdialog pour être utilisées dans plusieurs fonctions (l.52)

        #requête qui sera intégrée dans uri.setDataSource() (cf. paragraphe ci-dessous)
        reqwhere="""sortie="""+str(self.ui.sortie.itemData(self.ui.sortie.currentIndex()))

        # configure le shéma, le nom de la table, la colonne géométrique, et un sous-jeu de données (clause WHERE facultative)
        self.uri.setDataSource("bdtravaux", "operation_poly", "the_geom", reqwhere)
        #instanciation de la couche dans qgis 
        self.gestrealpolys=QgsVectorLayer(self.uri.uri(), "gestrealpolys", "postgres")
        if self.gestrealpolys.featureCount()>0:
        #si la couche importée n'est pas vide, intégration dans le Map Layer Registry pour pouvoir l'utiliser
            QgsMapLayerRegistry.instance().addMapLayer(self.gestrealpolys)

        self.uri.setDataSource("bdtravaux", "operation_lgn", "the_geom", reqwhere)
        self.gestreallgn=QgsVectorLayer(self.uri.uri(), "gestreallgn", "postgres")
        if self.gestreallgn.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.gestreallgn)

        self.uri.setDataSource("bdtravaux", "operation_pts", "the_geom", reqwhere)
        self.gestrealpts=QgsVectorLayer(self.uri.uri(), "gestrealpts", "postgres")
        if self.gestrealpts.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.gestrealpts)



    def composeur(self):
        #Intégration en base de la dernière opération saisie
        self.sauverOpeChoi()
        #S'il y a des entités géographiques dans la sortie, les afficher
        if self.sansgeom!='True':
            self.affiche()

        #Récupération des données de la table "sortie" pour affichage du site et utilisation dans les étiquettes du composeur
        self.recupDonnSortie()
        reqwheresit="""codesite='"""+str(self.codedusite)+"""'"""
        self.uri.setDataSource("sites_cen", "t_sitescen", "the_geom", reqwheresit)
        self.contours_site=QgsVectorLayer(self.uri.uri(), "contours_site", "postgres")
        if self.contours_site.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.contours_site)

        #Récupération des données de la table "ch_volont" pour utilisation dans les étiquettes du composeur
        self.recupDonnChVolont()

        #COMPOSEUR : Production d'un composeur
        beforeList = self.iface.activeComposers()
        self.iface.actionPrintComposer().trigger()  
        afterList = self.iface.activeComposers()
        diffList = []
        for item in afterList:
            if not item in  beforeList:
                diffList.append(item)
        #Intégration du composeur dans le QgsComposerView et création du QgsComposition
        self.composerView = diffList[0]
        self.composition = self.composerView.composition()
        #operationOnTop() : afficher le form "operation.py" devant QGIS qd le composeur est fermé
        self.composerView.composerViewHide.connect(self.operationOnTop)
        #Récupération du template. Intégration des ses éléments dans la carte.
        file1=QtCore.QFile('/home/vincent/form_pyqgis2013/bdtravaux/BDT_20130705_T_CART_ComposerTemplate.qpt')
        doc=QtXml.QDomDocument()
        doc.setContent(file1, False)
        self.composition.loadFromTemplate(doc)
        
        self.composerView.zoomFull()


        #CARTE : Récupération de la carte
        maplist=[]
        for item in self.composition.composerMapItems():
            maplist.append(item)
        self.composerMap=maplist[0]
        #Taille définie pour la carte
        x, y, w, h = 5, 28, 408, 240
        self.composerMap.setItemPosition(x, y, w, h)
        #Crée la bbox autour du site pour la carte en cours (fonction mapItemSetBBox l 293)
        #self.contours_sites est défini dans la fonction affiche()
        self.margin=10
        self.composerMapSetBBox(self.contours_site, self.margin)
                    #(Dé)zoome sur l'ensemble des deux pages du composeur
                    #self.composition.mActionZoomFullExtent().trigger()


        #ETIQUETTES :       Modifier les étiquettes du composeur.
        # Trouver les étiquettes dans le composeur
        labels = [item for item in self.composition.items()\
                if item.type() == QgsComposerItem.ComposerLabel]

        #trouver nomsite dans la table postgresql, en fonction de codesite
        querynomsite = QtSql.QSqlQuery(self.db)
        qnomsite=(u"""select nomsite from sites_cen.t_sitescen where codesite='{zr_codesite}'""".format (zr_codesite=self.codedusite))
        ok = querynomsite.exec_(qnomsite)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
        querynomsite.next()
        nomdusite=unicode(querynomsite.value(0))

        #trouver les opérations effectuées lors de la sortie et leurs commentaires dans la table postgresql, selon l'id de la sortie sélectionnée dans le module "opération"
        # une boucle permet de récupérer et afficher à la suite dans une seule zone de texte toutes les opérations et leurs descriptions
        querycomope = QtSql.QSqlQuery(self.db)
        qcomope=u"""select typ_operat, descriptio from (select * from bdtravaux.operation_poly UNION select * from bdtravaux.operation_lgn UNION select * from bdtravaux.operation_pts) tables where sortie={zr_sortie} order by typ_operat""".format \
        (zr_sortie = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        ok3 = querycomope.exec_(qcomope)
        if not ok3:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête operations ratée')
        querycomope.first()
        texteope=""
        for i in xrange(0 , querycomope.size()):
            ope=unicode(querycomope.value(0))
            descrope=unicode(querycomope.value(1))
            texteope=unicode(texteope+'<br/>'+'<b>'+ope+'</b>'+'<br/>'+descrope+'<br/>')
            querycomope.next()

        # Pour chaque étiquette qui contient le mot-clé (comme "$codesite"), remplacer le texte par le code du site concerné
        # La methode find() permet de chercher une chaîne dans une autre. 
        # Elle renvoie le rang du début de la chaîne cherchée. Si = -1, c'est que la chaîne cherchée n'est pas trouvée
        for label in labels:
            if label.displayText().find("$codesite")>-1:
                plac_codesite=label.displayText().find("$codesite")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_codesite]+self.codedusite+texte[plac_codesite+9:])
                #pr python equiv à VB6 left, mid and right : https://mail.python.org/pipermail/tutor/2004-November/033445.html
            if label.displayText().find("$redac")>-1:
                plac_redac=label.displayText().find("$redac")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_redac]+self.redacteur+texte[plac_redac+6:])
            if label.displayText().find("$date")>-1:
                plac_date=label.displayText().find("$date")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_date]+self.datesortie+texte[plac_date+5:])
            if label.displayText().find("$commsortie")>-1:
                plac_commsortie=label.displayText().find("$commsortie")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_commsortie]+self.sortcom+texte[plac_commsortie+11:])
            if label.displayText().find("$nomsite")>-1:
                plac_nomsite=label.displayText().find("$nomsite")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_nomsite]+nomdusite+texte[plac_nomsite+8:])
            if label.displayText().find("$commope")>-1:
                label.setText(texteope)
            if label.displayText().find("$objet")>-1:
                plac_objet=label.displayText().find("$objet")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_objet]+self.objvisite+texte[plac_objet+6:])
            if label.displayText().find("$objvi_autre")>-1:
                if self.objautre:
                    plac_objautre=label.displayText().find("$objvi_autre")
                    texte=unicode(label.displayText())
                    label.setText(texte[0:plac_objautre]+self.objautre+texte[plac_objautre+12:])
            if label.displayText().find("$natfaune")>-1:
                label.setText(str(self.natfaune))
            if label.displayText().find("$natflore")>-1:
                label.setText(str(self.natflore))
            if self.cv_partenaire is not None:
                if label.displayText().find("$nbjours")>-1:
                    plac_nbjours=label.displayText().find("$nbjours")
                    texte=unicode(label.displayText())
                    label.setText(texte[0:plac_nbjours]+str(self.cv_nb_jours)+texte[plac_nbjours+8:])
                if label.displayText().find("$nbheurch")>-1:
                    plac_nbheurch=label.displayText().find("$nbheurch")
                    texte=unicode(label.displayText())
                    label.setText(texte[0:plac_nbheurch]+str(self.cv_nb_heur_ch)+texte[plac_nbheurch+9:])
                if label.displayText().find("$nbheurdec")>-1:
                    plac_nbheurdec=label.displayText().find("$nbheurdec")
                    texte=unicode(label.displayText())
                    label.setText(texte[0:plac_nbheurdec]+str(self.cv_nb_heur_de)+texte[plac_nbheurdec+10:])
                if label.displayText().find("$partenair")>-1:
                    plac_partenair=label.displayText().find("$partenair")
                    texte=unicode(label.displayText())
                    label.setText(texte[0:plac_partenair]+self.cv_partenaire+texte[plac_partenair+10:])
                    print unicode(texte)
                if label.displayText().find("$heberg")>-1:
                    plac_heberg=label.displayText().find("$heberg")
                    texte=unicode(label.displayText())
                    label.setText(texte[0:plac_heberg]+self.cv_heberg+texte[plac_heberg+7:])
                if label.displayText().find("$jr1enc_am")>-1:
                    label.setText(str(self.cv_j1_enc_am))
                if label.displayText().find("$jr1enc_pm")>-1:
                    label.setText(str(self.cv_j1_enc_pm))
                if label.displayText().find("$jr1tot_am")>-1:
                    label.setText(str(self.cv_j1_tot_am))
                if label.displayText().find("$jr1tot_pm")>-1:
                    label.setText(str(self.cv_j1_tot_pm))
                if label.displayText().find("$jr1cen_am")>-1:
                    label.setText(str(self.cv_j1adcen_am))
                if label.displayText().find("$jr1cen_pm")>-1:
                    label.setText(str(self.cv_j1adcen_pm))
                if label.displayText().find("$jr1blo_am")>-1:
                    label.setText(str(self.cv_j1_blon_am))
                if label.displayText().find("$jr1blo_pm")>-1:
                    label.setText(str(self.cv_j1_blon_pm))
                if label.displayText().find("$jr2enc_am")>-1:
                    label.setText(str(self.cv_j2_enc_am))
                if label.displayText().find("$jr2enc_pm")>-1:
                    label.setText(str(self.cv_j2_enc_pm))
                if label.displayText().find("$jr2tot_am")>-1:
                    label.setText(str(self.cv_j2_tot_am))
                if label.displayText().find("$jr2tot_pm")>-1:
                    label.setText(str(self.cv_j2_tot_pm))
                if label.displayText().find("$jr2cen_am")>-1:
                    label.setText(str(self.cv_j2adcen_am))
                if label.displayText().find("$jr2cen_pm")>-1:
                    label.setText(str(self.cv_j2adcen_pm))
                if label.displayText().find("$jr2blo_am")>-1:
                    label.setText(str(self.cv_j2_blon_am))
                if label.displayText().find("$jr2blo_pm")>-1:
                    label.setText(str(self.cv_j2_blon_pm))
                if label.displayText().find("$sem_enc")>-1:
                    label.setText(str(self.cv_sem_enc))
                if label.displayText().find("$sem_ben")>-1:
                    label.setText(str(self.cv_sem_ben))
            else:
                if re.match("^\$jr",label.displayText()) or re.search("\$sem",label.displayText()) or re.search("\$nb",label.displayText()):
                    label.setText('0')
                if re.search("\$partenair",label.displayText()) or re.search("\$heberg",label.displayText()):
                    label.setText(' ')
                # le module re permet de chercher des chaînes dans du texte avec des expression régulières
                # match => le début du texte doit correspondre
                #search : on cherche la chaîne quelque-part dans le texte.
                #le \ permet d'échapper le $ (qui correspond normalement à une fin de ligne dans une regexp).



    def composerMapSetBBox(self, geom, margin = None):
    # crée la bbox pour la carte en cours.
        #Configure une nouvelle étendue avec un marge optionnelle (en %) pour la carte
        self.composerMap.setNewExtent(self.getNewExtent(geom, margin))



    def getNewExtent(self, geom, margin = None):
        #Calcule une étendue de la géometrie, avec une marge donnée (en %)
        #afin de pouvoir l'afficher dans la carte sélectionnée
        #Gère les géomlétries non carrées pour garder le même ratio
        # Calcule les coordonnées etle ratio
        new_extent = None
        x1, y1, x2, y2 = (0, 0, 0, 0)
        geom_rect = geom.extent()
        geom_ratio = geom_rect.width() / geom_rect.height()
        xa1 = geom_rect.xMinimum()
        xa2 = geom_rect.xMaximum()
        ya1 = geom_rect.yMinimum()
        ya2 = geom_rect.yMaximum()
        map_rect = self.composerMap.boundingRect()
        map_ratio = map_rect.width() / map_rect.height()
        # la hauteur de la géométrie est trop grande
        if geom_ratio < map_ratio:
            y1 = ya1
            y2 = ya2
            x1 = (xa1 + xa2 + map_ratio * (ya1 - ya2)) / 2.0
            x2 = x1 + map_ratio * (ya2 - ya1)
            new_extent = QgsRectangle(x1, y1, x2, y2)
        # la largeur de la géométrie est trop grande
        elif geom_ratio > map_ratio:
            x1 = xa1
            x2 = xa2
            y1 = (ya1 + ya2 + (xa1 - xa2) / map_ratio) / 2.0
            y2 = y1 + (xa2 - xa1) / map_ratio
            new_extent = QgsRectangle(x1, y1, x2, y2)
        # même ratio: renvoyer la bounding box de la géométrie
        else:
            new_extent = geom_rect
        # ajouter la marge à l'étendue calculée
        if margin:
            new_extent.scale(1 + margin / 100.0)
        return new_extent


    def operationOnTop(self):
    # Afficher le formulaire "operationdialog.py" (Qdialog) devant iface (QmainWindow) lorsque l'on ferme le composeur (QgsComposerView)
            self.raise_()
            self.activateWindow()
            print 'operationOnTop'

