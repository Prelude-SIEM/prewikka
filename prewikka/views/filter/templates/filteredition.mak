<%! from prewikka.utils import OrderedDict %>

<%namespace file="/prewikka/views/filter/templates/widget.mak" import="init, condition, group"/>

<%
    tooltips = {
        "=": _("Equal"),
        "=*": _("Equal (case-insensitive)"),
        "!=": _("Not equal"),
        "!=*": _("Not equal (case-insensitive)"),
        "~": _("Regular expression"),
        "~*": _("Regular expression (case-insensitive)"),
        "!~": _("Not regular expression"),
        "!~*": _("Not regular expression (case-insensitive)"),
        "<": _("Lesser than"),
        "<=": _("Lesser or equal"),
        ">": _("Greater than"),
        ">=": _("Greater or equal"),
        "<>": _("Substring"),
        "<>*": _("Substring (case-insensitive)"),
        "!<>": _("Not substring"),
        "!<>*": _("Not substring (case-insensitive)")
    }

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
            path_info = env.dataprovider.get_path_info(path)
            operators[typ][path] = path_info.operators
            enums[typ][path] = path_info.value_accept

            if path not in default_paths[typ].values():
                all_paths[typ].append(path)
%>


<link rel="stylesheet" type="text/css" href="prewikka/css/chosen.min.css">
<link rel="stylesheet" type="text/css" href="filter/css/filter.css">

<script type="text/javascript">
$LAB.script("filter/js/filter.js").script("prewikka/js/chosen.jquery.min.js").wait(function() {
    $(".type-checkbox").on("change", function() {
        $(this).closest(".panel-heading").siblings(".panel-body").slideToggle();
    });

    $("a.type-toggle").on("click", function() {
        $(this).siblings(".type-checkbox").click();
    });

    new FilterEdition("div.container",
                      ${default_paths | n,json.dumps},
                      ${all_paths | n,json.dumps},
                      ${operators | n,json.dumps},
                      ${enums | n,json.dumps},
                      ${tooltips | n,json.dumps}).init();

});
</script>

<div class="container">

<form class="filter-form" action="${url_for('FilterView.save')}" method="post">

    <div class="form-horizontal">
      <div class="form-group">
        <label for="filter_name" class="col-sm-2 control-label required">${ _("Name:") }</label>
        <div class="col-sm-10">
          <input class="form-control" type="text" id="filter_name" name="filter_name" value="${fltr.name}" placeholder="${ _("Filter name") }" required/>
        </div>
      </div>

      <div class="form-group">
        <label for="filter_description" class="col-sm-2 control-label">${ _("Description:") }</label>
        <div class="col-sm-10">
          <textarea class="form-control" id="filter_description" name="filter_description" rows="4">${fltr.description}</textarea>
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
                <input type="hidden" name="filter_types" value="${typ}"/>
                <input type="hidden" name="filter_criteria"/>
                ${init(fltr.criteria.get(typ), root=True, default_paths=default_paths[typ], all_paths=all_paths[typ], operators=operators[typ], enums=enums[typ], tooltips=tooltips)}
            </div>
        </div>
    </div>
    % endfor

    <button class="btn btn-primary widget-control" type="submit"><i class="fa fa-save"></i> ${ _("Save") }</button>

    <input type="hidden" name="filter_id" value="${fltr.name}">
</form>

</div>


<div id="example-condition" style="display:none">
    ${condition()}
</div>

<div id="example-group" style="display:none">
    ${group(operands=[])}
</div>
