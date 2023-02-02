import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from qgis.core import Qgis, QgsWkbTypes, QgsFields, QgsField, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsRectangle, QgsFeature, QgsGeometry, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFeatureSink
    )
import processing

from . import geohash

class GeohashDensityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource('INPUT', 'Input point vector layer', [QgsProcessing.TypeVectorPoint])
        )
        param = QgsProcessingParameterNumber('RESOLUTION', 'Geohash resolution',
                type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=6, maxValue=12, optional=False)
        if Qgis.QGIS_VERSION_INT >= 31600:
            param.setHelp(
                '''
                The resolution level of the grid, as defined in the geohash standard.
                <br>
                <table>
                  <tr>
                    <th>Resolution<br>Level</th>
                    <th>Approximate<br>Dimensions</th>
                  </tr>
                  <tr>
                    <td style="text-align: center">1</td>
                    <td style="text-align: center">≤ 5,000km X 5,000km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">2</td>
                    <td style="text-align: center">≤ 1,250km X 625km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">3</td>
                    <td style="text-align: center">≤ 156km X 156km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">4</td>
                    <td style="text-align: center">≤ 39.1km X 19.5km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">5</td>
                    <td style="text-align: center">≤ 4.89km X 4.89km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">6</td>
                    <td style="text-align: center">≤ 1.22km X 0.61km</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">7</td>
                    <td style="text-align: center">≤ 153m X 153m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">8</td>
                    <td style="text-align: center">≤ 38.2m X 19.1m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">9</td>
                    <td style="text-align: center">≤ 4.77m X 4.77m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">10</td>
                    <td style="text-align: center">≤ 1.19m X 0.596m</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">11</td>
                    <td style="text-align: center">≤ 149mm X 149mm</td>
                  </tr>
                  <tr>
                    <td style="text-align: center">12</td>
                    <td style="text-align: center">≤ 37.2mm X 18.6mm</td>
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
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output geohash density map',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
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
        fields.append(QgsField('GEOHASH', QVariant.String))
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
                    h = geohash.encode(pt.y(), pt.x(), resolution)
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
                    h = geohash.encode(pt.y(), pt.x(), resolution)
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
            lat1, lat2, lon1, lon2 = geohash.decode_extent(key)
            rect = QgsRectangle(lon1, lat1, lon2, lat2)
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromRect(rect))
            f.setAttributes([cnt, key, val])
            sink.addFeature(f)
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total)+85)
        return {'OUTPUT': dest_id}

    def group(self):
        return 'Geohash density'

    def groupId(self):
        return 'geohashdensity'

    def name(self):
        return 'geohashdensity'

    def displayName(self):
        return 'Geohash density grid'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/geohashdensity.svg'))

    def createInstance(self):
        return GeohashDensityAlgorithm()
