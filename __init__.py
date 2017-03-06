# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BdTravaux
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
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def name():
    return "Saisie_travaux"


def description():
    return "Plugin d'aide à la saisie à destination des gardes-techniciens"


def version():
    return "Version 0.9"


def icon():
    return "icon.png"


def qgisMinimumVersion():
    return "2.0"

def author():
    return "CEN NPdC"

def email():
    return "vincent.damoy@espaces-naturels.fr"

def classFactory(iface):
    # load BdTravaux class from file BdTravaux
    from bd_cen import BdTravaux
    return BdTravaux(iface)
