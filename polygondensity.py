import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsStyle, QgsUnitTypes, QgsCoordinateTransform, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterRasterDestination
    )
import processing

DISTANCE_LABELS = ["Size in pixels", "Kilometers", "Meters", "Miles", 'Yards', "Feet", "Nautical Miles", "Degrees"]

def conversionToCrsUnits(selected_unit, crs_unit, value):
    if selected_unit == 1:  # Kilometers
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceKilometers, crs_unit)
    elif selected_unit == 2:  # Meters
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMeters, crs_unit)
    elif selected_unit == 3:  # Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceMiles, crs_unit)
    elif selected_unit == 4:  # Yards
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceYards, crs_unit)
    elif selected_unit == 5:  # Feet
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceFeet, crs_unit)
    elif selected_unit == 6:  # Nautical Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceNauticalMiles, crs_unit)
    elif selected_unit == 7:  # Degrees
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(QgsUnitTypes.DistanceDegrees, crs_unit)
    return(measureFactor * value)

def conversionFromCrsUnits(selected_unit, crs_unit, value):
    if selected_unit == 1:  # Kilometers
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceKilometers)
    elif selected_unit == 2:  # Meters
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceMeters)
    elif selected_unit == 3:  # Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceMiles)
    elif selected_unit == 4:  # Yards
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceYards)
    elif selected_unit == 5:  # Feet
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceFeet)
    elif selected_unit == 6:  # Nautical Miles
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceNauticalMiles)
    elif selected_unit == 7:  # Degrees
        measureFactor = QgsUnitTypes.fromUnitToUnitFactor(crs_unit, QgsUnitTypes.DistanceDegrees)
    return(measureFactor * value)

