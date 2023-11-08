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
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.core import Qgis, QgsStyle, QgsSymbol, QgsGraduatedSymbolRenderer, QgsClassificationLogarithmic
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterField)
import processing
from .settings import settings, COLOR_RAMP_MODE


class GraduatedStyleAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                'INPUT', 'Input map layer', [QgsProcessing.TypeVectorAnyGeometry ])
        )
        self.addParameter(
            QgsProcessingParameterField(
                'GROUP_FIELD',
                'Field used for styling',
                parentLayerParameterName='INPUT',
                type=QgsProcessingParameterField.Any,
                defaultValue='NUMPOINTS',
                optional=False)
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
        self.addParameter(
            QgsProcessingParameterNumber(
                'CLASSES',
                'Number of gradient colors',
                QgsProcessingParameterNumber.Integer,
                defaultValue=settings.num_ramp_classes,
                minValue=2,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                'MODE',
                'Color ramp mode',
                options=COLOR_RAMP_MODE,
                defaultValue=settings.color_ramp_mode,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                'NO_OUTLINE',
                'No feature outlines',
                True,
                optional=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsVectorLayer(parameters, 'INPUT', context)
        attr = self.parameterAsString(parameters, 'GROUP_FIELD', context)
        if Qgis.QGIS_VERSION_INT >= 32200:
            ramp_name = self.parameterAsString(parameters, 'RAMP_NAMES', context)
        else:
            ramp_name = settings.ramp_names[self.parameterAsEnum(parameters, 'RAMP_NAMES', context)]
        mode = self.parameterAsInt(parameters, 'MODE', context)
        num_classes = self.parameterAsInt(parameters, 'CLASSES', context)
        no_outline = self.parameterAsBool(parameters, 'NO_OUTLINE', context)
        invert = self.parameterAsBool(parameters, 'INVERT', context)
        
        if mode == 0: # Quantile
            grad_mode = QgsGraduatedSymbolRenderer.Quantile
        elif mode == 1: # Equal Interval
            grad_mode = QgsGraduatedSymbolRenderer.EqualInterval
        elif mode == 2: # Logarithmic scale
            grad_mode = QgsGraduatedSymbolRenderer.Quantile
        elif mode == 3: # Natural Breaks (Jenks)
            grad_mode = QgsGraduatedSymbolRenderer.Jenks
        elif mode == 4: # Pretty Breaks
            grad_mode = QgsGraduatedSymbolRenderer.Pretty
        elif mode == 5: # Standard Deviation
            grad_mode = QgsGraduatedSymbolRenderer.StdDev

        geomtype = layer.geometryType()
        symbol = QgsSymbol.defaultSymbol(geomtype)
        if no_outline:
            symbol.symbolLayer(0).setStrokeStyle(Qt.PenStyle(Qt.NoPen))
        style = QgsStyle.defaultStyle()
        ramp = style.colorRamp(ramp_name)
        if invert:
            ramp.invert()
        new_renderer = QgsGraduatedSymbolRenderer.createRenderer(
            layer, # The layer
            attr, # Attribute name
            num_classes, # Number of classes
            grad_mode, # Mode
            symbol, # QgsSymbol
            ramp # Our color ramp
        )
        if mode == 2:
            new_renderer.setClassificationMethod(QgsClassificationLogarithmic())
            new_renderer.updateClasses(layer, num_classes)
        layer.setRenderer(new_renderer)
        # feedback.pushInfo('dump: {}'.format(new_renderer.dump()))
        # new_renderer.updateClasses(layer, num_classes)
        layer.triggerRepaint()
        return({})

    def group(self):
        return 'Styles'

    def groupId(self):
        return 'styles'

    def name(self):
        return 'graduatedstyle'

    def displayName(self):
        return 'Apply graduated style'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/gradient.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return GraduatedStyleAlgorithm()
