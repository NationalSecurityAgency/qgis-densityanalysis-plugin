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
from qgis.core import QgsCoordinateTransform, QgsProject
from .settings import settings, POLYGON_UNIT_LABELS, conversionToCrsUnits, conversionFromCrsUnits

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterExtent,
    QgsProcessingParameterEnum,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterRasterDestination
    )
import processing

class PolygonRasterDensityAlgorithm(QgsProcessingAlgorithm):

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
        param = QgsProcessingParameterNumber('MAX_IMAGE_DIMENSION', 'Maximum width or height dimensions for output image',
            type=QgsProcessingParameterNumber.Integer, minValue=1, defaultValue=settings.max_image_size, optional=False)
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

        layer_crs = layer.sourceCrs()
        if extent.isNull():
            extent = layer.sourceExtent()
            extent_crs = layer_crs
        
        if layer_crs != extent_crs:
            transform = QgsCoordinateTransform(extent_crs, layer_crs, QgsProject.instance())
            extent = transform.transformBoundingBox(extent)
            extent_crs = layer_crs
            
        if selected_units == 7:
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

    def group(self):
        return 'Raster density'

    def groupId(self):
        return 'rasterdensity'

    def name(self):
        return 'polygondensity'

    def displayName(self):
        return 'Polygon density (raster)'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/polydensity.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return PolygonRasterDensityAlgorithm()

