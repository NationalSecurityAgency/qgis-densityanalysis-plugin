def classFactory(iface):
    if iface:
        from .densityanalysis import DensityAnalysis
        return DensityAnalysis(iface)
    else:
        # This is used when the plugin is loaded from the command line command qgis_process
        from .densityanalysisprocessing import DensityAnalysis
        return DensityAnalysis()
