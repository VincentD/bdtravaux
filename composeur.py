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

from PyQt4 import QtCore, QtGui, QtSql, QtXml, Qt
from qgis.core import *
from qgis.gui import *
import sys                                          # Pour changer le chemin du modèle de composeur en fonction de l'OS
import inspect                                      # ???
import re                                           # Pour la méthode find : trouve des mots-clés dans les étiquettes du composeur
import random                                       # Pour choisir des couleurs au hasard dans le module Affiche

# créer une classe composeur (self) pour gérer toutes les classes "enfants" dans le module

    def recupDonnSortie(self):
        #recup de données en fction de l'Id de la sortie. Pr afficher le site dans affiche(), les txts des étiqu dans composeur() et mettre à jour "opprev" et "chx_opechvol" au lancement du module, et qd une nouvelle sortie est sélectionnée.
        querycodesite = QtSql.QSqlQuery(self.db)
        qcodesite = u"""select codesite, array_to_string(array(select distinct salaries from bdtravaux.join_salaries where id_joinsal=sortie_id), '; ') as salaries, date_sortie, chantvol, sortcom, objvisite, objvi_autr, natfaune, natflore, natautre from bdtravaux.sortie where sortie_id = {zr_sortie_id}""".format \
        (zr_sortie_id = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        ok2 = querycodesite.exec_(qcodesite)
        print qcodesite
        if not ok2:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête recupDonnSortie ratée')
        querycodesite.next()
        self.codedusite=querycodesite.value(0)
        self.salaries=querycodesite.value(1)
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



    def clr_hasard(self):
        # renvoie une couleur au hasard, en hexadécimal. Utilisé pour attribuer une couleur aux polygones affichés en fonction de leur catégorie.
        r=lambda: random.randint(0,255)
        couleur='#%02X%02X%02X' % (r(),r(),r())
        return couleur
        



    def affiche(self):
        # Fonction affichant dans QGIS les entités de la sortie en cours, présentes en base.
        # Accès à la base de données postgresql/postigs : cf l.52

        # Requête qui sera intégrée dans uri.setDataSource() (cf. paragraphe ci-dessous)
        reqwhere="""sortie="""+str(self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        # Affichage de la couche de polygoness si des surfaces sont saisis pour cette sortie
        # Configure le shéma, le nom de la table, la colonne géométrique, et un sous-jeu de données (clause WHERE facultative)
        self.uri.setDataSource("bdtravaux", "operation_poly", "the_geom", reqwhere)
        # Instanciation de la couche dans qgis 
        self.gestrealpolys=QgsVectorLayer(self.uri.uri(), "gestrealpolys", "postgres")
        if self.gestrealpolys.featureCount()>0:
            #si la couche importée n'est pas vide, intégration dans le Map Layer Registry pour pouvoir l'utiliser
            QgsMapLayerRegistry.instance().addMapLayer(self.gestrealpolys)
            # Attribution de couleurs différentes aux opérations
            # Récupération des valeurs uniques du champ qui servira de base à la symbologie
            layer=self.gestrealpolys
            field_index = layer.dataProvider().fieldNameIndex('typ_operat')
            unique_values = layer.uniqueValues(field_index)
            # Définit une correspondance: valeur -> (couleur) au moyen d'un dictionnaire et de la fonction clr_hasard
            # Création du dictionnaire au moyen d'une compréhension de dictionnaire
            operations={valeurunique : self.clr_hasard() for valeurunique in unique_values}
            # Crée une catégorie pour chaque item dans operations, puis les groupe en une liste (operations)
            categories = []
            for nom_opera, couleur in operations.items():
                symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
                symbol.setColor(QtGui.QColor(couleur))
                category = QgsRendererCategoryV2(nom_opera, symbol,nom_opera)
                categories.append(category)
            # Crée le renderer et l'assigne à la couche
            expression = 'typ_operat' # field name
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            layer.setRendererV2(renderer)
        else:
            print 'couche de surfaces vide'

        # Affichage de la couche de lignes si des linéaires sont saisis pour cette sortie
        self.uri.setDataSource("bdtravaux", "operation_lgn", "the_geom", reqwhere)
        self.gestreallgn=QgsVectorLayer(self.uri.uri(), "gestreallgn", "postgres")
        if self.gestreallgn.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.gestreallgn)
            layer=self.gestreallgn
            field_index = layer.dataProvider().fieldNameIndex('typ_operat')
            unique_values = layer.uniqueValues(field_index)
            operations={valeurunique : self.clr_hasard() for valeurunique in unique_values}
            categories = []
            for nom_opera, couleur in operations.items():
                symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
                symbol.setColor(QtGui.QColor(couleur))
                #création de la catégorie 1er param : l'attribut / 2ème : le symbole à appliquer / 3ème : l'étiquet ds tble matières
                category = QgsRendererCategoryV2(nom_opera, symbol,nom_opera)
                categories.append(category)
            expression = 'typ_operat' # field name
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            layer.setRendererV2(renderer)
        else :
            print 'couche de linéaires vide'

        # Affichage de la couche de points si des ponctuels sont saisis pour cette sortie
        self.uri.setDataSource("bdtravaux", "operation_pts", "the_geom", reqwhere)
        self.gestrealpts=QgsVectorLayer(self.uri.uri(), "gestrealpts", "postgres")
        if self.gestrealpts.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.gestrealpts)
            layer=self.gestrealpts
            field_index = layer.dataProvider().fieldNameIndex('typ_operat')
            unique_values = layer.uniqueValues(field_index)
            operations={valeurunique : self.clr_hasard() for valeurunique in unique_values}
            categories = []
            for nom_opera, couleur in operations.items():
                symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())
                symbol.setColor(QtGui.QColor(couleur))
                category = QgsRendererCategoryV2(nom_opera, symbol,nom_opera)
                categories.append(category)
            expression = 'typ_operat' # Nom du champ
            renderer = QgsCategorizedSymbolRendererV2(expression, categories)
            layer.setRendererV2(renderer)
        else :
            print 'couche de ponctuels vide'


    def creaComposeur(self):
        #Intégration en base de la dernière opération saisie
        if sourceAffiche=='ModOperation':
            self.sauverOpeChoi()
            print 'ModOperation'
        #S'il y a des entités géographiques dans la sortie, les afficher
        if self.sansgeom!='True':
            self.affiche()
        #Récupération des données de la table "sortie" pour affichage du site et utilisation dans les étiquettes du composeur
        self.recupDonnSortie()
        reqwheresit="""codesite='"""+str(self.codedusite)+"""'"""
        self.uri.setDataSource("sites_cen", "t_sitescen", "the_geom", reqwheresit)
        self.contours_site=QgsVectorLayer(self.uri.uri(), "contours_site", "postgres")
        # Affichage du site
        if self.contours_site.featureCount()>0:
            QgsMapLayerRegistry.instance().addMapLayer(self.contours_site)
        # Symbologie du contour de site
            # create a new single symbol renderer
        symbol = QgsSymbolV2.defaultSymbol(self.contours_site.geometryType())
        renderer = QgsSingleSymbolRendererV2(symbol)
            # create a new simple marker symbol layer, a white circle with a black border
        properties = {'color': 'green', 'color_border': 'red'}
        symbol_layer = QgsSimpleFillSymbolLayerV2.create(properties)
        symbol_layer.setBrushStyle(0) #0 = Qt.NoBrush. Cf doc de QBrush
            # assign the symbol layer to the symbol renderer
        renderer.symbols()[0].changeSymbolLayer(0, symbol_layer)
            # assign the renderer to the layer
        self.contours_site.setRendererV2(renderer)


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
        # Adaptation de la composition : 2 pages A3
        self.composition.setPaperSize(420, 297)
        self.composition.setNumPages(2)


        #TEMPLATE : Récupération du template. Intégration des ses éléments dans la carte.
        if sys.platform.startswith('linux'):
            file1=QtCore.QFile('/home/vincent/.qgis2/python/plugins/bdtravaux/BDT_20130705_T_CART_ComposerTemplate.qpt')
        if sys.platform.startswith('win32'):
            file1=QtCore.QFile('C:\qgistemplate\BDT_20130705_T_CART_ComposerTemplate.qpt')
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
        x, y, w, h = 5, 28, 408, 240
        self.composerMap.setItemPosition(x, y, w, h)
        #Crée la bbox autour du site pour la carte en cours (fonction mapItemSetBBox l 293)
        #self.contours_sites est défini dans la fonction affiche()
        self.margin=10
        self.composerMapSetBBox(self.contours_site, self.margin)
                    #(Dé)zoome sur l'ensemble des deux pages du composeur
                    #self.composition.mActionZoomFullExtent().trigger()


        #LEGENDE : mettre à jour la légende. 
        for i in self.composition.items():
            if isinstance(i,QgsComposerLegend):
                legend = i 
                legend.updateLegend()


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
                label.setText(texte[0:plac_redac]+self.salaries+texte[plac_redac+6:])
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
    # les couches de points, lignes et polygones créées pour le compte-rendu ainsi que le contour du site sont supprimées avec le composeur.
        self.raise_()
        self.activateWindow()
        if self.gestrealpolys:
            QgsMapLayerRegistry.instance().removeMapLayer( self.gestrealpolys.id() )
        if self.gestreallgn:
            QgsMapLayerRegistry.instance().removeMapLayer( self.gestreallgn.id() )
        if self.gestrealpts:
            QgsMapLayerRegistry.instance().removeMapLayer( self.gestrealpts.id() )
        if self.contours_site:
            QgsMapLayerRegistry.instance().removeMapLayer( self.contours_site.id() )
