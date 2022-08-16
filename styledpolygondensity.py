import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis, QgsStyle, QgsUnitTypes, QgsCoordinateTransform, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingException,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterRasterDestination
    )
import processing
from .settings import settings

DISTANCE_LABELS = ["Dimensions in pixels", "Kilometers", "Meters", "Miles", 'Yards', "Feet", "Nautical Miles", "Degrees"]

class StyledPolygonRasterDensityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer('INPUT', 'Input polygon vector layer',
            [QgsProcessing.TypeVectorPolygon])
        )
        self.addParameter(
            QgsProcessingParameterExtent('EXTENT', 'Grid extent', optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber('GRID_CELL_WIDTH', 'Grid cell width or image width in pixels',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber('GRID_CELL_HEIGHT', 'Grid cell height or image height in pixels',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum('UNITS', 'Grid measurement unit',
                options=DISTANCE_LABELS, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber('MAX_IMAGE_DIMENSION', 'Maximum width or height dimensions for output image',
                type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=20000, optional=False)
        )
        style = QgsStyle.defaultStyle()
        self.ramp_names = style.colorRampNames()
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name_param = QgsProcessingParameterString('RAMP_NAMES', 'Color ramp name', defaultValue=settings.defaultColorRamp(),
                optional=False)
            ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': settings.ramp_names } } )
        else:
            ramp_name_param = QgsProcessingParameterEnum(
                'RAMP_NAMES',
                'Color ramp name',
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
        self.addParameter(
            QgsProcessingParameterEnum(
                'INTERPOLATION',
                'Interpolation',
                options=['Discrete','Linear','Exact'],
                defaultValue=1,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'MODE',
                'Mode',
                options=['Continuous','Equal Interval','Quantile'],
                defaultValue=2,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                'CLASSES',
                'Number of classes',
                QgsProcessingParameterNumber.Integer,
                defaultValue=15,
                minValue=2,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination('OUTPUT', 'Output polygon density heatmap',
                createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsLayer(parameters, 'INPUT', context)
        extent = self.parameterAsExtent(parameters, 'EXTENT', context)
        extent_crs = self.parameterAsExtentCrs(parameters, 'EXTENT', context)
        cell_width = self.parameterAsDouble(parameters, 'GRID_CELL_WIDTH', context)
        cell_height = self.parameterAsDouble(parameters, 'GRID_CELL_HEIGHT', context)
        selected_units = self.parameterAsInt(parameters, 'UNITS', context)
        max_dimension = self.parameterAsInt(parameters, 'MAX_IMAGE_DIMENSION', context)
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name = self.parameterAsString(parameters, 'RAMP_NAMES', context)
        else:
            ramp_name = self.parameterAsEnum(parameters, 'RAMP_NAMES', context)
        invert = self.parameterAsBool(parameters, 'INVERT', context)
        interp = self.parameterAsInt(parameters, 'INTERPOLATION', context)
        mode = self.parameterAsInt(parameters, 'MODE', context)
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)

        results = {}
        outputs = {}

        # Polygon raster density map
        alg_params = {
            'EXTENT': parameters['EXTENT'],
            'GRID_CELL_HEIGHT': cell_height,
            'GRID_CELL_WIDTH': cell_width,
            'INPUT': parameters['INPUT'],
            'MAX_IMAGE_DIMENSION': max_dimension,
            'UNITS': selected_units,
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['PolygonDensity'] = processing.run('densityanalysis:polygondensity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Output'] = outputs['PolygonDensity']['OUTPUT']

        if feedback.isCanceled():
            return {}

        # Apply pseudocolor raster style
        alg_params = {
            'CLASSES': num_classes,
            'INPUT': outputs['PolygonDensity']['OUTPUT'],
            'INTERPOLATION': interp,
            'MODE': mode,
            'INVERT': invert,
            'RAMP_NAMES': ramp_name
        }
        outputs['PseudocolorStyle'] = processing.run('densityanalysis:rasterstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        return results

    def name(self):
        return 'styledpolygondensity'

    def displayName(self):
        return 'Styled polygon density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/styledrasterdensity.png'))

    def createInstance(self):
        return StyledPolygonRasterDensityAlgorithm()

