import os
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsStyle, QgsSymbol, QgsMapLayerType, QgsRasterBandStats, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterField)
import processing


class RasterStyleAlgorithm(QgsProcessingAlgorithm):
    PrmInput = 'INPUT'
    PrmRampName = 'RAMPNAME'
    PrmInterpolation = 'INTERPOLATION'
    PrmMode = 'MODE'
    PrmClasses = 'CLASSES'
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.PrmInput, 'Input raster layer')
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
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsRasterLayer(parameters, self.PrmInput, context)
        ramp_name = self.parameterAsString(parameters, self.PrmRampName, context)
        interp = self.parameterAsInt(parameters, self.PrmInterpolation, context)
        mode = self.parameterAsInt(parameters, self.PrmMode, context)
        num_classes = self.parameterAsInt(parameters, self.PrmClasses, context)
        
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

    def name(self):
        return 'rasterstyle'

    def displayName(self):
        return 'Apply a pseudocolor raster style'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/styleraster.png'))

    def createInstance(self):
        return RasterStyleAlgorithm()
