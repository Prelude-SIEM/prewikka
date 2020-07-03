<%!
from prewikka.utils import html, json
from prewikka.utils.html.helpers import POPOVER_HTML
%>

<link rel="stylesheet" type="text/css" href="agents/css/agents.css">

<script type="text/javascript">

    function statusAttr(rowId, value, rowObj) {
        var status_classes = {"online": "success", "offline": "default", "unknown": "warning", "missing": "danger"};
        return ' class="label-' + status_classes[rowObj.status] + '"';
    }

    function nameFormatter(cellValue, opts, rowObj) {
        var div = $("<div>");
        var span = $("<span>", {"class": "popup-menu"});
        $.each(rowObj.links, function(index, elem) {
            $(span).append(elem.toHTML());
        });
        $("<a>", {
            "data-toggle": "popover",
            "data-placement": "bottom",
            "data-html": "true",
            "data-content": span[0].outerHTML,
            "data-template": ${ html.escapejs(POPOVER_HTML) }
        }).text(cellValue).appendTo(div);
        return div.html();
    };

    var text = {'title': '<label class="label label-primary checkbox-inline global_toggle">${ _("Show/Hide all") }</label>', 'search': "${ _('Search:') }"};

    var grid = CommonListing('table#agents', text, {
        deleteLink: "${url_for('.delete')}",
        colModel: [
            {name: 'name', label: "${ _('Name') }", width: 15, formatter: nameFormatter},
            {name: 'location', label: "${ _('Location') }", width: 15},
            {name: 'label', label: "${ _('Node') }", width: 15},
            {name: 'model', label: "${ _('Model') }", width: 10, sortable: false},
            {name: 'version', label: "${ _('Version') }", width: 5, sortable: false},
            {name: 'class', label: "${ _('Class') }", width: 10, sortable: false},
            % for column in extra_columns:
            {name: '${ column.name }', label: '${ column.label }', width: 10, sortable: false},
            % endfor
            {name: 'latest_heartbeat', label: "${ _('Latest heartbeat') }", width: 10, sortable: false},
            {name: 'status_text', label: "${ _('Status') }", width: 5, sortable: false, align: 'center', classes: 'heartbeat_analyze', cellattr: statusAttr}
        ],
        data: ${ html.escapejs(data) },
        globalSearch: true,
        grouping: true,
        groupingView: {
            groupField: ["location", "label"],
            groupColumnShow: [false, false],
            groupText: ['<b>{0}</b> ({1} agent(s))', '<b>{0}</b> ({1} agent(s))'],
            groupCollapse: false,
            groupOrder: ['asc', 'asc'],
            groupSummary: [false, false]
        }
    }, ${html.escapejs(env.request.parameters["jqgrid_params_agents"])});

    $(".global_toggle").on("click", function() {
        if ( $("#agents .fa-plus-square-o").length > 0 ) {
            $("#agents .fa-plus-square-o").trigger("click");
            $("#agents .fa-plus-square-o").trigger("click");
        }
        else {
            $("#agents .fa-minus-square-o").trigger("click");
        }
    });

    $(".agent-delete").on("click", function() {
        if ( $(this).data("confirm") )
            return;

        var seltypes = $.map($("input[name='types[]']:checked"), function(input) {
            return $(input).val();
        });

        if ( seltypes.length > 0 )
            grid.ajax({ url: "${url_for('.delete')}", data: { types: seltypes }});
    });

</script>

<table id="agents"></table>

  <div class="footer-buttons form-inline">
    <div class="checkbox">
      <input id="agent_delete_alerts" class="checkbox" type="checkbox" name="types[]" value="alert" />
      <label for="agent_delete_alerts" data-toggle="tooltip" title="${ _("Delete the alerts of the selected agent(s)") }" data-container="#main">${ _("Alerts") }</label>
    </div>
    <div class="checkbox">
      <input id="agent_delete_heartbeats" class="checkbox" type="checkbox" name="types[]" value="heartbeat" />
      <label for="agent_delete_heartbeats" data-toggle="tooltip" title="${ _("Delete the heartbeats of the selected agent(s)") }" data-container="#main">${ _("Heartbeats") }</label>
    </div>
    &nbsp;<button type="button" class="btn btn-danger needone agent-delete" data-confirm="${ _("Delete the selected IDMEF messages?") }"><i class="fa fa-trash"></i> ${ _("Delete") }</button>
  </div>
