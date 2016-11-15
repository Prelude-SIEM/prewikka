from __future__ import absolute_import, division, print_function, unicode_literals

import pkg_resources
from prewikka import version, view


class About(view.View):
    plugin_name = "About"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Prelude About page")
    plugin_htdocs = (("about", pkg_resources.resource_filename(__name__, 'htdocs')),)

    view_template = pkg_resources.resource_filename(__name__, 'templates/about.mak')
