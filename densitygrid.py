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
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterField,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFeatureSink
    )
import processing
from .settings import settings, UNIT_LABELS, COLOR_RAMP_MODE, conversionToCrsUnits, conversionFromCrsUnits

class StyledDensityGridAlgorithm(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer('INPUT', 'Input point vector layer', 
            [QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterExtent('EXTENT', 'Grid extent (defaults to layer extent)', optional=True)
        )
        self.addParameter(
            QgsProcessingParameterEnum('GRID_TYPE', 'Grid type',
                options=['Rectangle','Diamond','Hexagon'],
                defaultValue=2, optional=False)
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
                options=UNIT_LABELS, defaultValue=settings.measurement_unit, optional=False)
        )

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

        param = QgsProcessingParameterNumber('MIN_GRID_COUNT', 'Minimum cell histogram count',
            type=QgsProcessingParameterNumber.Integer, minValue=0, defaultValue=1)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        param = QgsProcessingParameterNumber('MAX_GRID_SIZE', 'Maximum grid width or height',
            type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=1000, optional=False)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
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
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output density heatmap',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        layer = self.parameterAsLayer(parameters, 'INPUT', context)
        grid_type = self.parameterAsInt(parameters, 'GRID_TYPE', context) + 2
        min_grid_cnt = self.parameterAsInt(parameters, 'MIN_GRID_COUNT', context)
        extent = self.parameterAsExtent(parameters, 'EXTENT', context)
        extent_crs = self.parameterAsExtentCrs(parameters, 'EXTENT', context)
        if extent.isNull():
            extent = layer.sourceExtent()
            extent_crs = layer.sourceCrs()
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
        cell_width = self.parameterAsDouble(parameters, 'GRID_CELL_WIDTH', context)
        cell_height = self.parameterAsDouble(parameters, 'GRID_CELL_HEIGHT', context)
        selected_units = self.parameterAsInt(parameters, 'UNITS', context)
        max_dimension = self.parameterAsInt(parameters, 'MAX_GRID_SIZE', context)
        if 'WEIGHT' in parameters and parameters['WEIGHT']:
            use_weight = True
            weight_field = self.parameterAsString(parameters, 'WEIGHT', context)
        else:
            use_weight = False
        
        # Determine the width and height in extent units
        extent_units = extent_crs.mapUnits()
        cell_width_extent = conversionToCrsUnits(selected_units, extent_units, cell_width)
        cell_height_extent = conversionToCrsUnits(selected_units, extent_units, cell_height)
        # Add one additional cell, half on each side to better encapsulate the data
        min_x = extent.xMinimum() - cell_width_extent / 2
        max_x = extent.xMaximum() + cell_width_extent / 2
        min_y = extent.yMinimum() - cell_height_extent / 2
        max_y = extent.yMaximum() + cell_height_extent / 2
        extent.setXMinimum(min_x)
        extent.setXMaximum(max_x)
        extent.setYMinimum(min_y)
        extent.setYMaximum(max_y)
        width = int(extent.width() / cell_width_extent)
        height = int(extent.height() / cell_height_extent)
        if width > max_dimension or height > max_dimension:
            model_feedback.reportError('Maximum dimensions exceeded')
            model_feedback.reportError('Width: {}'.format(width))
            model_feedback.reportError('Height: {}'.format(height))
            max_cell_width = extent.width() / max_dimension
            max_cell_height = extent.height() / max_dimension
            model_feedback.reportError('Use values that are greater than, width: {}, height: {}'.format(
                conversionFromCrsUnits(selected_units, extent_units, max_cell_width),
                conversionFromCrsUnits(selected_units, extent_units, max_cell_height)))
            model_feedback.reportError('or increase the maximum grid width and height.')
            raise QgsProcessingException()
        model_feedback.pushInfo('Grid width: {}'.format(width))
        model_feedback.pushInfo('Grid height: {}'.format(height))

        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}
        
        # Create grid
        alg_params = {
            'CRS': 'ProjectCrs',
            'EXTENT': extent,
            'HOVERLAY': 0,
            'HSPACING': cell_width_extent,
            'TYPE': grid_type,
            'VOVERLAY': 0,
            'VSPACING': cell_height_extent,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['CreateGrid'] = processing.run('native:creategrid', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Count points in polygon
        alg_params = {
            'CLASSFIELD': '',
            'FIELD': 'NUMPOINTS',
            'POINTS': parameters['INPUT'],
            'POLYGONS': outputs['CreateGrid']['OUTPUT'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        if use_weight:
            alg_params['WEIGHT'] = weight_field
        else:
            alg_params['WEIGHT'] = ''
        outputs['CountPointsInPolygon'] = processing.run('native:countpointsinpolygon', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Extract by attribute
        alg_params = {
            'FIELD': 'NUMPOINTS',
            'INPUT': outputs['CountPointsInPolygon']['OUTPUT'],
            'OPERATOR': 3,  # ≥
            'VALUE': min_grid_cnt,
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['ExtractByAttribute']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Apply a graduated style
        alg_params = {
            'NO_OUTLINE': no_outline,
            'INVERT': invert,
            'CLASSES': num_classes,
            'GROUP_FIELD': 'NUMPOINTS',
            'INPUT': outputs['ExtractByAttribute']['OUTPUT'],
            'MODE': ramp_mode,  # Equal Count (Quantile)
            'RAMP_NAMES': ramp_name
        }
        outputs['GraduatedStyle'] = processing.run('densityanalysis:graduatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'densitymap'

    def displayName(self):
        return 'Styled density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/densitygrid.svg'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return StyledDensityGridAlgorithm()
