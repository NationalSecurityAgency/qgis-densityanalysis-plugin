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
from qgis.core import Qgis

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterField,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterFeatureSink
    )
import processing
from .settings import settings, COLOR_RAMP_MODE

class StyledPolygonVectorDensityAlgorithm(QgsProcessingAlgorithm):
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer('INPUT', 'Input polygon layer', 
                [QgsProcessing.TypeVectorPolygon ],
                optional=False
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                'UNIQUEID',
                'Unique ID field for list of contributing source polygons',
                parentLayerParameterName='INPUT',
                type=QgsProcessingParameterField.Any,
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber('FILTER', 'Keep polygons with overlap counts >= to this',
                type=QgsProcessingParameterNumber.Integer, defaultValue=1, minValue=1, optional=False)
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
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output polygon density',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None, optional=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        layer = self.parameterAsLayer(parameters, 'INPUT', context)
        if 'UNIQUEID' in parameters and parameters['UNIQUEID']:
            unique_id = True
            unique_id_field = self.parameterAsString(parameters, 'UNIQUEID', context)
        else:
            unique_id = False
        filter = self.parameterAsInt(parameters, 'FILTER', context)
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
        
        results = {}
        outputs = {}
        
        alg_params = {
            'INPUT':  parameters['INPUT'],
            'FILTER': filter,
            'OUTPUT': parameters['OUTPUT']
        }
        if unique_id:
            alg_params['UNIQUEID'] = unique_id_field
        outputs['PolyVectorDensity'] = processing.run('densityanalysis:polygonvectordensity', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['OUTPUT'] = outputs['PolyVectorDensity']['OUTPUT']

        if feedback.isCanceled():
            return {}

        # Apply a graduated style
        alg_params = {
            'NO_OUTLINE': no_outline,
            'INVERT': invert,
            'CLASSES': num_classes,
            'GROUP_FIELD': 'NUMPOINTS',
            'INPUT': outputs['PolyVectorDensity']['OUTPUT'],
            'MODE': ramp_mode,
            'RAMP_NAMES': ramp_name
        }
        processing.run('densityanalysis:graduatedstyle', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def group(self):
        return 'Polygon density (vector)'

    def groupId(self):
        return 'polygondensity'

    def name(self):
        return 'styledpolygonvectordensity'

    def displayName(self):
        return 'Styled polygon density (vector)'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/vecpolydensity.png'))

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/help/polygondensityvector.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return StyledPolygonVectorDensityAlgorithm()
