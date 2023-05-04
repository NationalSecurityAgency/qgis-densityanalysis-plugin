# -*- coding: utf-8 -*-

from qgis.core import QgsApplication
from .provider import DensityAnalysisProvider

import os

class DensityAnalysis(object):
    def __init__(self):
        self.provider = None

    def initProcessing(self):
        self.provider = DensityAnalysisProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)


