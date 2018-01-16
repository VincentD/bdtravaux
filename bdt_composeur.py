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
import sys
import re
import random

class composerClass (QtGui.QDialog):
    def __init__(self):

        QtGui.QDialog.__init__(self)
        #Référencement de iface dans l'interface
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

        # Connexion à la BD PostgreSQL
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



    def Composer(self, idsortie, idsite):
        #print 'dans composeur, id_sortie='+str(idsortie)
        
        # Si le bouton "Bordereau de terrain" a été cliqué -> on n'affiche que le contour du site sélectionné
        if idsite != '000':
            self.donnees_ImprBordereau(idsite)
            
        # Si les boutons "Réimprimer une sortie" ou "Dernier- Editer CR" ont été cliqués -> on affiche les données de la sortie sélectionnée
        else:
            #Affichage des contours du site
            #Récupération des données de la table "sortie" pour affichage du site et utilisation dans les étiquettes du composeur
            self.recupDonnSortie(idsortie)
            reqwheresit="""codesite='"""+str(self.codedusite)+"""'"""
            self.uri.setDataSource("sites_cen", "t_sitescen", "the_geom", reqwheresit)
            self.contours_site=QgsVectorLayer(self.uri.uri(), "contours_site", "postgres")
            # Import de la couche contenant les contours du site
            root = QgsProject.instance().layerTreeRoot()
            if self.contours_site.featureCount()>0:
               QgsMapLayerRegistry.instance().addMapLayer(self.contours_site, False)
               root.insertLayer(0, self.contours_site)
            # Symbologie du contour de site
                # create a new single symbol renderer
            symbol = QgsSymbolV2.defaultSymbol(self.contours_site.geometryType())
            renderer = QgsSingleSymbolRendererV2(symbol)
                # create a new simple marker symbol layer
            properties = {'color': 'green', 'color_border': 'red'}
            symbol_layer = QgsSimpleFillSymbolLayerV2.create(properties)
            symbol_layer.setBrushStyle(0) #0 = Qt.NoBrush. Cf doc de QBrush
                # assign the symbol layer to the symbol renderer
            renderer.symbols()[0].changeSymbolLayer(0, symbol_layer)
                # assign the renderer to the layer
            self.contours_site.setRendererV2(renderer)


            #Appel à la fonction "affiche", qui importe les couches non vides de gestion réalisée, parmi operation_poly, operation_lgn et operation_pts
            self.affiche(idsortie)


            # Affichage des couches contenant les contours du site et les opérations de gestion saisies, et masquage des autres
            self.rendreVisible=[]
            layers=iface.legendInterface().layers()
            for layer in layers:
                if layer.type()==QgsMapLayer.VectorLayer:
                    if layer.name()=='gestrealpolys' or layer.name()=='gestreallgn' or layer.name()=='gestrealpts' or layer.name()=='contours_site':
                        iface.legendInterface().setLayerVisible(layer, True)
                    else:
                        if iface.legendInterface().isLayerVisible(layer):
                            self.rendreVisible.append(layer)
                        iface.legendInterface().setLayerVisible(layer, False)


            #Récupération des données de la table "ch_volont" pour utilisation dans les étiquettes du composeur
            self.recupDonnChVolont(idsortie)

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
        # Adaptation de la composition : 2 pages A3
        self.composition.setPaperSize(420, 297)
        self.composition.setNumPages(2)
        
