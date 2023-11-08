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
from .settings import settings, COLOR_RAMP_MODE

class H3DensityMapAlgorithm(QgsProcessingAlgorithm):
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
        resolution = self.parameterAsInt(parameters, 'RESOLUTION', context)
        if 'WEIGHT' in parameters and parameters['WEIGHT']:
            use_weight = True
            weight_field = self.parameterAsString(parameters, 'WEIGHT', context)
        else:
            use_weight = False
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)
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
        outputs['CreateGrid'] = processing.run('densityanalysis:h3density', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['CreateGrid']['OUTPUT']

        if feedback.isCanceled():
            return {}

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
        processing.run('densityanalysis:graduatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def group(self):
        return 'H3 density'

    def groupId(self):
        return 'h3density'

    def name(self):
        return 'h3densitymap'

    def displayName(self):
        return 'Styled H3 density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/h3.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return H3DensityMapAlgorithm()
