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
from qgis.core import Qgis, QgsStyle, QgsMapLayerType, QgsRasterBandStats, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterRasterLayer)
import processing
from .settings import settings


class RasterStyleAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                'INPUT', 'Input raster layer')
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
                'Number of gradient colors',
                QgsProcessingParameterNumber.Integer,
                defaultValue=settings.num_ramp_classes,
                minValue=2,
                optional=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsRasterLayer(parameters, 'INPUT', context)
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name = self.parameterAsString(parameters, 'RAMP_NAMES', context)
        else:
            ramp_name = settings.ramp_names[self.parameterAsEnum(parameters, 'RAMP_NAMES', context)]
        invert = self.parameterAsBool(parameters, 'INVERT', context)
        interp = self.parameterAsInt(parameters, 'INTERPOLATION', context)
        mode = self.parameterAsInt(parameters, 'MODE', context)
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)
        
        rnd = layer.renderer()
        if layer.type() != QgsMapLayerType.RasterLayer or rnd.bandCount() != 1:
            feedback.reportError('This is only for single band raster images.')
            raise QgsProcessingException()
            
        if interp == 0: # Discrete
            interpolation = QgsColorRampShader.Discrete
        elif interp == 1: # Interpolated
            interpolation = QgsColorRampShader.Interpolated
        elif interp == 2: # Exact
            interpolation = QgsColorRampShader.Exact

        if mode == 0: # Continuous
            shader_mode = QgsColorRampShader.Continuous
        elif mode == 1: # Equal Interval
            shader_mode = QgsColorRampShader.EqualInterval
        elif mode == 2: # Quantile
            shader_mode = QgsColorRampShader.Quantile

        provider = layer.dataProvider()
        stats = provider.bandStatistics(1, QgsRasterBandStats.Min | QgsRasterBandStats.Max)
        
        style = QgsStyle.defaultStyle()
        ramp = style.colorRamp(ramp_name)
        if invert:
            ramp.invert()
        color_ramp = QgsColorRampShader(stats.minimumValue, stats.maximumValue, ramp, interpolation, shader_mode)
        if shader_mode == QgsColorRampShader.Quantile:
            color_ramp.classifyColorRamp(classes=num_classes, band=1, input=provider)
        else:
            color_ramp.classifyColorRamp(classes=num_classes)

        raster_shader = QgsRasterShader()
        raster_shader.setRasterShaderFunction(color_ramp)

        # Create a new single band pseudocolor renderer
        renderer = QgsSingleBandPseudoColorRenderer(provider, layer.type(), raster_shader)

        layer.setRenderer(renderer)
        layer.triggerRepaint()
        return({})

    def group(self):
        return 'Styles'

    def groupId(self):
        return 'styles'

    def name(self):
        return 'rasterstyle'

    def displayName(self):
        return 'Apply pseudocolor raster style'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/styleraster.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return RasterStyleAlgorithm()
