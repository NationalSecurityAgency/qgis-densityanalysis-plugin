import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import Qgis, QgsStyle, QgsUnitTypes, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterDestination
    )
import processing

DISTANCE_LABELS = ["Kilometers", "Meters", "Miles", 'Yards', "Feet", "Nautical Miles", "Degrees"]

def conversionToCrsUnits(selected_unit, crs_unit, value):
    if selected_unit == 0:  # Kilometers
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceKilometers, crs_unit)
    elif selected_unit == 1:  # Meters
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, crs_unit)
    elif selected_unit == 2:  # Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMiles, crs_unit)
    elif selected_unit == 3:  # Yards
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceYards, crs_unit)
    elif selected_unit == 4:  # Feet
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceFeet, crs_unit)
    elif selected_unit == 5:  # Nautical Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceNauticalMiles, crs_unit)
    elif selected_unit == 6:  # Degrees
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceDegrees, crs_unit)
    return(measureFactor * value)

def conversionFromCrsUnits(selected_unit, crs_unit, value):
    if selected_unit == 0:  # Kilometers
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceKilometers)
    elif selected_unit == 1:  # Meters
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceMeters)
    elif selected_unit == 2:  # Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceMiles)
    elif selected_unit == 3:  # Yards
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceYards)
    elif selected_unit == 4:  # Feet
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceFeet)
    elif selected_unit == 5:  # Nautical Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceNauticalMiles)
    elif selected_unit == 6:  # Degrees
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceDegrees)
    return(measureFactor * value)

class StyledKdeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer('INPUT', 'Input point layer',
            [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterNumber('KERNEL_RADIUS', 'Kernel radius',
                type=QgsProcessingParameterNumber.Double, minValue=0, defaultValue=2, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber('PIXEL_SIZE', 'Pixel grid size',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum('UNITS', 'Measurement unit of kernel radius and pixel grid size',
                options=DISTANCE_LABELS, defaultValue=0, optional=False)
        )
        param = QgsProcessingParameterNumber('MAX_IMAGE_DIMENSION', 'Maximum width or height dimensions of output image',
            type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=20000, optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterEnum('KERNEL', 'Kernel shape',
            options=['Quartic', 'Triangular', 'Uniform', 'Triweight', 'Epanechnikov'], defaultValue=0, optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber('DECAY', 'Decay ratio (Triangular kernels only)',
            type=QgsProcessingParameterNumber.Double, defaultValue=0, minValue=-100, maxValue=100, optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterEnum('OUTPUT_VALUE', 'Output value scaling',
            options=['Raw','Scaled'], defaultValue=0, optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

        style = QgsStyle.defaultStyle()
        self.ramp_names = style.colorRampNames()
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name_param = QgsProcessingParameterString('RAMP_NAMES', 'Color ramp name', defaultValue='Reds',
                optional=False)
            ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': self.ramp_names } } )
        else:
            try:
                index = self.ramp_names.index('Reds')
            except Exception:
                index = 0
            ramp_name_param = QgsProcessingParameterEnum(
                'RAMP_NAMES',
                'Color ramp name',
                options=self.ramp_names,
                defaultValue=index,
                optional=False)
        self.addParameter(ramp_name_param)
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
            QgsProcessingParameterRasterDestination('OUTPUT', 'Output kernel density heatmap',
                createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsLayer(parameters, 'INPUT', context)
        radius = self.parameterAsDouble(parameters, 'KERNEL_RADIUS', context)
        pixel_size = self.parameterAsDouble(parameters, 'PIXEL_SIZE', context)
        units = self.parameterAsEnum(parameters, 'UNITS', context)
        max_dimension = self.parameterAsInt(parameters, 'MAX_IMAGE_DIMENSION', context)
        kernel_shape = self.parameterAsEnum(parameters, 'KERNEL', context)
        decay = self.parameterAsDouble(parameters, 'DECAY', context)
        output_value = self.parameterAsEnum(parameters, 'OUTPUT_VALUE', context)
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name = self.parameterAsString(parameters, 'RAMP_NAMES', context)
        else:
            ramp_name = self.ramp_names[self.parameterAsEnum(parameters, 'RAMP_NAMES', context)]
        interp = self.parameterAsInt(parameters, 'INTERPOLATION', context)
        mode = self.parameterAsInt(parameters, 'MODE', context)
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)

        layer_crs = layer.sourceCrs()
        extent = layer.sourceExtent()
        
        layer_units = layer_crs.mapUnits()
        radius = conversionToCrsUnits(units, layer_units, radius)
            
        # Determine the width and height in extent units
        pixel_size_extent = conversionToCrsUnits(units, layer_units, pixel_size)
        # Add one additional cell, half on each side to better encapsulate the data
        width = int(extent.width() / pixel_size_extent)
        height = int(extent.height() / pixel_size_extent)
        if width > max_dimension or height > max_dimension:
            feedback.reportError('The grid pixel size exceeds the maximum output image dimensions as follows:')
            feedback.reportError('Output image width: {}'.format(width))
            feedback.reportError('Output image height: {}'.format(height))
            max_size = max(extent.width(), extent.height()) / max_dimension
            feedback.reportError('Use grid pixel size greater than: {}'.format(
                conversionFromCrsUnits(units, layer_units, max_size)))
            feedback.reportError('or increase the maximum grid width and height.')
            raise QgsProcessingException()
        if width == 0 or height == 0:
            raise QgsProcessingException('Cell dimensions are too large and return an image dimenson of 0.')
                
        feedback.pushInfo('Output image width: {}'.format(width))
        feedback.pushInfo('Output image height: {}'.format(height))
        
        results = {}
        outputs = {}

        unit_str = QgsUnitTypes.encodeUnit(layer_units)
        feedback.pushInfo('Grid pixel size: {} {}'.format(pixel_size_extent, unit_str))
        feedback.pushInfo('Kernel radius size: {} {}'.format(radius, unit_str))
        # Heatmap (Kernel Density Estimation)
        alg_params = {
            'DECAY': decay,
            'INPUT': parameters['INPUT'],
            'KERNEL': kernel_shape,
            'OUTPUT_VALUE': output_value,
            'PIXEL_SIZE': pixel_size_extent,
            'RADIUS': radius,
            'RADIUS_FIELD': '',
            'WEIGHT_FIELD': '',
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['HeatmapKDE'] = processing.run('qgis:heatmapkerneldensityestimation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Heatmap'] = outputs['HeatmapKDE']['OUTPUT']

        if feedback.isCanceled():
            return {}

        # Apply pseudocolor raster style
        alg_params = {
            'CLASSES': num_classes,
            'INPUT': outputs['HeatmapKDE']['OUTPUT'],
            'INTERPOLATION': interp,
            'MODE': mode,
            'RAMP_NAMES': ramp_name
        }
        outputs['Styled'] = processing.run('densityanalysis:rasterstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'styledkde'

    def displayName(self):
        return 'Styled heatmap (Kernel density estimation)'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/kde.png'))

    def createInstance(self):
        return StyledKdeAlgorithm()

