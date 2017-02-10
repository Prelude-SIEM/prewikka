<%!
import sys
from prewikka import env, utils
from prewikka.utils import nameToPath

if sys.version_info >= (3,0):
    import builtins
else:
    import __builtin__ as builtins
%>

<%inherit file="/prewikka/templates/toplayout.mak" />

<%block name="toplayout_content">
<script type="text/javascript">

function check_same_origin(url) {
    /*
     * Force url.hostname to be defined in IE
     * (problem with dynamically created links)
     */
    if ( ! url.hostname )
        url.href = url.href;

    /*
     * When the default port is used in IE,
     * location.port is empty but url.port is not
     */
    default_port = {"http:": "80", "https:": "443"};
    return url.protocol == location.protocol && url.hostname == location.hostname && (url.port || default_port[url.protocol]) == (location.port || default_port[location.protocol]);
}

$(document).ready(function() {
        % if not(context.get("is_error_template")):
           prewikka_loadTab({url: window.location.pathname, data: "${env.request.web.get_query_string() | n}", type: "${env.request.web.method}"});
        % endif

        /*
         * Back/Forward support.
         */
        $(window).on("popstate", function(e) {
                if ( e.originalEvent.state == null )
                        return;

                prewikka_loadTab({url: e.originalEvent.state, history:false});
        });

        $(document).on("click", "a:not(.ajax-bypass), area:not(.ajax-bypass)", function(event) {
                if ( $(this).data("confirm") )
                        return false;

                var url = $(this).attr('href');

                if ( ! url || url.indexOf("#") != -1 )
                        return;

                if ( ! check_same_origin(this) ) {
                        window.open(url, "${env.external_link_target}");
                        return false;
                }

                if ( ! $(this).hasClass("widget-link") )
                        prewikka_loadTab({ url: url });
                else
                        prewikka_widget({ url: url, dialog: { title: $(this).attr('title') }});

                return false;
        });

        $(document).on("click", ":input.widget-link", function() {
                prewikka_widget({
                        url: $(this).closest("form").attr("action"),
                        data: $(this).closest("form").serialize(),
                        dialog: { title: $(this).attr("title") }
                });

                return false;
        });

        $(document).on("submit", "body form", function() {
                $(this).find("input[name=_download]").remove();

                var form = this;
                var data = $(this).serialize();

                if ( $(this).data("clicked") ) {
                        data += "&" + $(this).data("clicked");
                        $(this).removeData("clicked");
                }

                if ( $(this).data("enable-download") ) {
                        $(this).removeData("enable-download");
                        $(this).append('<input type="hidden" name="_download" value="true" />');

                        /* No AJAX for download */
                        return true;
                }

                prewikka_loadTab({
                        url: $(this).attr("action"),
                        type: $(this).attr("method"),
                        data: data,
                        success: function() {
                              /* Close the modal potentially containing the form. */
                              $(form).closest(".modal").modal('hide');
                              $("#main form").trigger("submit-success");
                        },
                        error: function() {
                              $("#main form").trigger("submit-error");
                        },
                        complete: function() {
                              $("#main form").trigger("submit-complete");
                        },

                });

                return false;
        });

        $(document).on("click", "#main form :input[type=submit]", function() {
                var name = $(this).attr("name");
                var value = $(this).attr("value");

                if ( name && value )
                        $(this).closest("form").data("clicked", encodeURIComponent(name) + "=" + encodeURIComponent(value));
        });
});
</script>

<div id="topmenu">
  <div class="topmenu_nav">
    <div class="topmenu_nav_container"></div>
    <div class="topmenu_content">

    <%
      sections = {}
      if env.menumanager:
          sections = env.menumanager.get_sections()
    %>
    % for section in sections:
        <% style = "" %>

        % if nameToPath(section) != env.request.web.path_elements[0] if len(env.request.web.path_elements) > 0 else "":
            <% style="display:none;" %>
        % endif

        <ul style="${style}" class="nav nav-tabs topmenu_section" id="topmenu_${ nameToPath(section) }" data-section-title="${ _(section) }">
        % for name, views in sections.get(section).items():
            <%
            class_ = ""
            firstview = builtins.next(builtins.iter(views.values()))
            %>

            % if not(firstview.check_permissions(env.request.user)):
                <% continue %>
            % endif

            % if env.request.web.path == firstview.view_path:
                <% class_ = 'active' %>
            % endif

            <li role="presentation" class="${class_} topmenu_item"><a href="${ url_for(firstview.view_endpoint) }" class="topmenu_links">${_(name)}</a></li>
        % endfor
        </ul>
    % endfor
    </div>
  </div>
