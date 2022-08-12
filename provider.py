import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .randomstyle import RandomStyleAlgorithm
from .graduatedstyle import GraduatedStyleAlgorithm
from .densitygrid import StyledDensityGridAlgorithm
from .geohashdensity import GeohashDensityAlgorithm
from .geohashdensitymap import GeohashDensityMapAlgorithm
from .h3grid import H3GridAlgorithm
from .h3density import H3DensityAlgorithm
from .h3densitymap import H3DensityMapAlgorithm
from .polygondensity import PolygonRasterDensityAlgorithm
from .rasterstyle import RasterStyleAlgorithm
from . styledkde import StyledKdeAlgorithm

class DensityAnalysisProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(RandomStyleAlgorithm())
        self.addAlgorithm(GraduatedStyleAlgorithm())
        self.addAlgorithm(StyledDensityGridAlgorithm())
        self.addAlgorithm(GeohashDensityAlgorithm())
        self.addAlgorithm(GeohashDensityMapAlgorithm())
        self.addAlgorithm(H3GridAlgorithm())
        self.addAlgorithm(H3DensityAlgorithm())
        self.addAlgorithm(H3DensityMapAlgorithm())
        self.addAlgorithm(RasterStyleAlgorithm())
        self.addAlgorithm(PolygonRasterDensityAlgorithm())
        self.addAlgorithm(StyledKdeAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/densitygrid.svg')

    def id(self):
        return 'densityanalysis'

    def name(self):
        return 'Density analysis'

    def longName(self):
        return self.name()
