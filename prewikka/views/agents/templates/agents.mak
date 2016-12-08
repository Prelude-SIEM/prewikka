<%!
from prewikka.utils import json
%>

<link rel="stylesheet" type="text/css" href="agents/css/agents.css">

<script type="text/javascript">

    function statusAttr(rowId, value, rowObj) {
        var status_classes = {"online": "success", "offline": "default", "unknown": "warning", "missing": "danger"};
        return ' class="label-' + status_classes[rowObj.status] + '"';
    }

    function nameFormatter(cellValue, opts, rowObj) {
        var div = $("<div>");
        $("<a>", {"class": "popup_menu_toggle"}).text(cellValue).appendTo(div);
        var span = $("<span>", {"class": "popup_menu"}).appendTo(div);
        $.each(rowObj.links, function(index, elem) {
            $("<a>", {
                href: elem.link,
                class: elem.class,
                title: elem.title
            }).text(elem.text).appendTo(span);
        });
        return div.html();
    };

    var text = {'title': "${ _('Agents') }", 'search': "${ _('Search:') }"};

    var grid = CommonListing('table#agents', text, {
        colNames: ["${ _('Name') }", "${ _('Location') }", "${ _('Node') }", "${ _('Model') }", "${ _('Version') }", "${ _('Class') }",
                % for column in extra_columns:
                   "${ column.label }",
                % endfor
                   "${ _('Latest heartbeat') }", "${ _('Status') }"],
        colModel: [
            {name: 'name', width: 15, formatter: nameFormatter},
            {name: 'location', width: 15},
            {name: 'label', width: 15},
            {name: 'model', width: 10, sortable: false},
            {name: 'version', width: 5, sortable: false},
            {name: 'class', width: 10, sortable: false},
            % for column in extra_columns:
            {name: '${ column.name }', width: 10, sortable: false},
            % endfor
            {name: 'latest_heartbeat', width: 10, sortable: false},
            {name: 'status_text', width: 5, sortable: false, align: 'center', classes: 'heartbeat_analyze', cellattr: statusAttr}
        ],
        data: ${ data | n,json.dumps },
        globalSearch: true,
        grouping: true,
        groupingView: {
            groupField: ["location", "label"],
            groupColumnShow: [false, false],
            groupText: ['<b>{0}</b> ({1} agents)', '<b>{0}</b> ({1} agents)'],
            groupCollapse: false,
            groupOrder: ['asc', 'asc'],
            groupSummary: [false, false]
        }
    });

    $(".global_toggle").on("click", function() {
        if ( $("#agents .ui-icon-circlesmall-plus").length > 0 ) {
            $("#agents .ui-icon-circlesmall-plus").trigger("click");
            $("#agents .ui-icon-circlesmall-plus").trigger("click");
        }
        else {
            $("#agents .ui-icon-circlesmall-minus").trigger("click");
        }
    });

    $("form").on("submit", function() {
        var form = this;
        var rows = grid.getGridParam("selarrrow");
        if ( rows.length == 0 || $(this).data("confirm") ) return;

        $.each(rows, function(index, row) {
            $("<input>", {"type": "hidden", "name": "analyzerid", "value": row}).appendTo(form);
        });
    });

</script>

<table id="agents"></table>

<button type="button" class="btn btn-default btn-sm global_toggle">${ _("Show/Hide all") }</button>

<form action="${ url_for(".delete") }" method="post">

  <div class="footer-buttons form-inline">
    <div class="checkbox">
      <input id="agent_delete_alerts" class="checkbox" type="checkbox" name="types" value="alert" />
      <label for="agent_delete_alerts">${ _("Alerts") }</label>
    </div>
    <div class="checkbox">
      <input id="agent_delete_heartbeats" class="checkbox" type="checkbox" name="types" value="heartbeat" />
      <label for="agent_delete_heartbeats">${ _("Heartbeats") }</label>
    </div>
    &nbsp;<button class="btn btn-danger needone" type="submit" value="${ _("Delete") }" data-confirm="${ _("Delete the selected IDMEF messages?") }"><i class="fa fa-trash"></i> ${ _("Delete") }</button>
  </div>

</form>
