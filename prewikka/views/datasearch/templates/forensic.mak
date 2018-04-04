<%namespace file="/prewikka/views/datasearch/templates/table.mak" import="GroupbyTable"/>
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

<link rel="stylesheet" type="text/css" href="prewikka/css/bootstrap-chosen.css">

<script type="text/javascript">
$LAB.script("datasearch/js/datasearch.js").wait(function() {
  datasearch_autocomplete_init(${ html.escapejs(fields_info.keys()) },
                            ${ html.escapejs(history) },
                            ${ html.escapejs(labels) });

  $(".form-control-chosen").chosen({ width: "100%", search_contains: true });
    DataSearchPage("${backend}", ${html.escapejs(criterion_config)}, ${html.escapejs(criterion_config_default)}, "${url_for('.ajax_timeline')}");

  % if not search.groupby:
    <%
      for i in columns_properties:
         columns_properties[i].label = _(columns_properties[i].label)
    %>

    var columns = {
        'model': ${ html.escapejs(columns_properties.values()) },
        'subgrid': true
    };

    $(document).ready(function() {
        DataSearchListing('#datasearch_table', columns, "${url_for('.ajax_table')}", ${limit}, ${html.escapejs(env.request.parameters['jqgrid_params_datasearch_table'])});
        $("#datasearch_table").jqGrid($("#view-config-editable").prop("checked") ? 'showCol' : 'hideCol', 'cb');
    });
  % endif

  prewikka_resource_register({
      destroy: function() {
          $(".form-control-chosen").chosen('destroy');
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
          <div class="form-group">
              <label for=view-config-limit>${_("Limit")}</label>
              <select class="form-control input-sm" id="view-config-limit" name="limit">
              % for available_limit in [10, 30, 50, 100]:
                  <option ${selected(available_limit == limit)}>${available_limit}</option>
              % endfor
              </select>
          </div>

          <%block name="extra_datasearch_parameters"/>

          <div class="form-group">
            <label for="view-config-editable">
              ${ _("Expert mode") }
              <input type="checkbox" id="view-config-editable" ${ checked(env.request.parameters.get("editable")) } />
              <input type="hidden" name="editable" value="${env.request.parameters.get('editable')}" />
            </label>
          </div>
          <div class="form-group">
            <label for="view-config-condensed">
              ${ _("Condensed mode") }
              <input type="checkbox" id="view-config-condensed" ${ checked(env.request.parameters.get("condensed")) } />
              <input type="hidden" name="condensed" value="${env.request.parameters.get('condensed')}" />
            </label>
          </div>
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
      <div class="form-group">
        <div class="input-group">
          <span class="input-group-addon">${ _("Group by") }</span>
          <select class="form-control form-control-chosen" multiple name="groupby[]" data-placeholder="${ _("Select your field") }">
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
   <div class="col-md-4">
       ${ GroupbyTable(search) }
   </div>
   <div class="col-md-8">
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
        <div class="panel-heading">
          <h4 class="panel-title">
            <a data-toggle="collapse" href="#timeline">${ _("Timeline") }</a>
          </h4>
        </div>
        <div id="timeline" class="panel-collapse collapse ${'in' if env.request.parameters.get('timeline') else ''}">
          <div>
            <input type="hidden" name="timeline" value="${ env.request.parameters.get('timeline') }"/>
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
  <form id="datasearch_export_form">
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

<div id="PopoverOption" class="popover-options" style="display:none">
    <div class="popover">
        <div class="arrow"></div>
        <ul class="list-group">
          <a class="list-group-item add_search default_search">${ _("Add to search") }</a>
          <a class="list-group-item del_search default_search">${ _("Exclude from search") }</a>
          <a class="list-group-item new_search default_search">${ _("New search") }</a>
          <a class="list-group-item groupby_search">${ _("Group by") } <span></span></a>
          % for obj in itertools.chain(hookmanager.trigger("HOOK_DATASEARCH_LINK"), hookmanager.trigger("HOOK_DATASEARCH_%s_LINK" % backend.upper())):
            ${ obj.to_string(_class="list-group-item addon_search") }
          % endfor
        </ul>
        <%
          path_list = list(hookmanager.trigger("HOOK_PATH_LINK"))
        %>
        % if path_list:
          <div class="arrow"></div>
          <ul class="list-group">
            % for path, func in path_list:
            ${ func.to_string(_class="list-group-item addon_search") }
            % endfor
          </ul>
        % endif
    </div>
</div>
% endif

</div>
