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

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterField,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterNumber,
    QgsProcessingMultiStepFeedback,
    QgsProcessingParameterFeatureSink
    )
import processing

class PolygonVectorDensityAlgorithm(QgsProcessingAlgorithm):

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
        self.addParameter(
            QgsProcessingParameterFeatureSink('OUTPUT', 'Output polygon density',
                type=QgsProcessing.TypeVectorPolygon, createByDefault=True, defaultValue=None, optional=False)
        )

    def processAlgorithm(self, parameters, context, model_feedback):
        layer = self.parameterAsLayer(parameters, 'INPUT', context)
        if 'UNIQUEID' in parameters and parameters['UNIQUEID']:
            unique_id = True
            unique_id_field = self.parameterAsString(parameters, 'UNIQUEID', context)
        else:
            unique_id = False
        filter = self.parameterAsInt(parameters, 'FILTER', context)


        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(4, model_feedback)
        results = {}
        outputs = {}
        
        # Run Union algorithm
        alg_params = {
            'INPUT': parameters['INPUT'],
            'OVERLAY':None,
            'OVERLAY_FIELDS_PREFIX':'',
            'GRID_SIZE':None,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Union'] = processing.run('native:union', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Count points in polygon
        if unique_id:
            unique_param = [{'aggregate': 'count','delimiter': ',','input': '1','length': 0,'name': 'NUMPOINTS','precision': 0,'sub_type': 0,'type': 4,'type_name': 'int8'},{'aggregate': 'concatenate','delimiter': ',','input': 'to_string("'+unique_id_field+'")','length': 0,'name': 'ID_LIST','precision': 0,'sub_type': 0,'type': 10,'type_name': 'text'}]
        else:
            unique_param = [{'aggregate': 'count','delimiter': ',','input': '1','length': 0,'name': 'NUMPOINTS','precision': 0,'sub_type': 0,'type': 4,'type_name': 'int8'}]
        # Check to see if the polygons are going to be filtered out. If not (filter == 1) we will skip
        # the last algorithm.
        if filter == 1:
            alg_output = parameters['OUTPUT']
        else:
            alg_output = QgsProcessing.TEMPORARY_OUTPUT
        alg_params = {
            'INPUT': outputs['Union']['OUTPUT'],
            'GROUP_BY':'$geometry',
            'AGGREGATES': unique_param,
            'OUTPUT': alg_output
        }
        outputs['Aggregate'] = processing.run('native:aggregate', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}
        if filter == 1:
            # All the split polygons will be returned so we can skip the last algorithm
            results['OUTPUT'] = outputs['Aggregate']['OUTPUT']
        else:
            # Extract by attribute
            alg_params = {
                'FIELD': 'NUMPOINTS',
                'INPUT': outputs['Aggregate']['OUTPUT'],
                'OPERATOR': 3,  # ≥
                'VALUE': filter,
                'OUTPUT': parameters['OUTPUT']
            }
            outputs['ExtractByAttribute'] = processing.run('native:extractbyattribute', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
            results['OUTPUT'] = outputs['ExtractByAttribute']['OUTPUT']
        return results

    def group(self):
        return 'Polygon density (vector)'

    def groupId(self):
        return 'polygondensity'

    def name(self):
        return 'polygonvectordensity'

    def displayName(self):
        return 'Polygon density (vector)'

    def icon(self):
        return QIcon(os.path.join(os.path.dirname(__file__), 'icons/polydensity.png'))

    def shortHelpString(self):
        file = os.path.dirname(__file__) + '/help/polygondensityvector.help'
        if not os.path.exists(file):
            return ''
        with open(file) as helpf:
            help = helpf.read()
        return help

    def helpUrl(self):
        file = os.path.dirname(__file__) + '/index.html'
        if not os.path.exists(file):
            return ''
        return QUrl.fromLocalFile(file).toString(QUrl.FullyEncoded)

    def createInstance(self):
        return PolygonVectorDensityAlgorithm()
