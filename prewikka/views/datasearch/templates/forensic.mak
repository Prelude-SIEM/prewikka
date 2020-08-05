<%!
  import itertools
  from prewikka import hookmanager, utils
%>

<%
    labels = dict((label, _(label)) for label in (
        N_("Fields"),
        N_("Query history")
    ))
%>

% for resource in extra_resources:
  ${resource}
% endfor

<script type="text/javascript">
$LAB.script("datasearch/js/datasearch.js").wait(function() {
  datasearch_autocomplete_init(${ html.escapejs(list(fields_info.keys())) },
                            ${ html.escapejs(history) },
                            ${ html.escapejs(labels) });

  var groupby = $(".form-control-select2");
  groupby.closest(".form-group").show();
  groupby.select2_container();
  var page = DataSearchPage("${backend}", ${html.escapejs(criterion_config)}, ${html.escapejs(criterion_config_default)}, ${html.escapejs(separators)}, "${url_for('.ajax_timeline')}", ${html.escapejs(common_paths)});

  % if search.groupby:
    var columns = {
        'model': [
            % for field in search.groupby:
            {name: "${ field }", label: "${ _(common_paths.get(field, field)) }", align: "center"},
            % endfor
            {name: "_aggregation", label: "${ _('Count') }", align: "center"},
        ]
    };

    $(document).ready(function() {
        page.groupby('#datasearch_groupby_table', columns, "${url_for('.ajax_groupby')}", {limit: ${html.escapejs(search.limit)}});
    });

  % else:
    <%
      model = []
      for prop in columns_properties.values():
          prop = utils.AttrObj(**prop)
          prop.label = _(prop.label)
          model.append(prop)
    %>

    var columns = {
        'model': ${ html.escapejs(model) },
        'subgrid': true
    };

    $(document).ready(function() {
        page.listing('#datasearch_table', columns, "${url_for('.ajax_table')}", ${html.escapejs(env.request.parameters['jqgrid_params_datasearch_table'])});
        $("#datasearch_table").jqGrid($("#view-config-editable").prop("checked") ? 'showCol' : 'hideCol', 'cb');
    });
  % endif

  prewikka_resource_register({
      destroy: function() {
          $("select.form-control-select2").select2('destroy');
          $("#input_search").myautocomplete('destroy');
      },
      container: "#datasearch"
  });
});
</script>

<div id="datasearch" class="container-fluid">

<form id="form_search" method="POST" action="${ utils.iri2uri(env.request.web.get_uri()) }">

  <div id="prewikka-view-config-datasearch" class="prewikka-view-config collapse">
      <div>
          <div class="form-group">
              <label for="chart_type_select">${_("Chart type")}</label>
              <select class="form-control input-sm" name="chart_type" id="chart_type_select">
              % for type in available_types:
                  <option ${selected(type == chart_type)}>${type}</option>
              % endfor
              </select>
          </div>

          % if search.groupby:
          <div class="form-group">
              <label for=view-config-limit>${_("Limit")}</label>
              <select class="form-control input-sm" id="view-config-limit" name="limit">
              % for available_limit in [10, 30, 50, 100]:
                  <option ${selected(available_limit == limit)}>${available_limit}</option>
              % endfor
              </select>
          </div>
          % endif

          <%block name="extra_datasearch_parameters"/>

          % if not search.groupby:
          <div>
            <label for="view-config-editable">
              <input type="checkbox" id="view-config-editable" ${ checked(env.request.parameters.get("editable")) } />
              <input type="hidden" name="editable" value="${env.request.parameters.get('editable')}" />
              ${ _("Action mode") }
            </label>
          </div>
          <div>
            <label for="view-config-condensed">
              <input type="checkbox" id="view-config-condensed" ${ checked(env.request.parameters.get("condensed")) } />
              <input type="hidden" name="condensed" value="${env.request.parameters.get('condensed')}" />
              ${ _("Condensed mode") }
            </label>
          </div>
          % if expert_enabled:
          <div>
            <label for="view-config-expert">
              <input type="checkbox" id="view-config-expert" ${ checked(env.request.parameters.get("expert")) } />
              <input type="hidden" name="expert" value="${env.request.parameters.get('expert')}" />
              ${ _("Expert mode") }
            </label>
          </div>
          % endif
          % endif
      </div>
  </div>

  <div class="row">
    <div class="col-md-9">
      <div id="datasearch_search_bar" class="default-background form-group">
        <div class="input-group">
          <span class="input-group-btn">
           <a class="btn btn-default datasearch-mode ${'disabled' if len(criterion_config) < 2 else ''}" title="${ _("Search mode") }">${ criterion_config_default.capitalize() }</a>
           <input type="hidden" name="query_mode" value="${ criterion_config_default }" />
          </span>

          <input id="input_search" type="text" name="query" class="form-control" placeholder="${ _("Search") }" value="${ search.query }">
          <span class="input-group-btn">
            <button class="btn btn-default datasearch-refresh" type="submit" title="${ _("Reset search") }"><i class="fa fa-undo"></i></button>
            <button class="btn btn-primary" type="submit"><i class="fa fa-search"></i></button>
          </span>
        </div>
      </div>
    </div>

    <div class="col-md-3">
      <div id="datasearch_groupby" class="form-group" style="display: none;">
        <div class="input-group">
          <span class="input-group-addon">${ _("Group by") }</span>
          <select class="form-control form-control-select2" multiple name="groupby[]" data-placeholder="${ _("Select your field") }">
            <optgroup label="${ _("Time values") }">
              % for field in groupby_tempo:
              <option ${ selected(field in search.groupby) } value="${ field }">${ _(field) }</option>
              % endfor
            </optgroup>
            <optgroup label="${ _("%s fields") % backend.capitalize() }">
              % for field,unused in filter(lambda x: x[1].groupable, fields_info.items()):
              <option ${ selected(field in search.groupby) } value="${ field }">${ _(field) }</option>
              % endfor
            </optgroup>

            % for field in search.groupby:
              % if field not in groupby_tempo and field not in fields_info:
                <option selected="selected" value="${ field }">${ _(field) }</option>
              % endif
            % endfor
          </select>
        </div>
      </div>
    </div>
  </div>