class PolygonRasterDensityAlgorithm(QgsProcessingAlgorithm):
    PrmInput = 'INPUT'
    PrmExtent = 'EXTENT'
    PrmGridCellWidth = 'GRIDCELLWIDTH'
    PrmGridCellHeight = 'GRIDCELLHEIGHT'
    PrmUnits = 'UNITS'
    PrmMaximumImageDimension = 'MAXIMUMIMAGEDIMENSION'
    PrmRampNames = 'RAMPNAMES'
    PrmColorRampMode = 'COLORRAMPMODE'
    PrmAutoStyle = 'AUTOSTYLE'
    PrmRampName = 'RAMPNAME'
    PrmInterpolation = 'INTERPOLATION'
    PrmMode = 'MODE'
    PrmClasses = 'CLASSES'
    PrmOutput = 'OUTPUT'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(self.PrmInput, 'Input polygon vector layer',
            types=[QgsProcessing.TypeVectorPolygon])
        )
        self.addParameter(
            QgsProcessingParameterExtent(self.PrmExtent, 'Grid extent', optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmGridCellWidth, 'Pixel width or grid cell width',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmGridCellHeight, 'Pixel height or grid cell height',
                type=QgsProcessingParameterNumber.Double, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(self.PrmUnits, 'Grid measurement unit',
                options=DISTANCE_LABELS, defaultValue=1, optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(self.PrmMaximumImageDimension, 'Maximum width or height dimensions for output image',
                type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=5000, optional=False)
        )
        '''self.addParameter(
            QgsProcessingParameterBoolean(
                self.PrmAutoStyle,
                'Automatically apply the following style',
                True,
                optional=False)
        )
        style = QgsStyle.defaultStyle()
        ramp_names = style.colorRampNames()
        ramp_name_param = QgsProcessingParameterString(self.PrmRampName, 'Color ramp name', defaultValue='Reds')
        ramp_name_param.setMetadata( {'widget_wrapper': {'value_hints': ramp_names } } )
        self.addParameter(ramp_name_param)
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmInterpolation,
                'Interpolation',
                options=['Discrete','Linear','Exact'],
                defaultValue=1,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.PrmMode,
                'Mode',
                options=['Continuous','Equal Interval','Quantile'],
                defaultValue=0,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PrmClasses,
                'Number of classes',
                QgsProcessingParameterNumber.Integer,
                defaultValue=10,
                minValue=2,
                optional=False)
        )'''

        self.addParameter(
            QgsProcessingParameterRasterDestination(self.PrmOutput, 'Output polygon density heatmap',
                createByDefault=True, defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsLayer(parameters, self.PrmInput, context)
        extent = self.parameterAsExtent(parameters, self.PrmExtent, context)
        feedback.pushInfo("{}".format(extent))
        extent_crs = self.parameterAsExtentCrs(parameters, self.PrmExtent, context)
        feedback.pushInfo("{}".format(extent_crs))
        # ramp_name = self.parameterAsString(parameters, self.PrmRampNames, context)
        # ramp_mode = self.parameterAsInt(parameters, self.PrmColorRampMode, context)
        cell_width = self.parameterAsDouble(parameters, self.PrmGridCellWidth, context)
        cell_height = self.parameterAsDouble(parameters, self.PrmGridCellHeight, context)
        selected_units = self.parameterAsInt(parameters, self.PrmUnits, context)
        max_dimension = self.parameterAsInt(parameters, self.PrmMaximumImageDimension, context)

        '''auto_style = self.parameterAsBool(parameters, self.PrmAutoStyle, context)
        ramp_name = self.parameterAsString(parameters, self.PrmRampName, context)
        interp = self.parameterAsInt(parameters, self.PrmInterpolation, context)
        mode = self.parameterAsInt(parameters, self.PrmMode, context)
        num_classes = self.parameterAsInt(parameters, self.PrmClasses, context)'''

        layer_crs = layer.sourceCrs()
        if extent.isNull():
            extent = layer.sourceExtent()
            extent_crs = layer_crs
        
        if layer_crs != extent_crs:
            transform = QgsCoordinateTransform(extent_crs, layer_crs, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
            extent_crs = layer_crs
            
        if selected_units == 0:
            # This is the exact width and height of the output image
            width = int(cell_width)
            height = int(cell_height)
        else:
            # Determine the width and height in extent units
            extent_units = extent_crs.mapUnits()
            cell_width_extent = conversionToCrsUnits(selected_units, extent_units, cell_width)
            cell_height_extent = conversionToCrsUnits(selected_units, extent_units, cell_height)
            # Add one additional cell, half on each side to better encapsulate the data
            width = int(extent.width() / cell_width_extent)
            height = int(extent.height() / cell_height_extent)
            if width > max_dimension or height > max_dimension:
                feedback.reportError('Maximum dimensions exceeded')
                feedback.reportError('Image width: {}'.format(width))
                feedback.reportError('Image height: {}'.format(height))
                max_cell_width = extent.width() / max_dimension
                max_cell_height = extent.height() / max_dimension
                feedback.reportError('Use values that are greater than, width: {}, height: {}'.format(
                    conversionFromCrsUnits(selected_units, extent_units, max_cell_width),
                    conversionFromCrsUnits(selected_units, extent_units, max_cell_height)))
                feedback.reportError('or increase the maximum grid width and height.')
                raise QgsProcessingException()
        feedback.pushInfo('Output image width: {}'.format(width))
        feedback.pushInfo('Output image height: {}'.format(height))
        
        outputs = {}
        results = {}

        alg_params = {
            'BURN': 1,
            'DATA_TYPE': 5,  # Float32
            'EXTENT': extent,
            'EXTRA': '-add',
            'FIELD': '',
            'HEIGHT': height,
            'INIT': 0,
            'INPUT': parameters[self.PrmInput],
            'INVERT': False,
            'NODATA': 0,
            'OPTIONS': '',
            'UNITS': 0,  # Pixels
            'USE_Z': False,
            'WIDTH': width,
            'OUTPUT': parameters[self.PrmOutput]
        }
        outputs['Rasterize'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=False)
        
        '''if auto_style:
            # Apply a pseudocolor style
            alg_params = {
                'INTERPOLATION': interp,
                'CLASSES': num_classes,
                'MAPLAYER': outputs['Rasterize']['OUTPUT'],
                'MODE': mode,
                'RAMPNAME': ramp_name
            }
            outputs['RasterStyle'] = processing.run('densityanalysis:rasterstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=False)'''

        results[self.PrmOutput] = outputs['Rasterize']['OUTPUT']
        return results

    def name(self):
        return 'polygondensity'

    def displayName(self):
        return 'Create a polygon raster density map'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/polydensity.png'))

    def createInstance(self):
        return PolygonRasterDensityAlgorithm()

