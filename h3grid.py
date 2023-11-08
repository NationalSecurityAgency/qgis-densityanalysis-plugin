"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import json
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.core import Qgis, QgsWkbTypes, QgsFields, QgsField, QgsCoordinateTransform, QgsCoordinateReferenceSystem,  QgsFeature, QgsGeometry, QgsPointXY, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterNumber,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink
    )
import processing

class H3GridAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterExtent('EXTENT', 'Grid extent', optional=False)
        )
        param = QgsProcessingParameterNumber('RESOLUTION', 'H3 Resolution',
                type=QgsProcessingParameterNumber.Integer, minValue=0, defaultValue=9, maxValue=15, optional=False)
        if Qgis.QGIS_VERSION_INT >= 31600:
            param.setHelp(
                '''
                The resolution level of the grid, as defined in the H3 standard.
                <br>
                <table>
                  <tr>
                    <th>Resolution<br>Level</th>
                    <th>Avg. Hexagon<br>Edge Length</th>
                  </tr>
                  <tr>
                    <td style="text-align: center">0</td>
                    <td style="text-align: center">1107.71 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">1</td>
                    <td style="text-align: center">418.68 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">2</td>
                    <td style="text-align: center">158.24 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">3</td>
                    <td style="text-align: center">59.81 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">4</td>
                    <td style="text-align: center">22.61 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">5</td>
                    <td style="text-align: center">8.54 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">6</td>
                    <td style="text-align: center">3.23 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">7</td>
                    <td style="text-align: center">1.22 km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">8</td>
                    <td style="text-align: center">461.35 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">9</td>
                    <td style="text-align: center">174.38 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">10</td>
                    <td style="text-align: center">65.91 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">11</td>
                    <td style="text-align: center">24.91 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">12</td>
                    <td style="text-align: center">9.42 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">13</td>
                    <td style="text-align: center">3.56 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">14</td>
                    <td style="text-align: center">1.35 m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">15</td>
                    <td style="text-align: center">0.51 m</td>
                  </tr>
                </table>
                '''
            )
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output H3 grid',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        try:
            import h3
        except Exception:
            from .utils import h3InstallString
            feedback.reportError(h3InstallString)
            return {}

        extent = self.parameterAsExtent(parameters, 'EXTENT', context)
        if extent.isNull():
            raise QgsProcessingException('Invalid extent')
        extent_crs = self.parameterAsExtentCrs(parameters, 'EXTENT', context)

        resolution = self.parameterAsInt(parameters, 'RESOLUTION', context)
        if resolution < 0 or resolution > 15:
            raise QgsProcessingException('Invalid input resolution')
        
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        fields = QgsFields()
        fields.append(QgsField('ID', QVariant.Int))
        fields.append(QgsField('H3HASH', QVariant.String))
        (sink, dest_id) = self.parameterAsSink(
            parameters, 'OUTPUT',
            context, fields, QgsWkbTypes.Polygon, epsg4326)
        
        if extent_crs != epsg4326:
            # The extent needs to be in EPSG:4326
            transform = QgsCoordinateTransform(extent_crs, epsg4326, QgsProject.instance())
            extent = transform.transform(extent)
        json_str = QgsGeometry.fromRect(extent).asJson()
        js = json.loads(json_str)
        h3_ids = h3.polyfill(js, resolution, geo_json_conformant=True)
        if feedback.isCanceled():
            raise QgsProcessingException('Operation canceled')
        feedback.setProgress(50)
        if len(h3_ids) == 0:
            raise QgsProcessingException("No grid was created. Grid extent may be invalid or resolution and extent may exceeded a practical threshold.")

        total = 50 / len(h3_ids)
        for i, h3str in enumerate(h3_ids):
            coords = h3.h3_to_geo_boundary(h3str)
            geom = QgsGeometry.fromPolygonXY([[QgsPointXY(lon, lat) for lat, lon in coords], ])
            f = QgsFeature()
            f.setGeometry(geom)
            f.setAttributes([i, h3str])
            sink.addFeature(f)
            if i % 100 == 0:
                feedback.setProgress(int(i * total)+50)
            
        return {'OUTPUT': dest_id}

    def group(self):
        return 'H3 density'

    def groupId(self):
        return 'h3density'

    def name(self):
        return 'h3grid'

    def displayName(self):
        return 'H3 grid'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/h3grid.svg'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return H3GridAlgorithm()
