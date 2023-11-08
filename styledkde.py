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
from qgis.core import Qgis, QgsStyle, QgsUnitTypes, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterDestination
    )
import processing
from .settings import settings, UNIT_LABELS, conversionToCrsUnits, conversionFromCrsUnits

class StyledKdeAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer('INPUT', 'Input point layer',
            [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterNumber('PIXEL_SIZE', 'Cell/pixel dimension in measurement units',
                type=QgsProcessingParameterNumber.Double, defaultValue=settings.default_dimension, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber('KERNEL_RADIUS', 'Kernel radius in measurement units',
                type=QgsProcessingParameterNumber.Double, minValue=0, defaultValue=settings.default_dimension * 2, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum('UNITS', 'Measurement unit',
                options=UNIT_LABELS, defaultValue=settings.measurement_unit, optional=False)
        )

        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name_param = QgsProcessingParameterString('RAMP_NAMES', 'Select color ramp', defaultValue=settings.defaultColorRamp(),
                optional=False)
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
        param = QgsProcessingParameterNumber('MAX_IMAGE_DIMENSION', 'Maximum width or height dimensions of output image',
            type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=settings.max_image_size, optional=False)
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
        param = QgsProcessingParameterEnum(
            'INTERPOLATION',
            'Interpolation',
            options=['Discrete','Linear','Exact'],
            defaultValue=1,
            optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterEnum(
            'MODE',
            'Mode',
            options=['Continuous','Equal Interval','Quantile'],
            defaultValue=2,
            optional=False)
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
            ramp_name = self.parameterAsEnum(parameters, 'RAMP_NAMES', context)
        invert = self.parameterAsBool(parameters, 'INVERT', context)
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
            'INVERT': invert,
            'RAMP_NAMES': ramp_name
        }
        outputs['Styled'] = processing.run('densityanalysis:rasterstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def group(self):
        return 'Raster density'

    def groupId(self):
        return 'rasterdensity'

    def name(self):
        return 'styledkde'

    def displayName(self):
        return 'Styled heatmap (Kernel density estimation)'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/kde.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return StyledKdeAlgorithm()

