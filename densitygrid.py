import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsStyle, QgsUnitTypes

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterMapLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterFeatureSink
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

class KernelDensityAlgorithm(QgsProcessingAlgorithm):
    PrmInput = 'INPUT'
    PrmExtent = 'EXTENT'
    PrmGridType = 'GRIDTYPE'
    PrmMinGridCount = 'MINGRIDCOUNT'
    PrmGridCellWidth = 'GRIDCELLWIDTH'
    PrmGridCellHeight = 'GRIDCELLHEIGHT'
    PrmUnits = 'Units'
    PrmMaximumGridSize = 'MAXIMUMGRIDSIZE'
    PrmClasses = 'CLASSES'
    PrmRampNames = 'RAMPNAMES'
    PrmColorRampMode = 'COLORRAMPMODE'
    PrmOutput = 'OUTPUT'
    PrmNoOutline = 'NOOUTLINE'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterMapLayer(self.PrmInput, 'Input point vector layer', defaultValue=None,
            types=[QgsProcessing.TypeVectorPoint])
        )
        self.addParameter(
            QgsProcessingParameterExtent(self.PrmExtent, 'Grid extent', optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmMinGridCount, 'Minimum cell histogram count',
                type=QgsProcessingParameterNumber.Integer, minValue=0, defaultValue=1)
        )
        self.addParameter(
            QgsProcessingParameterEnum(self.PrmGridType, 'Grid type',
                options=['Rectangle','Diamond','Hexagon'],
                defaultValue=2, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmGridCellWidth, 'Grid cell width',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmGridCellHeight, 'Grid cell height',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(self.PrmUnits, 'Grid measurement unit',
                options=DISTANCE_LABELS, defaultValue=0, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmMaximumGridSize, 'Maximum grid width or height',
                type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=500, optional=False)
        )
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
            QgsProcessingParameterFeatureSink(self.PrmOutput, 'Output density heatmap',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        grid_type = self.parameterAsInt(parameters, self.PrmGridType, context) + 2
        min_grid_cnt = self.parameterAsInt(parameters, self.PrmMinGridCount, context)
        extent = self.parameterAsExtent(parameters, self.PrmExtent, context)
        extent_crs = self.parameterAsExtentCrs(parameters, self.PrmExtent, context)
        num_classes = self.parameterAsInt(parameters, self.PrmClasses, context)
        ramp_name = self.parameterAsString(parameters, self.PrmRampNames, context)
        ramp_mode = self.parameterAsInt(parameters, self.PrmColorRampMode, context)
        no_outline = self.parameterAsBool(parameters, self.PrmNoOutline, context)
        cell_width = self.parameterAsDouble(parameters, self.PrmGridCellWidth, context)
        cell_height = self.parameterAsDouble(parameters, self.PrmGridCellHeight, context)
        selected_units = self.parameterAsInt(parameters, self.PrmUnits, context)
        max_dimension = self.parameterAsInt(parameters, self.PrmMaximumGridSize, context)
        
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
            'POINTS': parameters[self.PrmInput],
            'POLYGONS': outputs['CreateGrid']['OUTPUT'],
            'WEIGHT': '',
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
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
            'OUTPUT': parameters[self.PrmOutput]
        }
        outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results[self.PrmOutput] = outputs['ExtractByAttribute']['OUTPUT']

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Apply a graduated style
        alg_params = {
            'NoOutline': no_outline,
            'classes': num_classes,
            'groupfield': 'NUMPOINTS',
            'maplayer': outputs['ExtractByAttribute']['OUTPUT'],
            'mode': ramp_mode,  # Equal Count (Quantile)
            'rampnames': ramp_name
        }
        outputs['ApplyAGraduatedStyle'] = processing.run('densityanalysis:gratuatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'kerneldensity'

    def displayName(self):
        return 'Create kernel density grid'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/densitygrid.svg'))

    def createInstance(self):
        return KernelDensityAlgorithm()
