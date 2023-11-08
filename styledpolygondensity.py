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
from qgis.core import Qgis, QgsStyle

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
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterDestination
    )
import processing
from .settings import settings, POLYGON_UNIT_LABELS

class StyledPolygonRasterDensityAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer('INPUT', 'Input polygon vector layer',
            [QgsProcessing.TypeVectorPolygon])
        )
        self.addParameter(
            QgsProcessingParameterExtent('EXTENT', 'Grid extent (defaults to layer extent)', optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber('GRID_CELL_WIDTH', 'Cell width in measurement units',
                type=QgsProcessingParameterNumber.Double, defaultValue=settings.default_dimension, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber('GRID_CELL_HEIGHT', 'Cell height in measurement units',
                type=QgsProcessingParameterNumber.Double, defaultValue=settings.default_dimension, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum('UNITS', 'Measurement unit',
                options=POLYGON_UNIT_LABELS, defaultValue=settings.poly_measurement_unit, optional=False)
        )
        style = QgsStyle.defaultStyle()
        self.ramp_names = style.colorRampNames()
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
        param = QgsProcessingParameterNumber('MAX_IMAGE_DIMENSION', 'Maximum width or height dimensions for output image',
            type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=settings.max_image_size, optional=False)
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

    def group(self):
        return 'Raster density'

    def groupId(self):
        return 'rasterdensity'

    def name(self):
        return 'styledpolygondensity'

    def displayName(self):
        return 'Styled polygon density (raster)'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/styledrasterdensity.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return StyledPolygonRasterDensityAlgorithm()

