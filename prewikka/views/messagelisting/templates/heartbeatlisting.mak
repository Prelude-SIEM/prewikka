<%inherit file="/prewikka/views/messagelisting/templates/messagelisting.mak" />

<%block name="message_fields_header">
<thead>
<tr>
<td class="filtered_column">
  <div>${ _("Agent") }</div>
  % if name_filtered:
    <span>*</span>
  % endif
</td>

<td class="filtered_column">
  <div>${ _("Node address") }</div>
  % if address_filtered:
    <span>*</span>
  % endif
</td>

<td class="filtered_column">
  <div>${ _("Node name") }</div>
  % if node_name_filtered:
    <span>*</span>
  % endif
</td>

<td class="filtered_column">
  <div>${ _("Model") }</div>
  % if model_filtered:
    <span>*</span>
  % endif
</td>

<td>${ _("Date") }</td>

% if messages and env.request.user.has("IDMEF_ALTER"):
<td><input class="checkbox" type="checkbox" id="allbox" /></td>
% endif

</tr>

</thead>
</%block>

<%def name="message_fields(message)">
<td>
  <a class="popup_menu_toggle">${ message['agent']['value'] }</a>
  <span class="popup_menu">
   % if message['summary']:
    <a href="${ message['summary'] }" title="${ _('Heartbeat details') }" class="widget-link">${ _("See heartbeat details") }</a>
   % endif
   <a href="${ message['agent']['inline_filter'] }">${ _("Filter on agent") }</a>
  </span>
</td>

<td>
  %if len(message["node.address(*).address"]) > 0:
    % for address in message["node.address(*).address"]:
    <a class="popup_menu_toggle">${ address.value }</a>
    <span class="popup_menu">
      <a href="${ address['inline_filter'] }">${ _("Filter on address") }</a>
      % if env.enable_details:
      <a target="${ env.external_link_target }" href="${ env.host_details_url }?host=${ address['value'] }">Address information</a>
      % endif
      % for name, link, widget in address['host_links']:
      % if widget:
       <a href="${ link }" class="widget-link" title="${ name }">${ name }</a>
      % else:
       <a href="${ link }" target="_${ name }">${ name }</a>
      % endif
      % endfor
    </span>
    <br />
    % endfor
  % else:
    n/a
  % endif
</td>

<td>
 <a href="${ message["node.name"].inline_filter }">${ message["node.name"]['value'] }</a><br />
</td>

<td>
  <a href="${ message["model"].inline_filter }">${ message["model"].value }</a>
</td>

<td>${ message["time"].value }</td>
</%def>

<%block name="message_extra_footer">
  % if env.request.user.has("IDMEF_ALTER"):
  <div class="pull-right">
    <div class="form-inline">
      <input type="submit" class="btn btn-primary" name="listing_apply" value="${ _("Apply") }" data-confirm="${ _("Delete the selected heartbeats?") }" />
      <div class="form-group">
        <select class="form-control" name="action" id="action">
          <option value="delete_message">${ _('Delete') }</option>
        </select>
      </div>
    </div>
  </div>
  % endif
</%block>