#        self.iface.actionZoomFullExtent().trigger()


        #TEMPLATE : Récupération du template. Intégration des ses éléments dans la carte.
        if sys.platform.startswith('linux'):
            file1=QtCore.QFile(QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bd_cen/BDT_20130705_T_CART_ComposerTemplate_linux.qpt")   
#            file1=QtCore.QFile(QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bd_cen/BDT_20130705_T_CART_ComposerTemplate.qpt")   
            if file1.exists():
                print 'trouve le modele de composeur'
            else:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Pas trouvé le modèle du composeur sous Linux')
        if sys.platform.startswith('win32'):
            file1=QtCore.QFile(QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "python/plugins/bdcen/BDT_20130705_T_CART_ComposerTemplate_win.qpt")
#            file1=QtCore.QFile(QtCore.QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "\python\plugins\\bd_cen\BDT_20130705_T_CART_ComposerTemplate.qpt")
            if file1.exists():
                print 'trouve le modele de composeur'
            else:
                QtGui.QMessageBox.warning(self, 'Alerte', u'Pas trouvé le modèle du composeur sous Windows')
        doc=QtXml.QDomDocument()
        doc.setContent(file1, False)
        elem=doc.firstChildElement()
        self.composition.loadFromTemplate(doc, substitutionMap=None, addUndoCommands =False)


        #CARTE : Récupération de la carte. 
        maplist=[]
        for item in self.composition.composerMapItems():
            maplist.append(item)
        self.composerMap=maplist[0]
        #Taille définie pour la carte
        x, y, w, h, mode, frame, page = 5, 15, 408, 270, QgsComposerItem.UpperLeft, False, 1
        self.composerMap.setItemPosition(x, y, w, h, mode, frame, page)
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

        #trouver les opérations effectuées lors de la sortie et leurs commentaires dans la table postgresql, selon l'id de la sortie sélectionnée dans le module "opération"
        # une boucle permet de récupérer et afficher à la suite dans une seule zone de texte toutes les opérations et leurs descriptions
        querycomope = QtSql.QSqlQuery(self.db)
        qcomope=u"""select operation_id, (select distinct array_to_string(array(select distinct typoperation from bdtravaux.join_typoperation where id_jointyp=id_oper order by typoperation),'; ')) as typope, round(st_area(the_geom)::numeric,2) as surface, round(st_length(the_geom)::numeric,2) as longueur, ST_NumGeometries(the_geom) as compte, (select distinct array_to_string(array(select distinct operateurs from bdtravaux.join_operateurs where id_joinop=id_oper order by operateurs),'; ')) as operateurs, (select distinct array_to_string(array(select distinct lblope from bdtravaux.join_opeprevues where id_joinprev=id_oper order by lblope),'; ')) as opeprev, (select distinct array_to_string(array(select distinct codeope from bdtravaux.join_opeprevues where id_joinprev=id_oper order by codeope),'; ')) as codeope, case when chantfini=True then 'Opération terminée' else '' end , descriptio from (select * from bdtravaux.operation_poly UNION select * from bdtravaux.operation_lgn UNION select * from bdtravaux.operation_pts) tables where sortie={zr_sortie} order by typ_operat""".format \
        (zr_sortie = idsortie) #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        ok3 = querycomope.exec_(qcomope)
        if not ok3:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête operations ratée')
            #print qcomope
        querycomope.first()
        texteope=""
        #Requête : Données à récupérer pour chaque opération de la sortie
        for i in xrange(0 , querycomope.size()):
            #Récupération des autres valeurs de chaque opération
            idope=unicode(querycomope.value(0))
            ope=unicode(querycomope.value(1))
            surfope=unicode(querycomope.value(2))
            longope=unicode(querycomope.value(3))
            countope=unicode(querycomope.value(4))
            operatope=unicode(querycomope.value(5))
            opeprev=unicode(querycomope.value(6))
            ghopeprev=unicode(querycomope.value(7))
            finiope=unicode(querycomope.value(8))
            descrope=unicode(querycomope.value(9)).replace('\n','<br/>')
            texteope=unicode(texteope+u'<br/>'+u'<b>'+ope+u'</b>'+u'<h style="margin-left:1cm;">'+u'/'+u'<h style="margin-left:0.5cm;">'+surfope+u' m²'+'<h style="margin-left:0.5cm;">'+u'/'+u'<h style="margin-left:0.5cm;">'+longope+u' ml<h style="margin-left:0.5cm;">'+u'/'+u'<h style="margin-left:0.5cm;">'+countope+u' geom<h style="margin-left:0.5cm;">'+u'/'+u'<h style="margin-left:0.5cm;">'+operatope+u'<br/>'+opeprev+u'<h style="margin-left:1cm;">('+ ghopeprev+u')'+u'<h style="margin-left:0.5cm;">'+u'<b>'+finiope+u'<h style="margin-left:0.5cm;">'+u'/ id ='+u'<h style="margin-left:0.2cm;">'+idope+u'</b><br/>'+descrope+u'<br/>')
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
            if label.displayText().find("$salaries")>-1:
                plac_redac=label.displayText().find("$salaries")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_redac]+self.salaries+texte[plac_redac+9:])
            if label.displayText().find("$date")>-1:
                plac_date=label.displayText().find("$date")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_date]+self.datesortie+texte[plac_date+5:])
            if label.displayText().find("$datefin")>-1:
                plac_date=label.displayText().find("$datefin")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_date]+self.datefin+texte[plac_date+8:])
            if label.displayText().find("$jourschan")>-1:
                plac_date=label.displayText().find("$jourschan")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_date]+self.jourschan+texte[plac_date+10:])
            if label.displayText().find("$idsortie")>-1:
                plac_date=label.displayText().find("$idsortie")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_date]+str(idsortie)+texte[plac_date+9:])
            if label.displayText().find("$commsortie")>-1:
                plac_commsortie=label.displayText().find("$commsortie")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_commsortie]+self.sortcom+texte[plac_commsortie+11:])
            if label.displayText().find("$nomsite")>-1:
                plac_nomsite=label.displayText().find("$nomsite")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_nomsite]+self.nomdusite+texte[plac_nomsite+8:])
            if label.displayText().find("$commope")>-1:
                label.setText(texteope)
            if label.displayText().find("$objet")>-1:
                plac_objet=label.displayText().find("$objet")
                texte=unicode(label.displayText())
                label.setText(texte[0:plac_objet]+self.objvisite+texte[plac_objet+6:])
            if label.displayText().find("$objvi_autre")>-1:
                plac_objautre=label.displayText().find("$objvi_autre")
                texte=unicode(label.displayText())
                if self.objautre:
                    label.setText(texte[0:plac_objautre]+self.objautre.strip('; ')+texte[plac_objautre+12:])
                else:
                    label.setText(texte[0:plac_objautre]+''+texte[plac_objautre+12:])
            if label.displayText().find("$natfaune")>-1:
                label.setText(self.natfaune)
            if label.displayText().find("$natflore")>-1:
                label.setText(self.natflore)
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


        #LEGENDE : mettre à jour la légende. 
        for i in self.composition.items():
            if isinstance(i,QgsComposerLegend):
                #print "mise a jour legende"
                legend = i 
                legend.setAutoUpdateModel(True)
                for j in xrange(legend.modelV2().rowCount()):
                    modelindex=legend.modelV2().index(j, 0)
                    layertreenode=legend.modelV2().index2node(modelindex)
