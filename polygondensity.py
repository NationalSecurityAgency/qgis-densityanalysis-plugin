import os
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsUnitTypes, QgsCoordinateTransform, QgsProject

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination
    )
import processing

DISTANCE_LABELS = ["Dimensions in pixels", "Kilometers", "Meters", "Miles", 'Yards', "Feet", "Nautical Miles", "Degrees"]

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
        if width == 0 or height == 0:
            feedback.reportError('Cell dimensions are too large and return an image dimenson of 0.')
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
            'INPUT': parameters['INPUT'],
            'INVERT': False,
            'NODATA': 0,
            'OPTIONS': '',
            'UNITS': 0,  # Pixels
            'USE_Z': False,
            'WIDTH': width,
            'OUTPUT': parameters['OUTPUT']
        }
        outputs['Rasterize'] = processing.run('gdal:rasterize', alg_params, context=context, feedback=feedback, is_child_algorithm=False)

        results['OUTPUT'] = outputs['Rasterize']['OUTPUT']
        return results

    def name(self):
        return 'polygondensity'

    def displayName(self):
        return 'Polygon density'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/polydensity.png'))

    def createInstance(self):
        return PolygonRasterDensityAlgorithm()

