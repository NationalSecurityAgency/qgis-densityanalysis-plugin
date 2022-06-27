import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon
from .randomstyle import RandomStyleAlgorithm
from .graduatedstyle import GraduatedStyleAlgorithm
from .densitygrid import KernelDensityAlgorithm
from .geohashdensity import GeohashDensityAlgorithm
from .h3density import H3DensityAlgorithm
from .polygondensity import PolygonRasterDensityAlgorithm
from .rasterstyle import RasterStyleAlgorithm

class DensityAnalysisProvider(QgsProcessingProvider):

    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(RandomStyleAlgorithm())
        self.addAlgorithm(GraduatedStyleAlgorithm())
        self.addAlgorithm(KernelDensityAlgorithm())
        self.addAlgorithm(GeohashDensityAlgorithm())
        self.addAlgorithm(H3DensityAlgorithm())
        self.addAlgorithm(RasterStyleAlgorithm())
        self.addAlgorithm(PolygonRasterDensityAlgorithm())

    def icon(self):
        return QIcon(os.path.dirname(__file__) + '/icons/densitygrid.svg')

    def id(self):
        return 'densityanalysis'

    def name(self):
        return 'Density analysis'

    def longName(self):
        return self.name()
