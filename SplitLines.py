# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SplitLines
                                 A QGIS plugin
 Splits Lines at Points
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2022-11-21
        git sha              : $Format:%H$
        copyright            : (C) 2022 by HSBO
        email                : pia.rolf@stud.hs-bochum.de
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
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QVariant
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .SplitLines_dialog import SplitLinesDialog
import os.path
from qgis.core import *
import collections
import math
import processing
# from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsFeature, QgsGeometry, QgsProject, QgsField
import shapely.ops
from shapely.geometry import LineString


class SplitLines:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SplitLines_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SplitLines')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SplitLines', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/SplitLines/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Split Lines at Points'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&SplitLines'),
                action)
            self.iface.removeToolBarIcon(action)


    def sliderChange(self):
        self.dlg.selectedDistance.display(self.dlg.DistanceSelect.value())
    
    def pointLayerChange(self):
        self.dlg.PointAttribut.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.PointAttribut_2.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.PointAttribut_3.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.attributFromPoint.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.attributToPoint.setLayer(self.dlg.selectPoints.currentLayer())

    def lineLayerChange(self):
        self.dlg.LineAttribut.setLayer(self.dlg.selectLines.currentLayer())
        self.dlg.LineAttribut_2.setLayer(self.dlg.selectLines.currentLayer())
        self.dlg.LineAttribut_3.setLayer(self.dlg.selectLines.currentLayer())
     
    def add1Clicked(self):
        if self.dlg.add_1.text() == '+':
            self.dlg.LineAttribut_2.setEditable(True)
            self.dlg.PointAttribut_2.setEditable(True)
            self.dlg.LineAttribut_2.setHidden(False)
            self.dlg.PointAttribut_2.setHidden(False)
            self.dlg.add_1.setText('-')
            self.dlg.same_2.setHidden(False)
            self.dlg.add_2.setHidden(False)
        elif self.dlg.add_1.text() == '-':
            self.dlg.LineAttribut_2.setEditable(False)
            self.dlg.PointAttribut_2.setEditable(False)
            self.dlg.LineAttribut_2.setHidden(True)
            self.dlg.PointAttribut_2.setHidden(True)
            self.dlg.add_1.setText('+')
            self.dlg.same_2.setHidden(True)
            self.dlg.add_2.setHidden(True)
     
    def add2Clicked(self):
        if self.dlg.add_2.text() == '+':
            self.dlg.LineAttribut_3.setEditable(True)
            self.dlg.PointAttribut_3.setEditable(True)
            self.dlg.LineAttribut_3.setHidden(False)
            self.dlg.PointAttribut_3.setHidden(False)
            self.dlg.add_2.setText('-')
            self.dlg.same_3.setHidden(False)
        elif self.dlg.add_2.text() == '-':
            self.dlg.LineAttribut_3.setEditable(False)
            self.dlg.PointAttribut_3.setEditable(False)
            self.dlg.LineAttribut_3.setHidden(True)
            self.dlg.PointAttribut_3.setHidden(True)
            self.dlg.add_2.setText('+')
            self.dlg.same_3.setHidden(True)
        
    
    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SplitLinesDialog()
        
        self.dlg.selectLines.setShowCrs(True)
        self.dlg.selectLines.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.dlg.selectPoints.setShowCrs(True)
        self.dlg.selectPoints.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.dlg.LineAttribut_2.setEditable(False)
        self.dlg.PointAttribut_2.setEditable(False)
        self.dlg.LineAttribut_3.setEditable(False)
        self.dlg.PointAttribut_3.setEditable(False)
        self.dlg.same_2.setHidden(True)
        self.dlg.same_3.setHidden(True)
        self.dlg.add_2.setHidden(True)
        self.dlg.LineAttribut_2.setHidden(True)
        self.dlg.PointAttribut_2.setHidden(True)
        self.dlg.LineAttribut_3.setHidden(True)
        self.dlg.PointAttribut_3.setHidden(True)
        
        self.dlg.PointAttribut.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.LineAttribut.setLayer(self.dlg.selectLines.currentLayer())
        self.dlg.PointAttribut_2.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.LineAttribut_2.setLayer(self.dlg.selectLines.currentLayer())
        self.dlg.PointAttribut_3.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.LineAttribut_3.setLayer(self.dlg.selectLines.currentLayer())
        self.dlg.attributFromPoint.setLayer(self.dlg.selectPoints.currentLayer())
        self.dlg.attributToPoint.setLayer(self.dlg.selectPoints.currentLayer())
        
        self.dlg.selectPoints.layerChanged.connect(self.pointLayerChange)
        self.dlg.selectLines.layerChanged.connect(self.lineLayerChange)
        self.dlg.DistanceSelect.valueChanged.connect(self.sliderChange) 
        
        self.dlg.add_1.clicked.connect(self.add1Clicked)
        self.dlg.add_2.clicked.connect(self.add2Clicked)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            ### remove old layers
            QgsProject.instance().removeMapLayer(QgsProject.instance().mapLayersByName('straightLines')[0].id())
            QgsProject.instance().removeMapLayer(QgsProject.instance().mapLayersByName('singleLines')[0].id())
            QgsProject.instance().removeMapLayer(QgsProject.instance().mapLayersByName('tempBuffer')[0].id())
            QgsProject.instance().removeMapLayer(QgsProject.instance().mapLayersByName('nearestPoint')[0].id())
            ### layer for pointbuffer
            vl = QgsVectorLayer("polygon?crs=epsg:25832", "tempBuffer", "memory")
            pr = vl.dataProvider()
            ### layer for nearestPoint
            vlN = QgsVectorLayer("point?crs=epsg:25832", "nearestPoint", "memory")
            prN = vlN.dataProvider()
            ### linelayer (multi)
            outLayer = self.dlg.selectLines.currentLayer()
            ### layer for lines (multi to single)
            fn2 = self.plugin_dir + "/data/singleLines.shp"
            layer2 = QgsVectorLayer("linestring?crs=epsg:25832", "singleLines", "memory")
            layer2PR = layer2.dataProvider()
            layer2PR.addAttributes(outLayer.fields())
            layer2.updateFields()

            ### vorher vielleicht noch mergen??? damit zusammenhängende linien mit gleichen attributen auch nur 1 linie ist

            ### mulitLine to singleLine(new layer)
            for feat2 in outLayer.getFeatures():
                geom = feat2.geometry()
                if QgsWkbTypes.isSingleType(geom.wkbType()):
                    # single
                    points = []
                    f = QgsFeature()
                    for pnt in geom.asPolyline():
                        points.append(QgsPoint(pnt.x(),pnt.y()))
                    f.setGeometry(QgsGeometry.fromPolyline(points))
                    f.setAttributes(feat2.attributes())
                    layer2PR.addFeature(f)
                else:
                    # multipart
                    for part in geom.asMultiPolyline():
                        points = []
                        f = QgsFeature()
                        for pnt in part:
                            points.append(QgsPoint(pnt.x(),pnt.y()))
                        f.setGeometry(QgsGeometry.fromPolyline(points))
                        f.setAttributes(feat2.attributes())
                        layer2PR.addFeature(f)
            QgsProject.instance().addMapLayer(layer2)

            ### new layer for Straight lines (curved to straight)
            fn3 = self.plugin_dir + "/data/straightLines.shp"
            layer3 = QgsVectorLayer("linestring?crs=epsg:25832", "straightLines", "memory")
            layer3PR = layer3.dataProvider()
            layer3PR.addAttributes(layer2.fields())
            layer3.updateFields()
            for feat3 in layer2.getFeatures():
                geom3 = feat3.geometry()
                f = QgsFeature()
                points = []
                for pnt in geom3.asPolyline():
                    if points != []:
                        points.append(QgsPoint(pnt.x(),pnt.y()))
                        f.setGeometry(QgsGeometry.fromPolyline(points))
                        f.setAttributes(feat3.attributes())
                        layer3PR.addFeature(f)
                        points = []
                    points.append(QgsPoint(pnt.x(),pnt.y()))
            QgsProject.instance().addMapLayer(layer3)
            
            ### loop through all points
            for feat in self.dlg.selectPoints.currentLayer().getFeatures():
            
                ### select all lines with same attributs as point in given fields (PointAttribut, LineAttribut)
                exp = self.dlg.LineAttribut.currentField()+" = '"+feat[self.dlg.PointAttribut.currentField()]+"'"
                if self.dlg.add_1.text() == '-':
                    exp = exp + " AND " + self.dlg.LineAttribut_2.currentField()+" = '"+feat[self.dlg.PointAttribut_2.currentField()]+"'"
                if self.dlg.add_2.text() == '-':
                    exp = exp + " AND " + self.dlg.LineAttribut_3.currentField()+" = '"+feat[self.dlg.PointAttribut_3.currentField()]+"'"
                print(exp)
                layer2.selectByExpression(exp)
                layer3.selectByExpression(exp)
                #self.dlg.selectPoints.currentLayer().selectByExpression(self.dlg.PointAttribut.currentField()+'='+feat[self.dlg.PointAttribut.currentField()])
                print("Anzahl selektierte Linien von Layer 2 nach Location", int(layer2.selectedFeatureCount()))
                print("Anzahl selektierte Linien nach Attribut", int(layer3.selectedFeatureCount()))                 
                 
                ### create buffer around actual point with given distance(DistanceSelect)
                print("distance: ", self.dlg.DistanceSelect.value())
                buffer = feat.geometry().buffer(self.dlg.DistanceSelect.value(),10)
                poly = buffer.asPolygon()
                outGeom = QgsFeature()
                outGeom.setGeometry(QgsGeometry.fromPolygonXY(poly))
                pr.addFeature(outGeom)
                vl.updateExtents() 
                QgsProject.instance().addMapLayer(vl)
                
                ### subselect lines intersecting the buffer
                parameters = { 'INPUT' : layer3, 'INTERSECT' : vl, 'METHOD' : 2, 'PREDICATE' : [0] }
                processing.run('qgis:selectbylocation', parameters )
                print("Anzahl selektierte Linien nach Location", int(layer3.selectedFeatureCount()))
                if (int(layer3.selectedFeatureCount()) > 1):
                  raise Exception('The distance is too big')
                
                ### get nearest point on line from actual point
                ## Inputs
                #line = Line(0.0, 0.0, 100.0, 0.0)
                print(layer3.selectedFeatures()[0].geometry().asPolyline())
                line = layer3.selectedFeatures()[0].geometry().asPolyline()
                #point = Point(50.0, 1500)
                print(feat.geometry().asPoint())
                point = feat.geometry().asPoint()
                ## Calculate Length of line
                len = math.sqrt((line[0].x() - line[1].x())*(line[0].x() - line[1].x()) + (line[0].y() - line[1].y())*(line[0].y() - line[1].y()))
                if (len == 0):
                  raise Exception('The points on input line must not be identical')

                u = ((point.x() - line[1].x()) * (line[0].x() - line[1].x()) + (point.y() - line[1].y()) * (line[0].y() - line[1].y())) / (len*len)

                # restrict to line boundary
                if u > 1:
                  u = 1
                elif u < 0:
                  u = 0

                nearestPointOnLine = QgsPointXY(line[1].x() + u * (line[0].x() - line[1].x()), line[1].y() + u * (line[0].y() - line[1].y()))
                print('Nearest point "N" on line: ({}, {})'.format(nearestPointOnLine.x(), nearestPointOnLine.y()))
                fN = QgsFeature()
                fN.setGeometry(QgsGeometry.fromPointXY(nearestPointOnLine))
                prN.addFeature(fN)
                QgsProject.instance().addMapLayer(vlN)
                
                ### subselect lines intersecting the point
                parameters = { 'INPUT' : layer2, 'INTERSECT' : vlN, 'METHOD' : 2, 'PREDICATE' : [0] }
                processing.run('qgis:selectbylocation', parameters )
                print("Anzahl selektierte Linien von Layer 2 nach Location", int(layer2.selectedFeatureCount()))
                
                ###   splitte selektierte linie an punkt
                #splitPt = nearestPointOnLine
                #splitLine = layer2.selectedFeatures()[0].geometry()
                #splitResult = split(splitLine, splitPt)
                #splitResult.wkt
                
                #   if attribut nicht null ...
                #   gib Linie mit ID: 1 attribut bis Punkt
                #   gib Linie mit ID: 2 attribut vom Punkt
                
            pass
