import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsStyle

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink
    )
import processing

class H3DensityMapAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource('INPUT', 'Input point vector layer', [QgsProcessing.TypeVectorPoint])
        )
        param = QgsProcessingParameterNumber('RESOLUTION', 'H3 Resolution',
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
                'CLASSES',
                'Number of gradient colors',
                QgsProcessingParameterNumber.Integer,
                defaultValue=15,
                minValue=2,
                optional=False)
        )
        style = QgsStyle.defaultStyle()
        ramp_names = style.colorRampNames()
        ramp_name_param = QgsProcessingParameterString('RAMP_NAMES', 'Select a color ramp', defaultValue='Reds')
        ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': ramp_names } } )
        self.addParameter(ramp_name_param)
        self.addParameter(
            QgsProcessingParameterEnum(
                'COLOR_RAMP_MODE',
                'Color ramp mode',
                options=['Equal Count (Quantile)','Equal Interval','Logrithmic scale','Natural Breaks (Jenks)','Pretty Breaks','Standard Deviation'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                'NO_OUTLINE',
                'No feature outlines',
                True,
                optional=False)
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
        resolution = self.parameterAsInt(parameters, 'RESOLUTION', context)
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)
        ramp_name = self.parameterAsString(parameters, 'RAMP_NAMES', context)
        ramp_mode = self.parameterAsInt(parameters, 'COLOR_RAMP_MODE', context)
        no_outline = self.parameterAsBool(parameters, 'NO_OUTLINE', context)
        
        results = {}
        outputs = {}
        
        alg_params = {
            'INPUT':  parameters['INPUT'],
            'RESOLUTION': resolution,
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['CreateGrid'] = processing.run('densityanalysis:h3density', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['CreateGrid']['OUTPUT']

        if feedback.isCanceled():
            return {}

        # Apply a graduated style
        alg_params = {
            'NO_OUTLINE': no_outline,
            'CLASSES': num_classes,
            'GROUP_FIELD': 'NUMPOINTS',
            'INPUT': outputs['CreateGrid']['OUTPUT'],
            'MODE': ramp_mode,
            'RAMP_NAMES': ramp_name
        }
        processing.run('densityanalysis:gratuatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'h3densitymap'

    def displayName(self):
        return 'Create styled H3 density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/h3.png'))

    def createInstance(self):
        return H3DensityMapAlgorithm()
