# -*- coding: utf-8 -*-
from qgis.core import *

def convert_geometries(geomlist, geomtype):
    """Convert a list of QgsGeometries to a specific geometry type.
    All geometries in list must be of the same type
    Possible conversions :
    * (multi)polygon -> point : centroid
    * (multi)linestring -> point : centroid
    * (multi)linestring -> polygon : close linestrings and build multipolygon
    * (multi)polygon -> linestring : take external rings and build multilinestring
    * (multi)point -> linestring : take all points in given order and build linestring
    * (multi)point -> polygon : take all points in given order and build one polygon
    :param geomlist: list of QgsGeometries
    :param geomtype: desired output geometry type among QGis.Point, QGis.Polyline, QGis.Polygon
    :returns: desired geometry or None if conversion failed
    """
    ret = None
    if len(set([geom.type() for geom in geomlist])) <> 1:
        print [geom.type() for geom in geomlist]
        ret = None
    else:
    #if geomlist[0].type() == geomtype:
        #ret =  None #QgsGeometry([feature.asGeometryCollection() for feature in geomlist])
        if geomlist[0].type() == QGis.Line and geomtype == QGis.Line:
            ret = lines_line(geomlist)
        elif geomlist[0].type() == QGis.Polygon and geomtype == QGis.Polygon:
            ret = polygons_polygon(geomlist)
        elif geomlist[0].type() == QGis.Point and geomtype == QGis.Point:
            ret = points_point(geomlist)
        elif geomlist[0].type() == QGis.Polygon and geomtype == QGis.Point:
            ret = polygons_point(geomlist)
        elif geomlist[0].type() == QGis.Polygon and geomtype == QGis.Line:
            ret = polygons_linestring(geomlist)
        elif geomlist[0].type() == QGis.Line and geomtype == QGis.Point:
            ret = linestrings_point(geomlist)
        elif geomlist[0].type() == QGis.Line and geomtype == QGis.Polygon:
            ret = linestrings_polygon(geomlist)
        elif geomlist[0].type() == QGis.Point and geomtype == QGis.Line:
            ret = points_linestring(geomlist)
        elif geomlist[0].type() == QGis.Point and geomtype == QGis.Polygon:
            ret = points_polygon(geomlist)
    return ret

def lines_line(linegeoms):
    return QgsGeometry.fromMultiPolyline([line.asPolyline() for line in linegeoms])

def points_point(pointgeoms):
    return QgsGeometry.fromMultiPoint([point.asPoint() for point in pointgeoms])

def polygons_polygon(polygeoms):
    return QgsGeometry.fromMultiPolygon([poly.asPolygon() for poly in polygeoms])

def linestrings_polygon(linegeoms):
    polygons = []
    for linegeom in linegeoms:
        polyline = linegeom.asPolyline()
        polyline.append(polyline[0])
        polygons.append([[QgsPoint(i, j) for i,j in polyline]])
    return QgsGeometry.fromMultiPolygon(polygons)

def linestrings_point(linegeoms):
    return QgsGeometry.fromMultiPolyline([line.asPolyline() for line in linegeoms]).centroid()

def polygons_point(polygeoms):
    return QgsGeometry.fromMultiPolygon([poly.asPolygon() for poly in polygeoms]).centroid()

def points_linestring(pointgeoms):
    return QgsGeometry.fromPolyline(pointgeoms)

def points_polygon(pointgeoms):
    return linestrings_polygon([points_linestring(pointgeoms)])

def polygons_linestring(polygeoms):
    lines = []
    for polygeom in polygeoms:
        print "polygeom="
        print polygeom.asPolygon()
        for ring in polygeom.asPolygon():
            lines.append(ring)
            print "ring="
            print ring
    return QgsGeometry.fromMultiPolyline(lines)


    
if __name__ == "__main__":
    linesgeom = [QgsGeometry.fromPolyline([QgsPoint(i, j) for i, j in [(-1.05404,0.924307), (-0.445411,0.675137), (-0.853888,-0.166325), (-1.47477,0.381033), (-1.56872,0.662882), (-1.50745,0.916138), (-1.35223,0.920223), (-1.27053,0.613865), (-1.04587,0.732323), (-1.12348,0.809934), (-1.12348,0.809934), (-1.16025,1.02234)]]),
            QgsGeometry.fromPolyline([QgsPoint(i,j) for i, j in [(0.363373,0.376949), (0.967918,0.26666), (1.02919,-0.43592), (0.142795,-0.721854), (-0.523022,-0.190834), (-0.249343,-0.129563), (0.106032,-0.190834), (0.0978627,0.054252), (0.0120826,0.356525), (0.0284216,0.405542)]])]
    # lines to polygon
    poly = convert_geometries(linesgeom, QGis.Polygon)
    print poly.exportToWkt()

    # lines to point
    point = convert_geometries(linesgeom, QGis.Point)
    print point.exportToWkt()

    point2 = convert_geometries([poly], QGis.Point)
    print point2
    