% if search.groupby:
<div class="row">
   <% chart = search.diagram(cview=".forensic") %>
   <div class="col-md-6">
       <table class="table table-striped commonlisting" id="datasearch_groupby_table"></table>
   </div>
   <div class="col-md-6">
       ${ chart['html'] }
       <script type="text/javascript">
         ${ chart['script'] }
       </script>
   </div>
</div>
% else:
  <div class="row">
    <div class="col-md-12">
      <div class="panel panel-default">
        <% timeline = env.request.parameters.get('timeline') %>
        <div class="panel-heading">
          <h4 class="panel-title">
            <a data-toggle="collapse" href="#timeline" class="timeline-toggle"><i class="fa ${'fa-minus' if timeline else 'fa-plus' }"></i>${ _("Timeline") }</a>
          </h4>
        </div>
        <div id="timeline" class="panel-collapse collapse ${'in' if timeline else ''}">
          <div>
            <input type="hidden" name="timeline" value="${ timeline }"/>
            <div id="timeline_results" class="prewikka-resources-container"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
% endif

</form>

% if not search.groupby:
<div class="row">
  <div class="col-md-12">
    <table id="datasearch_table"></table>
  </div>
</div>

<div class="footer-buttons collapse fade ${'in' if env.request.parameters.get('editable') else ''}">
  <form id="datasearch_grid_form">
    <input type="hidden" value="${ json.dumps(search.all_criteria) }" name="datasearch_criteria"/>
  </form>
  <form id="datasearch_export_form" method="post">
    <input type="hidden" value="${ json.dumps(search.all_criteria) }" name="datasearch_criteria"/>
  </form>

  <div class="form-inline">
  <%
  _sentinel = object()
  prev_sortkey = _sentinel
  %>
  % for obj in sorted(actions):
      % if prev_sortkey is not _sentinel and prev_sortkey != obj._sortkey:
        <span>|</span>
      % endif
      <% prev_sortkey = obj._sortkey %>
      ${ obj }
  % endfor
  </div>
</div>

<div id="PopoverOption" class="popover-options">
  <ul class="popover dropdown-menu dropdown-menu-theme multi-level" role="menu" aria-labelledby="dropdownMenu">
    <div class="arrow"></div>
    <li class="dropdown-submenu">
      <a>${ _("Search") }</a>
      <ul class="dropdown-menu dropdown-menu-theme">
        <li><a class="add_search">${ _("Add to search") }</a></li>
        <li><a class="del_search">${ _("Exclude from search") }</a></li>
        <li><a class="new_search">${ _("New search") }</a></li>
        <li><a class="groupby_search">${ _("Group by") } <span></span></a></li>
      </ul>
    </li>

    <%
      links = list(env.linkmanager.get_links(arg="$value"))
    %>
    % if links:
    <li class="dropdown-submenu">
      <a>${ _("Actions") }</a>
      <ul class="dropdown-menu dropdown-menu-theme">
        % for link in links:
        <li>${ link.to_string(_class="addon_search") }</li>
        % endfor
        % for obj in itertools.chain(hookmanager.trigger("HOOK_DATASEARCH_LINK"), hookmanager.trigger("HOOK_DATASEARCH_%s_LINK" % backend.upper())):
        <li>${ obj.to_string(_class="addon_search") }</li>
        % endfor
      </ul>
    </li>
    % endif

    <li class="dropdown-submenu oca-infos">
      <a>${ _("Informations") }</a>
      <div class="dropdown-menu dropdown-menu-theme panel panel-default">
        <div class="ajax-spinner hidden">
          <i class="fa fa-circle-o-notch fa-3x fa-spin"></i>
        </div>
        <div class="processed-content">
          <div class="panel-heading"></div>
          <div class="panel-body">
            <ul class="nav nav-pills nav-justified" role="tablist"></ul>
            <div class="tab-content"></div>
          </div>
        </div>
      </div>
    </li>
  </ul>
</div>
% endif

</div>
