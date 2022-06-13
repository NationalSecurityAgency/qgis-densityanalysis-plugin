try:
    import h3
    utils.H3_INSTALLED = True
except Exception:
    import os
    import site
    import platform
    if platform.system() == 'Windows':
        site.addsitedir(os.path.abspath(os.path.dirname(__file__) + '/libs'))
    try:
        import h3
        from . import utils
        utils.H3_INSTALLED = True
    except Exception:
        pass

def classFactory(iface):
    from .densityanalysis import DensityAnalysis
    return DensityAnalysis(iface)
