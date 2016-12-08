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
           prewikka_loadTab({url: "${document.href}", data: "${env.request.web.get_query_string() | n}", type: "${env.request.web.method}"});
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

        $(document).on("submit", "#main form", function() {
                $(this).find("input[name=_download]").remove();

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
          sections = env.menumanager.get_sections(env.request.user)
    %>
    % for section in sections:
        <% style = "" %>

        % if nameToPath(section) != env.request.web.path_elements[0] if len(env.request.web.path_elements) > 0 else "":
            <% style="display:none;" %>
        % endif

        <ul style="${style}" class="nav nav-tabs topmenu_section" id="topmenu_${ nameToPath(section) }">
        % for name, views in sections.get(section).items():
            <%
            class_ = ""
            firstview = builtins.next(builtins.iter(views.values()))
            %>

            % if env.request.user and not env.request.user.has(firstview.view_permissions):
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
    menus = env.menumanager.get_menus(env.request.user)
%>

% if env.request.user:
    <ul id="top_view_navbar_menu" class="nav navbar-nav navbar-primary">
    % for name, menu_item in menus.items():
        <li class="dropdown">
            <a class="dropdown-toggle" data-toggle="dropdown">
                % if menu_item.icon:
                    <i class="fa fa-${ menu_item.icon }"></i>
                % endif
                ${ _(name) }
                <span class="caret"></span>
            </a>
            <ul class="dropdown-menu" role="menu">
            % for section in menu_item.entries:
                % if section.views:
                    % if len(section.views) == 1:
                <li>
                    <a href="${ url_for(section.views[0].view_endpoint) }">
                    % if section.icon:
                        <i class="fa fa-${section.icon}"></i>
                    % endif
                        ${ _(section.name) }
                    </a>
                </li>
                    % else:
                <li class="dropdown dropdown-submenu">
                    <a class="dropdown-toggle" data-toggle="dropdown">
                    % if section.icon:
                        <i class="fa fa-${section.icon}"></i>
                    % endif
                        ${ _(section.name) }
                    </a>
                    <ul class="dropdown-menu">
                    % for view in section.views:
                        <li><a href="${ url_for(view.view_endpoint) }">${ _(view.view_menu[-1]) }</a></li>
                    % endfor
                    </ul>
                </li>
                    % endif
                % else:
                <li class="disabled" title="${ _('This app has been disabled or failed to load.') }"><a>
                    % if section.icon:
                    <i class="fa fa-${section.icon}"></i>
                    % endif
                    ${ _(section.name) }
                </a></li>
                % endif
            % endfor
            % if menu_item.default:
                <li role="separator" class="divider"></li>
                <li><a class="widget-link" title="${ _("About") }" href="${ url_for('About.render') }">${ _("About") }</a></li>
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
