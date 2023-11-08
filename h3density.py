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
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant, QUrl
from qgis.core import Qgis, QgsWkbTypes, QgsFields, QgsField, QgsCoordinateTransform, QgsCoordinateReferenceSystem,  QgsFeature, QgsGeometry, QgsPointXY, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSink
    )
import processing

class H3DensityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource('INPUT', 'Input point vector layer', [QgsProcessing.TypeVectorPoint])
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
            QgsProcessingParameterField(
                'WEIGHT',
                'Weight field',
                parentLayerParameterName='INPUT',
                type=QgsProcessingParameterField.Numeric,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output H3 density map',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        try:
            import h3.api.basic_int as h3
        except Exception:
            from .utils import h3InstallString
            feedback.reportError(h3InstallString)
            return {}
        source = self.parameterAsSource(parameters, 'INPUT', context)
        resolution = self.parameterAsInt(parameters, 'RESOLUTION', context)
        if 'WEIGHT' in parameters and parameters['WEIGHT']:
            use_weight = True
            weight_field = self.parameterAsString(parameters, 'WEIGHT', context)
        else:
            use_weight = False
        
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        fields = QgsFields()
        fields.append(QgsField('ID', QVariant.Int))
        fields.append(QgsField('H3HASH', QVariant.String))
        fields.append(QgsField('NUMPOINTS', QVariant.Double))
        (sink, dest_id) = self.parameterAsSink(
            parameters, 'OUTPUT',
            context, fields, QgsWkbTypes.Polygon, epsg4326)
        src_crs = source.sourceCrs()
        
        if src_crs != epsg4326:
            transform = QgsCoordinateTransform(src_crs, epsg4326, QgsProject.instance())

        total = 85.0 / source.featureCount() if source.featureCount() else 0
        ghash = {}

        iterator = source.getFeatures()
        if use_weight:
            for cnt, feature in enumerate(iterator):
                if feedback.isCanceled():
                    break
                try:
                    pt = feature.geometry().asPoint()
                    if src_crs != epsg4326:
                        pt = transform.transform(pt)
                    h = h3.geo_to_h3(pt.y(), pt.x(), resolution)
                    if h == 0: # Check to see if the input coordinates were invalid
                        continue
                    weight = feature[weight_field]
                    if h in ghash:
                        ghash[h] += weight
                    else:
                        ghash[h] = weight
                except Exception:
                    pass
                if cnt % 1000 == 0:
                    feedback.setProgress(int(cnt * total))
        else:
            for cnt, feature in enumerate(iterator):
                if feedback.isCanceled():
                    break
                try:
                    pt = feature.geometry().asPoint()
                    if src_crs != epsg4326:
                        pt = transform.transform(pt)
                    h = h3.geo_to_h3(pt.y(), pt.x(), resolution)
                    if h == 0: # Check to see if the input coordinates were invalid
                        continue
                    if h in ghash:
                        ghash[h] += 1
                    else:
                        ghash[h] = 1
                except Exception:
                    pass
                if cnt % 1000 == 0:
                    feedback.setProgress(int(cnt * total))

        if len(ghash) == 0:
            return {}
        total = 15 / len(ghash)
        for cnt, key in enumerate(ghash.keys()):
            val = ghash[key]
            try:
                coords = h3.h3_to_geo_boundary(key)
            except:
                continue
            pts = []
            for p in coords:
                pt = QgsPointXY(p[1], p[0])
                pts.append(pt)
            # pts.append(pts[0])
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolygonXY([pts]))
            f.setAttributes([cnt, h3.h3_to_string(key), val])
            sink.addFeature(f)
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total)+85)
        return {'OUTPUT': dest_id}

    def group(self):
        return 'H3 density'

    def groupId(self):
        return 'h3density'

    def name(self):
        return 'h3density'

    def displayName(self):
        return 'H3 density grid'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/h3density.svg'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return H3DensityAlgorithm()