#                    print modelindex.data()
#                    print modelindex.__class__.__name__
#                    print layertreenode.__class__.__name__
                    if isinstance(layertreenode, QgsLayerTreeGroup):
                        layertreenode.setVisible(False)
#                        print modelindex.data()
#                        layertreenode.setName("")
#                        print modelindex.data()
                    else:
                         print 'Layer'
                legend.setAutoUpdateModel(False)
                legend.setLegendFilterByMapEnabled(True)



    def donnees_ImprBordereau(self, idsite):
        self.querypoly = QtSql.QSqlQuery(self.db)
        qpoly=u"""select operation_id from bdtravaux.operation_poly where sortie=999999999 order by operation_id limit 1"""
        okpoly = self.querypoly.exec_(qpoly)

#        self.querylgn = ''
#        self.querypts = ''
        #Affiche les couches qui apparaîtront dans le composeur après choix du site dans l'onglet "Bordereau de terrain"
        print 'bouton bordereau cliqué'
        reqbordsite="""codesite='"""+str(idsite)+"""'"""
        self.uri.setDataSource("sites_cen", "t_sitescen", "the_geom", reqbordsite)
        self.contours_site=QgsVectorLayer(self.uri.uri(), "contours_site", "postgres")
        # Import de la couche contenant les contours du site
        root = QgsProject.instance().layerTreeRoot()
        if self.contours_site.featureCount()>0:
           QgsMapLayerRegistry.instance().addMapLayer(self.contours_site, False)
           root.insertLayer(0, self.contours_site)
        # Symbologie du contour de site
            # create a new single symbol renderer
        symbol = QgsSymbolV2.defaultSymbol(self.contours_site.geometryType())
        renderer = QgsSingleSymbolRendererV2(symbol)
            # create a new simple marker symbol layer
        properties = {'color': 'green', 'color_border': 'red'}
        symbol_layer = QgsSimpleFillSymbolLayerV2.create(properties)
        symbol_layer.setBrushStyle(0) #0 = Qt.NoBrush. Cf doc de QBrush
            # assign the symbol layer to the symbol renderer
        renderer.symbols()[0].changeSymbolLayer(0, symbol_layer)
            # assign the renderer to the layer
        self.contours_site.setRendererV2(renderer)
            
        # Affichage de la couche contenant les contours du site, et masquage des autres
        self.rendreVisible=[]
        layers=iface.legendInterface().layers()
        for layer in layers:
            if layer.type()==QgsMapLayer.VectorLayer:
                if layer.name()=='contours_site':
                    iface.legendInterface().setLayerVisible(layer, True)
                else:
                    if iface.legendInterface().isLayerVisible(layer):
                        self.rendreVisible.append(layer)
                    iface.legendInterface().setLayerVisible(layer, False)
        # Récupération du code et du nom du site et remplissage des objets qui remplaceront les étiquettes du composeur.
        querysite = QtSql.QSqlQuery(self.db)
        qsite = u"""select codesite, nomsite from sites_cen.t_sitescen where codesite = '{zr_idsite}'""".format \
        (zr_idsite = str(idsite))
        #print qsite
        oksite = querysite.exec_(qsite)
        if not oksite :
            print 'Requête site ratée'
        querysite.next()
        self.codedusite=querysite.value(0)
        self.nomdusite=querysite.value(1)
        self.redacteur = self.salaries = self.datesortie = self.datefin = self.jourschan = self.chantvol = self.sortcom = self.objvisite =\
        self.objautre = self.natfaune = self.natflore = self.natautre = self.cv_nb_jours = self.cv_nb_heur_ch = self.cv_nb_heur_de =\
        self.cv_partenaire = self.cv_heberg = self.cv_j1_enc_am = self.cv_j1_enc_pm = self.cv_j1_tot_am = self.cv_j1_tot_pm =\
        self.cv_j1adcen_am = self.cv_j1adcen_pm = self.cv_j1_blon_am = self.cv_j1_blon_pm = self.cv_j2_enc_am = self.cv_j2_enc_pm =\
        self.cv_j2_tot_am = self.cv_j2_tot_pm = self.cv_j2adcen_am = self.cv_j2adcen_pm = self.cv_j2_blon_am = self.cv_j2_blon_pm =\
        self.cv_sem_enc = self.cv_sem_ben = ''


    def recupDonnSortie(self, idsortie):
        #print 'dans recupDonnSortie, id_sortie='+str(idsortie)
        #recup de données en fction de l'Id de la sortie. Pr afficher le site et les txts des étiqu dans composeur()
        querycodesite = QtSql.QSqlQuery(self.db)
        qcodesite = u"""select sor.codesite, 
(select nomsite from sites_cen.t_sitescen sit where sit.codesite=sor.codesite) as nomsite, redacteur , array_to_string(array(select distinct salaries from bdtravaux.join_salaries where id_joinsal=sortie_id), '; ') as salaries, date_sortie, date_fin, jours_chan, chantvol, sortcom, array_to_string(array(select distinct objvisite from bdtravaux.join_objvisite where id_joinvis=sortie_id), '; ') as objvisite, array_to_string(array(select distinct objviautre from bdtravaux.join_objvisite where id_joinvis=sortie_id), '; ') as objviautre, natfaune, natflore, natautre from bdtravaux.sortie sor where sortie_id = {zr_sortie_id}""".format \
        (zr_sortie_id = str(idsortie)) #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        ok2 = querycodesite.exec_(qcodesite)
        if not ok2:
            print u'Requête recupDonnSortie ratée'
        querycodesite.next()
        self.codedusite=querycodesite.value(0)
        self.nomdusite=querycodesite.value(1)
        self.redacteur=querycodesite.value(2)
        self.salaries=querycodesite.value(3)
        self.datesortie=querycodesite.value(4).toPyDate().strftime("%Y-%m-%d")
        self.datefin=querycodesite.value(5).toPyDate().strftime("%Y-%m-%d")
        self.jourschan=querycodesite.value(6)
        self.chantvol=querycodesite.value(7)
        self.sortcom=querycodesite.value(8).replace('\n','<br/>')
        self.objvisite=querycodesite.value(9)
        self.objautre=querycodesite.value(10)
        self.natfaune=querycodesite.value(11).replace('\n','<br/>')
        self.natflore=querycodesite.value(12).replace('\n','<br/>')
        self.natautre=querycodesite.value(13).replace('\n','<br/>')



    def affiche(self, idsortie):
        # Fonction affichant dans QGIS les entités de la sortie en cours, présentes en base.
        # Pour l'accès à la base de données postgresql/postigs, voir l.52

        # Référencer l'arborescence de la TOC (layer tree). Cela permettra de placer la (les) couche(s) où l'on veut à l'intérieur (i.e. en haut, et en dehors d'un groupe)
        root = QgsProject.instance().layerTreeRoot()

        # Requête qui sera intégrée dans uri.setDataSource() (cf. paragraphe ci-dessous)
        reqwhere="""sortie_id="""+str(idsortie)+""" and the_geom IS NOT NULL""" 

        # SURFACES : Import de la couche de polygones si des surfaces sont saisies pour cette sortie
        self.querypoly = QtSql.QSqlQuery(self.db)
        qpoly=u"""select operation_id from bdtravaux.operation_poly where sortie={zr_sortie} order by operation_id limit 1""".format (zr_sortie = idsortie)
        okpoly = self.querypoly.exec_(qpoly)
        if not okpoly:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête existence polygones ratée')
        if self.querypoly.size()>0:
            #print 'taille requete'+str(self.querypoly.size)
        # Configure le schéma, le nom de la table, la colonne géométrique, un sous-jeu de données (clause WHERE facultative), et une clé primaire.
            self.uri.setDataSource("bdtravaux", "v_bdtravaux_surfaces", "the_geom", reqwhere, "operation_id")
        # Instanciation de la couche dans qgis 
            self.gestrealpolys=QgsVectorLayer(self.uri.uri(), "gestrealpolys", "postgres")
            # Intégration dans le MapLayerRegistry pour pouvoir l'utiliser, MAIS sans l'importer dans l'arbo (d'où le False)
            QgsMapLayerRegistry.instance().addMapLayer(self.gestrealpolys, False)
            # Intégration de la couche dans l'arborescence, à l'index 0 (c'est à dire en haut de l'arborescence)
            root.insertLayer(0, self.gestrealpolys)
            ## Attribution de COULEURS différentes aux opérations
            # Récupération des valeurs uniques du champ qui servira de base à la symbologie
            layer = self.gestrealpolys
            field_index = layer.dataProvider().fieldNameIndex('lblope')
            unique_values = layer.uniqueValues(field_index)
            # Définit une correspondance: valeur -> (couleur) au moyen d'un dictionnaire et de la fonction clr_hasard
            # Création du dictionnaire au moyen d'une compréhension de dictionnaire
            operations={valeurunique : self.clr_hasard() for valeurunique in unique_values}
            # Crée une catégorie pour chaque item dans operations, puis les groupe en une liste (operations)
            categories = []
            for nom_opera, couleur in operations.items():
                symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
                symbol.setColor(QtGui.QColor(couleur))
                symbol.setAlpha(0.5)
                #création de la catég. 1er param : l'attribut / 2ème : le symbole à appliquer / 3ème : l'étiquet ds tble matières
                category = QgsRendererCategoryV2(nom_opera, symbol,nom_opera)
                categories.append(category)
            # Crée le renderer et l'assigne à la couche
            expression = 'lblope' # nom du champ
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            layer.setRendererV2(renderer)
            #layer.setLayerTransparency(50)
        else:
            print u'couche de surfaces vide'

        # LIGNES : Import de la couche de lignes si des linéaires sont saisis pour cette sortie
        self.querylgn = QtSql.QSqlQuery(self.db)
        qlgn=u"""select operation_id from bdtravaux.operation_lgn where sortie={zr_sortie} order by operation_id limit 1""".format (zr_sortie = idsortie )   #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        oklgn = self.querylgn.exec_(qlgn)
        if not oklgn:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête existence lignes ratée')
        if self.querylgn.size()>0:
            self.uri.setDataSource("bdtravaux", "v_bdtravaux_lignes", "the_geom", reqwhere, "operation_id")
            self.gestreallgn=QgsVectorLayer(self.uri.uri(), "gestreallgn", "postgres")
