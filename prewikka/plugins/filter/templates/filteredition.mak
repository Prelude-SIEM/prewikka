<%!
    from collections import OrderedDict
    from prewikka.dataprovider import OPERATORS
%>

<%namespace file="/prewikka/plugins/filter/templates/widget.mak" import="init, condition, group"/>

<%
    tooltips = {op: _(label) for op, label in OPERATORS.items()}
    default_paths = {}
    all_paths = {}
    operators = {}
    enums = {}

    for typ, label in types:
        default_paths[typ] = OrderedDict((_(label), path) for label, path in env.dataprovider.get_common_paths(typ))
        all_paths[typ] = []
        operators[typ] = {}
        enums[typ] = {}
        for path in env.dataprovider.get_paths(typ):
            path_info = env.dataprovider.get_path_info(path, typ)
            operators[typ][path] = path_info.operators
            enums[typ][path] = None if not path_info.value_accept else [v.value for v in path_info.value_accept]

            if path not in default_paths[typ].values():
                all_paths[typ].append(path)
%>


<div class="container">
  <div class="widget ui-front" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="false" data-draggable="true" data-widget-options="modal-lg">

    <link rel="stylesheet" type="text/css" href="filter/css/filter.css">

    <script type="text/javascript">
    $LAB.script("filter/js/filter.js").wait(function() {
        $("#filter_category").select2_container({
            tags: true
        });

        $(".filter-form .modal-body").on("scroll", function() {
            $(".dropdown-fixed.open").find("[data-toggle=dropdown]").dropdown("toggle");
        });
        $(".type-checkbox").on("change", function() {
            $(this).closest(".panel-heading").siblings(".panel-body").slideToggle();
        });

        $("a.type-toggle").on("click", function() {
            $(this).siblings(".type-checkbox").click();
        });

        new FilterEdition("form.filter-form",
                          ${html.escapejs(default_paths)},
                          ${html.escapejs(all_paths)},
                          ${html.escapejs(operators)},
                          ${html.escapejs(enums)},
                          ${html.escapejs(tooltips)}).init();

    });
    </script>

    <form class="filter-form" action="${url_for('FilterView.save', name=fltr.name)}" method="post">

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">&times;</button>
        <h5 class="modal-title">${ _("Filter %s") % fltr.name if fltr.name else _("New filter") }</h5>
      </div>

      <div class="modal-body">

        <div class="form-horizontal">
          <div class="form-group">
            <label for="filter_name" class="col-sm-2 control-label required">${ _("Name:") }</label>
            <div class="col-sm-10">
              <input class="form-control" type="text" id="filter_name" name="filter_name" value="${fltr.name}" placeholder="${ _("Filter name") }" required/>
            </div>
          </div>

          <div class="form-group">
            <label for="filter_category" class="col-sm-2 control-label">${ _("Category:") }</label>
            <div class="col-sm-10">
              <select class="form-control" id="filter_category" name="filter_category" value="${fltr.category}">
                <option value="">&nbsp;</option>
                % for category in categories:
                <option value="${ category }" ${ selected(category == fltr.category) }>${ category }</option>
                % endfor
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="filter_description" class="col-sm-2 control-label">${ _("Description:") }</label>
            <div class="col-sm-10">
              <input type="text" class="form-control" id="filter_description" name="filter_description" value="${fltr.description}">
            </div>
          </div>
        </div>

        %for typ, label in types:
        <div class="panel panel-theme">
            <% enabled = typ in fltr.criteria %>
            <div class="panel-heading">
                <h3 class="panel-title">
                    <input type="checkbox" class="type-checkbox" id="type-checkbox-${typ}" ${checked(enabled)}/>
                    <label for="type-checkbox-${typ}"><span class="badge"><a></a></span></label>
                    <a class="type-toggle" style="color: inherit">${label}</a>
                </h3>
            </div>
            <div class="panel-body ${'panel-disabled' if not enabled else ''}">
                <div class="filter-edition form-inline" data-type="${typ}">
                    <input type="hidden" name="filter_types[]" value="${typ}"/>
                    <input type="hidden" name="filter_criteria[]"/>
                    ${init(fltr.criteria.get(typ), root=True, default_paths=default_paths[typ], all_paths=all_paths[typ], operators=operators[typ], enums=enums[typ], tooltips=tooltips)}
                </div>
            </div>
        </div>
        % endfor

      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${ _("Cancel") }</button>
        <button type="submit" class="btn btn-primary"><i class="fa fa-save"></i> ${ _("Save") }</button>
      </div>

    </form>


    <div id="example-condition" style="display:none">
        ${condition()}
    </div>

    <div id="example-group" style="display:none">
        ${group(operands=[])}
    </div>

  </div>
</div>
