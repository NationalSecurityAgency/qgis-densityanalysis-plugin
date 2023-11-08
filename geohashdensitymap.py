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
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterField,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFeatureSink
    )
import processing

from . import geohash
from .settings import settings, COLOR_RAMP_MODE

class GeohashDensityMapAlgorithm(QgsProcessingAlgorithm):

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
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name_param = QgsProcessingParameterString('RAMP_NAMES', 'Select color ramp', defaultValue=settings.defaultColorRamp())
            ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': settings.ramp_names } } )
        else:
            ramp_name_param = QgsProcessingParameterEnum(
                'RAMP_NAMES',
                'Select color ramp',
                options=settings.ramp_names,
                defaultValue=settings.defaultColorRampIndex(),
                optional=False)
        self.addParameter(ramp_name_param)
        self.addParameter(
            QgsProcessingParameterBoolean(
                'INVERT',
                'Invert color ramp',
                False,
                optional=False)
        )

        param = QgsProcessingParameterField(
            'WEIGHT',
            'Weight field',
            parentLayerParameterName='INPUT',
            type=QgsProcessingParameterField.Numeric,
            optional=True)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber(
            'CLASSES',
            'Number of gradient colors',
            QgsProcessingParameterNumber.Integer,
            defaultValue=settings.num_ramp_classes,
            minValue=2,
            optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterEnum(
            'COLOR_RAMP_MODE',
            'Color ramp mode',
            options=COLOR_RAMP_MODE,
            defaultValue=settings.color_ramp_mode,
            optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterBoolean(
            'NO_OUTLINE',
            'No feature outlines',
            True,
            optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        self.addParameter(
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output geohash density map',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        resolution = self.parameterAsInt(parameters, 'RESOLUTION', context)
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)
        if 'WEIGHT' in parameters and parameters['WEIGHT']:
            use_weight = True
            weight_field = self.parameterAsString(parameters, 'WEIGHT', context)
        else:
            use_weight = False
        if Qgis.QGIS_VERSION_INT >= 32200:
            # In this case ramp_name will be the name
            ramp_name = self.parameterAsString(parameters, 'RAMP_NAMES', context)
        else:
            # In this case ramp_name will be an index into ramp_names
            ramp_name = self.parameterAsEnum(parameters, 'RAMP_NAMES', context)
        ramp_mode = self.parameterAsInt(parameters, 'COLOR_RAMP_MODE', context)
        no_outline = self.parameterAsBool(parameters, 'NO_OUTLINE', context)
        invert = self.parameterAsBool(parameters, 'INVERT', context)
        
        results = {}
        outputs = {}

        alg_params = {
            'INPUT':  parameters['INPUT'],
            'RESOLUTION': resolution,
            'OUTPUT': parameters['OUTPUT']
        }
        if use_weight:
            alg_params['WEIGHT'] = weight_field
        outputs['CreateGrid'] = processing.run('densityanalysis:geohashdensity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['CreateGrid']['OUTPUT']

        # Apply a graduated style
        alg_params = {
            'NO_OUTLINE': no_outline,
            'INVERT': invert,
            'CLASSES': num_classes,
            'GROUP_FIELD': 'NUMPOINTS',
            'INPUT': outputs['CreateGrid']['OUTPUT'],
            'MODE': ramp_mode,
            'RAMP_NAMES': ramp_name
        }
        processing.run('densityanalysis:graduatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=False)
        return results

    def group(self):
        return 'Geohash density'

    def groupId(self):
        return 'geohashdensity'

    def name(self):
        return 'geohashdensitymap'

    def displayName(self):
        return 'Styled geohash density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/geohash.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return GeohashDensityMapAlgorithm()