</div>
<a type="button" id="config-button" data-toggle="collapse" data-target=".prewikka-view-config"><i class="fa fa-cog"></i></a>
</%block>

<%block name="toplayout_menu">

<%
menus = {}
if env.menumanager:
    menus = env.menumanager.get_menus()
    sections = env.menumanager.get_sections()
    declared_sections = env.menumanager.get_declared_sections()

def _get_view_url(section, tabs):
    if section not in sections:
        return

    for tab in tabs:
        if tab not in sections[section]:
            continue

        for view in sections[section][tab].values():
            if view.check_permissions(env.request.user):
                return url_for(view.view_endpoint)
%>

<%def name="write_menu(obj, section, tabs)">
    <% url = _get_view_url(section, tabs) %>

    % if url:
    <li>
        <a href="${ url }">
    % else:
    <li class="disabled" title="${ _('This app has been disabled or failed to load.') }">
        <a>
    % endif
            % if "icon" in obj:
            <i class="fa fa-${obj['icon']}"></i>
            % endif
            ${ _(obj["name"]) }
        </a>
    </li>
</%def>

<%def name="write_menu_expand(obj, sections)">
    <li class="dropdown dropdown-submenu">
        <a class="dropdown-toggle" data-toggle="dropdown">
            % if "icon" in obj:
            <i class="fa fa-${obj['icon']}"></i>
            % endif
            ${ _(obj["name"]) }
        </a>
        <ul class="dropdown-menu">
            % for section, tabs, name in sections:
            ${write_menu({"name": name}, section, tabs)}
            % endfor
        </ul>
    </li>
</%def>

% if env.request.user:
    <ul id="top_view_navbar_menu" class="nav navbar-nav navbar-primary">
    % for menu in menus:
        <li class="dropdown">
            <a class="dropdown-toggle" data-toggle="dropdown">
                % if "icon" in menu:
                <i class="fa fa-${ menu['icon'] }"></i>
                % endif
                ${ menu.get("name", "") }
            </a>
            <ul class="dropdown-menu" role="menu">
            % for category in menu.get("categories", []):
                % if "name" in category:
                    ${write_menu_expand(category, [(section["name"], section.get("tabs", []), section["name"]) for section in category.get("sections", [])])}
                % else:
                    % for section in category.get("sections", []):
                        % if not section.get("expand"):
                            ${write_menu(section, section["name"], section.get("tabs", []))}
                        % else:
                            ${write_menu_expand(section, [(section["name"], [tab], tab) for tab in section.get("tabs", [])])}
                        % endif
                    % endfor
                % endif
            % endfor
            % if menu.get("default"):

            ## Put the sections not declared in the YAML file into the default menu
            % for name in set(sections) - set(declared_sections):
                ${write_menu({"name": name}, name, sections[name].keys())}
            % endfor

                <li role="separator" class="divider"></li>
                <% url = url_for('About.render', _default=None) %>
                % if url:
                <li><a class="widget-link" title="${ _("About") }" href="${ url }">${ _("About") }</a></li>
                % endif
                % if env.session.can_logout():
                <li><a id="logout" title="${ _("Logout") }" class="ajax-bypass" href="${ url_for('Logout.render') }" data-confirm="${ _("Are you sure you want to log out?") }">${ _("Logout") }</a></li>
                % endif
            % endif
            </ul>
        </li>
    % endfor
    </ul>
% endif
</%block>

<%block name="main_content">
    <div id="ajax-spinner" class="ajax-spinner" style="display:none;">
        <div class="loader">${ _("Loading") }</div>
    </div>
    <div id="main" class="content">
     <%block name="content"></%block>
    </div>
</%block>
