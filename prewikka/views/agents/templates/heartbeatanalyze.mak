<%
 status_classes = {"online": "success", "offline": "default", "unknown": "warning", "missing": "danger"}
%>

<div class="container">
  <div class="widget" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="false" data-draggable="true" data-widget-options="modal-lg">

    <link rel="stylesheet" type="text/css" href="agents/css/agents.css">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">&times;</button>
      <h5 class="modal-title">${ _("Heartbeat analysis") }</h5>
    </div>

    <div class="modal-body">
      <table class="table table-striped table-bordered table-condensed">
        <thead>
          <tr>
            <td>${ _("Name") }</td>
            <td>${ _("Model") }</td>
            <td>${ _("OS") }</td>
            <td>${ _("Node name") }</td>
            <td>${ _("Node location") }</td>
            <td>${ _("Node address") }</td>
            <td>${ _("Latest heartbeat") }</td>
            <td>${ _("Current status") }</td>
          </tr>
        </thead>

        <tbody>
          <tr>
            <td>${ analyzer['name'] }</td>
            <td>${ analyzer['model'] } ${ analyzer['version'] }</td>
            <td>${ analyzer['ostype'] } ${ analyzer['osversion'] }</td>
            <td>${ analyzer['node.name'] }</td>
            <td>${ analyzer['node.location'] }</td>
            <td>
              % if len(analyzer["node.address(*).address"]):
                % for address in analyzer["node.address(*).address"]:
                  ${ address }<br/>
                % endfor
              % else:
                n/a
              % endif
            </td>
            <td>${ analyzer.last_heartbeat_time }</td>
            <td class="heartbeat_analyze label-${status_classes[analyzer.status]}">
              <b>${ analyzer.status_meaning }</b>
            </td>
          </tr>
        </tbody>
      </table>

      <table class="table table-striped table-bordered table-condensed">
        <thead>
          <tr><th colspan="2">${ _("Events") }</th></tr>
        </thead>

        <tbody>
          % for event in reversed(analyzer.events):
            <tr>
              <td class="heartbeat_analyzer_event_${ event.type }">${ event.time }</td>
              <td class="heartbeat_analyzer_event_${ event.type }">${ event.value }</td>
            </tr>
          % endfor
        </tbody>
      </table>
    </div>

    <div class="modal-footer">
      <button class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${ _('Close') }</button>
    </div>

  </div>
</div>
