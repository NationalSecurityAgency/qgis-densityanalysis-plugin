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
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .randomstyle import RandomStyleAlgorithm
from .graduatedstyle import GraduatedStyleAlgorithm
from .densitygrid import StyledDensityGridAlgorithm
from .geohashdensity import GeohashDensityAlgorithm
from .geohashmultidensity import GeohashMultiLayerDensityAlgorithm
from .geohashdensitymap import GeohashDensityMapAlgorithm
from .geohashmultidensitymap import GeohashMultiLayerDensityMapAlgorithm
from .h3grid import H3GridAlgorithm
from .h3density import H3DensityAlgorithm
from .h3multidensity import H3MultiLayerDensityAlgorithm
from .h3densitymap import H3DensityMapAlgorithm
from .h3multidensitymap import H3MultiLayerDensityMapAlgorithm
from .polygondensity import PolygonRasterDensityAlgorithm
from .styledpolygondensity import StyledPolygonRasterDensityAlgorithm
from .rasterstyle import RasterStyleAlgorithm
from .styledkde import StyledKdeAlgorithm
from .polyvectordensity import PolygonVectorDensityAlgorithm
from .styledpolyvectordensity import StyledPolygonVectorDensityAlgorithm

class DensityAnalysisProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(RandomStyleAlgorithm())
        self.addAlgorithm(GraduatedStyleAlgorithm())
        self.addAlgorithm(StyledDensityGridAlgorithm())
        self.addAlgorithm(GeohashDensityAlgorithm())
        self.addAlgorithm(GeohashMultiLayerDensityAlgorithm())
        self.addAlgorithm(GeohashDensityMapAlgorithm())
        self.addAlgorithm(GeohashMultiLayerDensityMapAlgorithm())
        self.addAlgorithm(H3GridAlgorithm())
        self.addAlgorithm(H3DensityAlgorithm())
        self.addAlgorithm(H3MultiLayerDensityAlgorithm())
        self.addAlgorithm(H3DensityMapAlgorithm())
        self.addAlgorithm(H3MultiLayerDensityMapAlgorithm())
        self.addAlgorithm(RasterStyleAlgorithm())
        self.addAlgorithm(PolygonRasterDensityAlgorithm())
        self.addAlgorithm(PolygonVectorDensityAlgorithm())
        self.addAlgorithm(StyledPolygonRasterDensityAlgorithm())
        self.addAlgorithm(StyledPolygonVectorDensityAlgorithm())
        self.addAlgorithm(StyledKdeAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/densitygrid.svg')

    def id(self):
        return 'densityanalysis'

    def name(self):
        return 'Density analysis'

    def longName(self):
        return self.name()