#        if self.gestreallgn.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.gestreallgn, False)
            root.insertLayer(0, self.gestreallgn)
            layer=self.gestreallgn
            field_index = layer.dataProvider().fieldNameIndex('lblope')
            unique_values = layer.uniqueValues(field_index)
            operations={valeurunique : self.clr_hasard() for valeurunique in unique_values}
            categories = []
            for nom_opera, couleur in operations.items():
                symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
                symbol.setColor(QtGui.QColor(couleur))
                symbol.setWidth(1.26)
                symbol.setAlpha(0.7)
                category = QgsRendererCategoryV2(nom_opera, symbol,nom_opera)
                categories.append(category)
            expression = 'lblope'
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            layer.setRendererV2(renderer)
        else :
            print u'couche de lineaires vide'

        # POINTS : Import de la couche de points si des ponctuels sont saisis pour cette sortie
        self.querypts = QtSql.QSqlQuery(self.db)
        qpts=u"""select operation_id from bdtravaux.operation_pts where sortie={zr_sortie} order by operation_id limit 1""".format (zr_sortie = idsortie)    #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        okpts = self.querypts.exec_(qpts)
        if not okpts:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête existence points ratée')
        if self.querypts.size()>0:
            self.uri.setDataSource("bdtravaux", "v_bdtravaux_points", "the_geom", reqwhere, "operation_id")
            self.gestrealpts=QgsVectorLayer(self.uri.uri(), "gestrealpts", "postgres")
        #if self.gestrealpts.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.gestrealpts, False)
            root.insertLayer(0, self.gestrealpts)
            layer=self.gestrealpts
            field_index = layer.dataProvider().fieldNameIndex('lblope')
            unique_values = layer.uniqueValues(field_index)
            operations={valeurunique : self.clr_hasard() for valeurunique in unique_values}
            categories = []
            for nom_opera, couleur in operations.items():
                symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
                symbol.setColor(QtGui.QColor(couleur))
                symbol.setSize(3)
                category = QgsRendererCategoryV2(nom_opera, symbol,nom_opera)
                categories.append(category)
            expression = 'lblope'
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            layer.setRendererV2(renderer)
        else :
            print u'couche de ponctuels vide'


    def clr_hasard(self):
        # renvoie une couleur au hasard, en hexadécimal. Utilisé pour attribuer une couleur aux polygones affichés en fonction de leur catégorie.
        r=lambda: random.randint(0,255)
        couleur='#%02X%02X%02X' % (r(),r(),r())
        return couleur


    def recupDonnChVolont(self, idsortie):
        # recup des données d'un chantier de volontaires en fction de l'Id de la sortie (et de l'opé). Pour afficher les textes ds composeur().
        querycodevolont = QtSql.QSqlQuery(self.db)
        qchvolont = u"""select nb_jours, nb_heur_ch, nb_heur_de, partenaire, heberg, j1_enc_am, j1_enc_pm, j1_tot_am, j1_tot_pm, j1adcen_am, j1adcen_pm, j1_blon_am, j1_blon_pm, j2_enc_am, j2_enc_pm, j2_tot_am, j2_tot_pm, j2adcen_am, j2adcen_pm, j2_blon_am, j2_blon_pm, sem_enc, sem_ben from bdtravaux.ch_volont where sortie={zr_sortie}""".format(zr_sortie=idsortie)    #self.ui.sortie.itemData(self.ui.sortie.currentIndex())
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



    def afterComposerClose(self):
    # les couches de points, lignes et polygones créées pour le compte-rendu ainsi que le contour du site sont supprimées avec le composeur.
        if self.querypoly.size()>0:
            QgsMapLayerRegistry.instance().removeMapLayer( self.gestrealpolys.id() )
        if self.querylgn.size()>0:
            QgsMapLayerRegistry.instance().removeMapLayer( self.gestreallgn.id() )
        if self.querypts.size()>0:
            QgsMapLayerRegistry.instance().removeMapLayer( self.gestrealpts.id() )
        if self.contours_site:
            QgsMapLayerRegistry.instance().removeMapLayer( self.contours_site.id() )
    # la visibilité de chaque couche revient à son état initial
        legend = self.iface.legendInterface()
        for wanted in self.rendreVisible:
            legend.setLayerVisible(wanted, True)
