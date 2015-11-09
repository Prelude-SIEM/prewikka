import pkg_resources

from . import templates
from prewikka import view, version

class About(view.View):
    plugin_name = "About"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Prewikka About page")
    plugin_htdocs = (("about", pkg_resources.resource_filename(__name__, 'htdocs')),)

    view_name = N_("About")
    view_template = templates.About
    view_parameters = view.Parameters
    view_section = N_("Settings")
    view_order = 6
