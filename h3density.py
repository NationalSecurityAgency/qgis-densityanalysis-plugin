import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsWkbTypes, QgsStyle, QgsUnitTypes, QgsFields, QgsField, QgsCoordinateTransform, QgsCoordinateReferenceSystem, QgsRectangle, QgsFeature, QgsGeometry, QgsPointXY

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink
    )
import processing

import h3

class H3DensityAlgorithm(QgsProcessingAlgorithm):
    PrmInput = 'INPUT'
    PrmH3Resolution = 'RESOLUTION'
    PrmClasses = 'CLASSES'
    PrmRampNames = 'RAMPNAMES'
    PrmColorRampMode = 'COLORRAMPMODE'
    PrmOutput = 'OUTPUT'
    PrmNoOutline = 'NOOUTLINE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(self.PrmInput, 'Input point vector layer', defaultValue=None,
            types=[QgsProcessing.TypeVectorPoint])
        )
        param = QgsProcessingParameterNumber(self.PrmH3Resolution, 'H3 Resolution',
                type=QgsProcessingParameterNumber.Integer, minValue=0, defaultValue=9, maxValue=15, optional=False)
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
            QgsProcessingParameterNumber(
                self.PrmClasses,
                'Number of gradient colors',
                QgsProcessingParameterNumber.Integer,
                defaultValue=10,
                minValue=2,
                optional=False)
        )
        style = QgsStyle.defaultStyle()
        ramp_names = style.colorRampNames()
        ramp_name_param = QgsProcessingParameterString(self.PrmRampNames, 'Select a color ramp', defaultValue='Reds')
        ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': ramp_names } } )
        self.addParameter(ramp_name_param)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmColorRampMode,
                'Color ramp mode',
                options=['Equal Count (Quantile)','Equal Interval','Logrithmic scale','Natural Breaks (Jenks)','Pretty Breaks','Standard Deviation'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmNoOutline,
                'No feature outlines',
                True,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(self.PrmOutput, 'Output H3 density map',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        source = self.parameterAsSource(parameters, self.PrmInput, context)
        num_classes = self.parameterAsInt(parameters, self.PrmClasses, context)
        resolution = self.parameterAsInt(parameters, self.PrmH3Resolution, context)
        ramp_name = self.parameterAsString(parameters, self.PrmRampNames, context)
        ramp_mode = self.parameterAsInt(parameters, self.PrmColorRampMode, context)
        no_outline = self.parameterAsBool(parameters, self.PrmNoOutline, context)
        
        epsg4326 = QgsCoordinateReferenceSystem("EPSG:4326")
        fields = QgsFields()
        fields.append(QgsField('ID', QVariant.Int))
        fields.append(QgsField('H3HASH', QVariant.String))
        fields.append(QgsField('NUMPOINTS', QVariant.Int))
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.PrmOutput,
            context, fields, QgsWkbTypes.Polygon, epsg4326)
        src_crs = source.sourceCrs()
        
        if src_crs != epsg4326:
            transform = QgsCoordinateTransform(src_crs, epsg4326, QgsProject.instance())

        total = 85.0 / source.featureCount() if source.featureCount() else 0
        ghash = {}

        iterator = source.getFeatures()
        for cnt, feature in enumerate(iterator):
            if feedback.isCanceled():
                break
            try:
                pt = feature.geometry().asPoint()
                if src_crs != epsg4326:
                    pt = transform.transform(pt)
                h = h3.geo_to_h3(pt.y(), pt.x(), resolution)
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
            coords = h3.h3_to_geo_boundary(key)
            pts = []
            for p in coords:
                pt = QgsPointXY(p[1], p[0])
                pts.append(pt)
            # pts.append(pts[0])
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolygonXY([pts]))
            f.setAttributes([cnt, key, val])
            sink.addFeature(f)
            if cnt % 100 == 0:
                feedback.setProgress(int(cnt * total)+85)

        # Apply a graduated style
        alg_params = {
            'NoOutline': no_outline,
            'classes': num_classes,
            'groupfield': 'NUMPOINTS',
            'maplayer': dest_id,
            'mode': ramp_mode,
            'rampnames': ramp_name
        }
        processing.run('densityanalysis:gratuatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=False)
        return {self.PrmOutput: dest_id}

    def name(self):
        return 'h3density'

    def displayName(self):
        return 'Create H3 density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/h3.png'))

    def createInstance(self):
        return H3DensityAlgorithm()
