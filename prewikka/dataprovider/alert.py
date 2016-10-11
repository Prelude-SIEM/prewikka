# Copyright (C) 2016 CS-SI. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>

from prewikka import pluginmanager, version
from prewikka.dataprovider import DataProviderNormalizer

class AlertDataProvider(pluginmanager.PluginBase):
    plugin_name = "Alert data provider"
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Provides an API to fetch security alerts")
    normalizer = DataProviderNormalizer('create_time')
