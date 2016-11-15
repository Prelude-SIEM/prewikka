<link rel="stylesheet" type="text/css" href="agents/css/agents.css">

<%
 status_classes = {"online": "success", "offline": "default", "unknown": "warning", "missing": "danger"}
%>

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
    <tr><td>${ _("Events") }</td></tr>
  </thead>

  <tbody>
    % for event in analyzer.events:
      <tr>
        <td class="heartbeat_analyzer_event_${ event.type }">${ event.time }</td>
        <td class="heartbeat_analyzer_event_${ event.type }">${ event.value }</td>
      </tr>
    % endfor
  </tbody>
</table>
