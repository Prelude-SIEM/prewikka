<%inherit file="/prewikka/templates/toplayout.mak" />

<%block name="toplayout_content">
<script type="text/javascript">
"use strict";

function check_same_origin(url) {
    if ( typeof(url) == 'string' ) {
        var obj = document.createElement("a");
        obj.href = url;
        url = obj;
    }

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
    var default_port = {"http:": "80", "https:": "443"};
    return url.protocol == location.protocol && url.hostname == location.hostname && (url.port || default_port[url.protocol]) == (location.port || default_port[location.protocol]);
}

$(function() {
        % if not(context.get("is_error_template")):
            prewikka_ajax({ url: window.location.pathname + window.location.hash,
                            data: "${env.request.web.get_query_string() | n}",
                            type: "${env.request.web.method}",
                            prewikka: { target: PrewikkaAjaxTarget.TAB }
            });
        % endif

        /*
         * Back/Forward support.
         */
        $(window).on("popstate", function(e) {
                if ( e.originalEvent.state == null )
                        return;

                prewikka_ajax({url: e.originalEvent.state, prewikka: { history:false, target: PrewikkaAjaxTarget.TAB }});
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

                prewikka_ajax({ url: url, prewikka: { target: $(this).hasClass("no-widget") ? PrewikkaAjaxTarget.TAB : PrewikkaAjaxTarget.AUTO }});
                return false;
        });

        $(document).on("submit", "body form", function(event) {
                var form = this;
                var multipart = $(this).attr("enctype") == "multipart/form-data";
                var data = multipart ? new FormData(this) : $(this).serializeArray();
                var orig = $($(this).data("clicked"));

                if ( event.isDefaultPrevented() )
                    return;

                if ( $(form).triggerHandler("submit-prepare", [form, data]) == false )
                    return false;

                if ( orig.length ) {
                    $(this).removeData("clicked");

                    /*
                     * FIXME: is this still in use ?
                     */
                    if ( orig.attr("name") && orig.val() )
                        data.push({ name: orig.attr("name"), value: orig.val() });
                }

                var options = {
                        url: (orig && orig.attr("formAction")) || $(this).attr("action"),
                        type: (orig && orig.attr("formMethod")) || $(this).attr("method"),
                        data: data,
                        prewikka: { target: $(this).hasClass("no-widget") ? PrewikkaAjaxTarget.TAB : PrewikkaAjaxTarget.AUTO },
                        success: function() {
                              $("form").trigger("submit-success", [form, data]);

                              /* Close the modal potentially containing the form. */
                              $(form).closest(".modal").modal('hide');
                        },
                        error: function() {
                              $("form").trigger("submit-error", [form, data]);
                        },
                        complete: function() {
                              $("form").trigger("submit-complete", [form, data]);
                        },
                };
                if ( multipart ) {
                    options.processData = false;
                    options.contentType = false;
                }
                prewikka_ajax(options);

                return false;
        });

        $(document).on("click", ":input[type=submit]", function(e) {
                $(this.form).data("clicked", $(e.target));
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
        <ul style="display:none;" class="nav nav-tabs topmenu_section" data-section-title="${ _(section) }">
        % for tab, (endpoint, kwargs) in sections[section].items():
            <%
            view = env.viewmanager.get_view(endpoint=endpoint)
            if not(view.check_permissions(env.request.user, view_kwargs=kwargs)):
                continue
            %>

            <li role="presentation" class="topmenu_item"><a href="${ url_for(view.view_endpoint, **kwargs) }" class="topmenu_links no-widget">${_(tab)}</a></li>
        % endfor
        </ul>
    % endfor
    </div>
  </div>

  <div id="topmenu_right">
    <button type="button" class="btn btn-info btn-sm prewikka-config-button" title="${ _('View options') }" data-toggle="collapse" data-target=".prewikka-view-config" disabled>
      <i class="fa fa-cog fa-lg fa-fw"></i>
    </button>
    <button type="button" class="btn btn-info btn-sm prewikka-help-button" title="${ _('View help') }" disabled>
      <i class="fa fa-question fa-lg fa-fw"></i>
    </button>
  </div>

</div>
</%block>

<%block name="toplayout_menu">

<%
menus = {}
if env.menumanager:
    menus = env.menumanager.get_menus()
    sections = env.menumanager.get_sections()
    declared_sections = env.menumanager.get_declared_sections()

def _merge_tabs(section):
    if section["name"] not in sections:
        return section["tabs"]

    ret = []
    tabs = section["tabs"] + [tab for tab in sections[section["name"]] if tab not in section["tabs"]]
    for tab in tabs:
        if tab not in sections[section["name"]]:
            ret.append(tab)
            continue

        endpoint, kwargs = sections[section["name"]][tab]
        view = env.viewmanager.get_view(endpoint=endpoint)
        if view.check_permissions(env.request.user, view_kwargs=kwargs):
            ret.append(tab)

    return ret

def _get_view_url(section, tabs):
    if section not in sections:
        return

    for tab in tabs:
        if tab not in sections[section]:
            continue

        endpoint, kwargs = sections[section][tab]
        return url_for(endpoint, **kwargs)
%>

<%def name="write_menu(obj, section, tabs)">
    <% url = _get_view_url(section, tabs) %>

    % if url:
    <li>
        <a href="${ url }" class="no-widget">
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
        <ul class="dropdown-menu dropdown-menu-theme">
            % for section, tabs, name in sections:
            ${write_menu({"name": name}, section, tabs)}
            % endfor
        </ul>
    </li>
</%def>

<%def name="write_section(section, tabs=None)">
    <% tabs = tabs or _merge_tabs(section) %>
    % if tabs:
        % if not section.get("expand"):
            ${write_menu(section, section["name"], tabs)}
        % else:
            ${write_menu_expand(section, [(section["name"], [tab], tab) for tab in tabs])}
        % endif
    % endif
</%def>

<%def name="write_category(category)">
    <% sections = [] %>
    % for section in category["sections"]:
        <% tabs = _merge_tabs(section) %>
        % if tabs:
            <% sections.append((section["name"], tabs, section["name"])) %>
        % endif
    % endfor
    % if sections:
        ${write_menu_expand(category, sections)}
    % endif
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

            <ul class="dropdown-menu dropdown-menu-theme" role="menu">
            % for category in menu["categories"]:
                % if "name" in category:
                    ${write_category(category)}
                % else:
                    % for section in category["sections"]:
                        ${write_section(section)}
                    % endfor
                % endif
            % endfor
            % if menu.get("default"):

            ## Put the sections not declared in the YAML file into the default menu
            % for name in set(sections) - set(declared_sections):
                ${write_section({"name": name, "tabs": []})}
            % endfor

                <li role="separator" class="divider"></li>
                <% url = url_for('About.about', _default=None) %>
                % if url:
                <li><a href="${ url }">${ _("About") }</a></li>
                % endif
                % if env.session.can_logout():
                <li><a id="logout" class="ajax-bypass" href="${ url_for('BaseView.logout') }" data-confirm="${ _("Are you sure you want to log out?") }">${ _("Logout") }</a></li>
                % endif
            % endif
            </ul>
        </li>
    % endfor
    </ul>
% endif
</%block>

<%block name="main_content">
    <div id="ajax-spinner" class="ajax-spinner main-spinner" style="display:none;">
        <i class="fa fa-circle-o-notch fa-5x fa-spin"></i>
    </div>
    <div id="main" class="content prewikka-resources-container">
     <%block name="content"></%block>
    </div>
</%block>
