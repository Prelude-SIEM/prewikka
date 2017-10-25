<%!
import prelude
from prewikka.utils import json
from prewikka import usergroup, utils, idmefbrowser
%>

<%inherit file="/prewikka/views/messagelisting/templates/messagelisting.mak" />

<%def name="sortable(link, field, current_order=None)">
<script>
$(".sortable_${ field }").on("click", function() {
    $(".hidden_order_by_input").remove();
    $("#main form").prepend('<input type="hidden" class="hidden_order_by_input" name="orderby" value="${ field + "_desc" if current_order and current_order == field + "_asc" else field + "_asc" }">');
    $("#main form").submit();
});
</script>

<a class="sortable_${ field }" data-toggle="tooltip" title="${ _("Order column") }" data-container="#main">${ link }</a>
    % if current_order == field + "_desc":
<span class="caret"></span>
    % elif current_order == field + "_asc":
<span class="dropup"><span class="caret"></span></span>
    % endif
</%def>


<%block name="messagelisting_scripts">

<script type="text/javascript" src="messagelisting/js/alertlisting.js"></script>

<script type="text/javascript">

var operators = {
        "!": "${ _("Not defined") }",
        "=": "${ _("Equal") }",
        "!=": "${ _("Not equal") }",
        "<": "${ _("Lesser than") }",
        ">": "${ _("Greater than") }",
        "<=": "${ _("Lesser or equal") }",
        ">=": "${ _("Greater or equal") }",
        "<>": "${ _("Substring") }",
        "<>*": "${ _("Substring (case-insensitive)") }",
        "~": "${ _("Regular expression") }",
        "~*": "${ _("Regular expression (case-insensitive)") }"
};

var stateArray = [ "default", "saved", "current" ];
var saved_forms = Array();
var columns_data = ${ html.escapejs(columns_data) };

var saved_state = columns_data["column_names"];
$(saved_state).each(function() {
        saved_forms[this] = [ "default", "saved", "current" ];
});

var messagelisting = new MessageListing(operators);

var stateText = {
        "null": "${ _("Reset to null") }",
        "default": "${ _("Reset to default") }",
        "saved": "${ _("Reset to saved") }",
        "current": "${ _("Reset to current") }"
};

$(saved_state).each(function(idx, type) {
        $(stateArray).each(function(idx, state) {
                messagelisting.set(type, state, columns_data);
                saved_forms[type][state] = messagelisting._cloneForm($("#" + type + " :input"));
        });

        var form = $("#" + type + " :input");
        saved_forms[type]["current"] = messagelisting._cloneForm(form);

        if ( messagelisting._equals(saved_forms[type]["default"], saved_forms[type]["saved"]) )
                saved_forms[type]["saved"] = null;

        if ( messagelisting._equals(saved_forms[type]["current"], saved_forms[type]["default"]) )
                saved_forms[type]["current"] = null;

        if ( messagelisting._equals(saved_forms[type]["current"], saved_forms[type]["saved"]) )
                saved_forms[type]["current"] = null;

        ## Set the current state
        $(stateArray).each(function(idx, state) {
                if ( messagelisting._equals(form, saved_forms[type][state]) )
                        saved_state[type] = state;
        });

        $("#" + type + " input.reset_filter").val(stateText[messagelisting.get_next_state(saved_forms, type, saved_state[type])]);
});


$("input.reset_filter").click(function() {
        var type = $(this).closest(".filter_popup").find("div").prop("id");

        saved_state[type] = messagelisting.get_next_state(saved_forms, type, saved_state[type]);

        messagelisting.set(type, saved_state[type], columns_data);
        $(this).val(stateText[messagelisting.get_next_state(saved_forms, type, saved_state[type])]);
});

</script>
</%block>

<%def name="define_inline_filter_options(rootcl, preselect, depth)">
        % if rootcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
         <option disabled="disabled" value="">${ depth * "&nbsp;" | n }${ rootcl.getName().capitalize() }</option>

          % for subcl in rootcl:
                ${ define_inline_filter_options(subcl, preselect, depth + 1) }
          % endfor

        % else:
           % if rootcl.getPath() in checkbox_fields:
                <% return "" %>
           % endif

           <%
             oplist = idmefbrowser.getOperatorList(rootcl.getValueType())
             is_enum = rootcl.getValueType() == prelude.IDMEFValue.TYPE_ENUM
           %>

           % if is_enum or oplist:
           <script type="text/javascript">
            % if is_enum:
            messagelisting.value_array["${ rootcl.getPath() }"] = ${ html.escapejs(list(rootcl.getEnumValues())) };
            % endif
            % if oplist:
            messagelisting.operator_array["${ rootcl.getPath() }"] = ${ html.escapejs(oplist) };
            % endif
           </script>
           % endif

           % if rootcl.getPath() == None:
            <option disabled="disabled" value="">${ depth * "&nbsp;" | n } ${ rootcl.getName().capitalize() }</option>

           % elif rootcl.getPath() == preselect:
            <option value="${ rootcl.getPath() }" selected="selected">${ depth * "&nbsp;" | n }${ rootcl.getName() }</option>

           % else:
            <option value="${ rootcl.getPath() }">${ depth * "&nbsp;" | n }${ rootcl.getName() }</option>
           % endif
        % endif
</%def>

<%def name="define_inline_filter(obname, preselect)">
      <table class="inline_filter_content filter_table">
       <tr class="inline_filter">
        <th>${ _('Filter on') } [<a class="expert_mode">${ _("advanced") }</a>]:</th>
        <td class="td_container_path">
         <input type="hidden" name="${obname}_object_0" value="__all__" />
         <select style="display:none;" disabled="disabled" class="popup_select_field form-control input-sm" name="${obname}_object_0">
            % for i in all_filters[obname]:
             ${ define_inline_filter_options(i, preselect, 0) }
            % endfor
           </select>
        </td>

        <td class="td_container_operator">
         <select style="display:none;" class="popup_operator_select form-control input-sm" name="${obname}_operator_0" />
        </td>

        <td class="td_container_value">
         <input class="popup_input_field form-control input-sm" type="text" name="${obname}_value_0" />
        </td>

        <td class="td_container_remove"><a class="fa fa-minus" style="visibility: hidden"></a></td>
        <td class="td_container_add"><a class="append_entry fa fa-plus"></a></td>
       </tr>
      </table>
</%def>

<%def name="define_inline_aggreg_options(rootcl, depth)">
        % if rootcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
        <option disabled="disabled" value="">${ depth * "&nbsp;" | n }${ rootcl.getName().capitalize() }</option>

          % for subcl in rootcl:
                ${ define_inline_aggreg_options(subcl, depth + 1) }
          % endfor
        % else:
            <option value="${ rootcl.getPath(listidx='(0)') }">${ depth * "&nbsp;" | n }${ rootcl.getName() }</option>
        % endif
</%def>

<%def name="define_inline_aggreg(obname)">
      <table class="inline_filter_content aggregation_table">
       <tr class="inline_filter">
        <th>${ _('Group entry by:') }</th>
        <td class="td_container_path">
         <select class="popup_input_field form-control input-sm" name="aggregated_${obname}">
          <option value="none"></option>
          % for i in all_filters[obname]:
           ${ define_inline_aggreg_options(i, 0) }
          % endfor
         </select>
        </td>
        <td class="td_container_remove"><a class="fa fa-minus" style="visibility: hidden"></a></td>
        <td class="td_container_add"><a class="append_entry fa fa-plus"></a></td>
       </tr>
      </table>
</%def>

<%def name="filter_enabled_marker(type)">
  <span class="filter_enabled_marker filter_popup_link">
   % if type == 2:
    [<a class="filter_enabled_marker">${ _("filtered") }</a>]
   % else:
    [<a style="color: gray;">${ _("filtered") }</a>]
   % endif
  </span>
</%def>

<%def name="filter_reset()">
<tr><td>
    <table class="inline_filter_content">
     <tr class="inline_filter nodash">
      <td colspan="3">&nbsp;</td>
      <td>
       <input type="button" class="reset_filter btn btn-default" value="${ _("Reset") }" />
       <input type="submit" class="btn btn-primary" value="${ _("Apply") }" />
      </td>
     </tr>
    </table>
</td></tr>
</%def>

<%block name="message_fields_header">
<thead>
 <tr style="height: 20px;">
  <th style="text-align: right; min-width: 3.0em;">${ sortable("#", "count", order_by) }</th>
  <th class="filter_popup">
   <a class="filter_popup_link">${ _("Classification") }</a>
    % if classification_filtered:
     ${ filter_enabled_marker(classification_filtered) }
    % endif
   <div id="classification" style="display: none">
    <table class="shadow">
     <tr><td>${ define_inline_filter("classification", "alert.classification.text") }</td></tr>
     <tr><td>${ define_inline_aggreg("classification") }</td></tr>
     <tr><td><table class="inline_filter_content">
       <tr>
        <th>${ _("Type:") }</th>
        <td>&nbsp;</td>
        % for name, path in ((N_("Alert"), "alert.create_time"), (N_("CorrelationAlert"), "alert.correlation_alert.name"), (N_("OverflowAlert"), "alert.overflow_alert.program"), (N_("ToolAlert"), "alert.tool_alert.name")):
        <td>
          <input id="checkbox-type-${ name }" class="checkbox-label" type="checkbox" name="alert.type[]" value="${ path }" ${ disabled(correlation_alert_view) }  />
          <label for="checkbox-type-${ name }" class="btn btn-default btn-xs label-checkbox">${ _(name) }<span class="badge"></span></label>
        </td>
        % endfor
       </tr>

       <tr>
        <th>${ _("Severity:") }</th>
        % for item in N_("info"), N_("low"), N_("medium"), N_("high"), N_("n/a"):
        <td>
          <input id="checkbox-severity-${ item }" class="checkbox-label" type="checkbox" name="alert.assessment.impact.severity[]" value="${ item }"/>
          <label for="checkbox-severity-${ item }" class="btn btn-default btn-xs label-checkbox">${ _(item) }<span class="badge"></span></label>
        </td>
        % endfor
       </tr>

      </table>
     </td></tr>
     ${ filter_reset() }
    </table>
    </div>
  </th>

  <th class="filter_popup">
   <a class="filter_popup_link">${ _("Source") }</a>
   % if source_filtered:
     ${ filter_enabled_marker(source_filtered) }
   % endif
   <div id="source" style="display: none">
    <table class="shadow">
     <tr><td>${ define_inline_filter("source", "alert.source.node.address.address") }</td></tr>
     <tr><td>${ define_inline_aggreg("source") }</td></tr>
     ${ filter_reset() }
    </table>
   </div>
  </th>

  <th class="filter_popup">
   <a class="filter_popup_link">${ _("Target") }</a>
   % if target_filtered:
     ${ filter_enabled_marker(target_filtered) }
   % endif
   <div id="target" style="display: none">
    <table class="shadow">
     <tr><td>${ define_inline_filter("target", "alert.target.node.address.address") }</td></tr>
     <tr><td>${ define_inline_aggreg("target") }</td></tr>
     ${ filter_reset() }
    </table>
   </div>
  </th>

  <th class="filter_popup">
   <a class="filter_popup_link">${ _("Analyzer") }</a>
   % if analyzer_filtered:
     ${ filter_enabled_marker(analyzer_filtered) }
   % endif
   <div id="analyzer" style="display: none">
    <table class="shadow">
     <tr><td>${ define_inline_filter("analyzer", "alert.analyzer.name") }</td></tr>
     <tr><td>${ define_inline_aggreg("analyzer") }</td></tr>
     ${ filter_reset() }
    </table>
   </div>
  </th>

  <th>${ sortable(_("Date"), "time", order_by) }</th>

  % for column in extra_column:
  <th>${ column }</th>
  % endfor

  % if messages and env.request.user.has("IDMEF_ALTER"):
  <th><input class="checkbox" type="checkbox" id="allbox" /></th>
  % endif

</tr>
</thead>
</%block>


<%def name='writeInlineFilter(inline_filter, optval=None, cl="", help="")'>
% if optval:
% if inline_filter.already_filtered:
<span class="${ cl }" title="${ help }">${ optval }</span>
% else:
<a class="${ cl }" href="${ inline_filter.inline_filter }" title="${ help }">${ optval }</a>
% endif
% else:
% if inline_filter.already_filtered:
<span class="${ cl }" title="${ help }">${ _(inline_filter.value) }</span>
% else:
<a class="${ cl }" href="${ inline_filter.inline_filter }" title="${ help }">${ _(inline_filter.value) }</a>
% endif
% endif
</%def>

<%def name="classificationWrite(info, text)">
<a class="impact_severity_${ info.severity.value } popup_menu_toggle" title="${ info.description }" data-toggle="tooltip" data-placement="top" data-container="#main">${ text }</a><span class="popup_menu">
% if info.count == 1:
% for obj in info.links:
${ obj.to_string() }
% endfor
% endif
% if not info.classification.already_filtered:
<a href="${ info.classification.inline_filter }">${ _("Filter on this classification") }</a>
% else:
<span>${ _("Filter on this classification") }</span>
% endif
% for name, url in info.classification_url:
<a href="${ url }">${ name }</a>
% endfor
</span>
</%def>

<%def name="timeWrite(time_url, text)">
% if time_url:
<a class="popup_menu_toggle">${ text }</a><span class="popup_menu">
% for name, url in time_url:
<a href="${ url }">${ name }</a>
% endfor
</span>
% else:
${ text }
% endif
</%def>

<%def name="writeService(hstr, direction)">
  % if direction.service.value != None:
       ${ hstr }
       <a class="popup_menu_toggle">${ direction.service.value }</a>
       <span class="popup_menu">
        ${ writeInlineFilter(direction.service, _("Filter on this port/protocol")) }
        % if direction.port.value and env.enable_details:
        <a target="${ env.external_link_target }" href="${ env.port_details_url }?port=${ direction.port.value }&amp;protocol=${ direction.protocol.value or '' }">${ _("Port/protocol information") }</a>
        % endif
       </span>
  % endif
</%def>


<%def name="message_fields(message)">
<td style="text-align: right; width: 20px">
  % if message.aggregated and message.aggregated_classifications_hidden > 0:
    <br/>
  % endif
  % for info in message.infos:
    % if message.aggregated and info.count > 1:
      <a href="${ info.display }">${ info.count }</a>
    % else:
      ${ info.count }
    % endif
    <br/>
  % endfor
</td>

<td>
  % if message.aggregated and message.aggregated_classifications_hidden > 0:
    <b>(${ _("{hidden} of {total} alerts not shown...").format(hidden=message.aggregated_classifications_hidden, total=message.aggregated_classifications_total) }
    <a href="${ message.aggregated_classifications_hidden_expand }">${ _("expand") }</a>)</b>
    <br/>
  % endif

  % for info in message.infos:
    ${ classificationWrite(info, info.classification.value or "n/a") }

    % if message.sub_alert_name:
      % if message.sub_alert_display:
        <b>(<a href="${ message.sub_alert_display }">${ message.sub_alert_number }</a> ${ ngettext("alert", "alerts", message.sub_alert_number) })</b>
      % endif
      : <i>${ message.sub_alert_name }</i><br/>
    % endif

    <br/>
  % endfor

</td>

% for name, direction, hidden, total, expand in ("source", message.source, message.aggregated_source_hidden, message.aggregated_source_total, message.aggregated_source_expand), ("target", message.target, message.aggregated_target_hidden, message.aggregated_target_total, message.aggregated_target_expand):
<td>
<% need_hr = 0 %>
% if hidden > 0:
<%
       dt = {
            "source": ["{hidden} of {total} source not shown", "{hidden} of {total} sources not shown"],
            "target": ["{hidden} of {total} target not shown", "{hidden} of {total} targets not shown"]
       }
%>
       <b>(${ ngettext(*(dt[name] + [total])).format(hidden=hidden, total=total) }
       <a href="${ expand }">${ _("expand") }</a>)</b>
       <br/>
% endif

% for direction in direction:
      % if need_hr:
        <hr style="border: 1px dashed #808080; margin-top: 3px; margin-bottom: 0px;" />
      % endif

      <% need_hr = 1 %>

      % for address in direction.addresses:

       <a class="popup_menu_toggle ajax-tooltip popup_menu_dynamic" data-title-url="${ address.url_infos }" data-popup-url="${ address.url_popup }">${ address.hostname }</a><span class="popup_menu">
         ${ writeInlineFilter(address, _("Filter on this %s") % (name)) }

       % if address.value and (not address.category or address.category in ("ipv4-addr", "ipv4-net", "ipv6-addr", "ipv6-net")):
         % if env.enable_details:
         <a target="${ env.external_link_target }" href="${ env.host_details_url }?host=${ address.value }">${ (_("%s information") % (name)).capitalize() }</a>
         % endif
         % for obj in address.host_links:
          ${ obj.to_string() }
         % endfor
       % endif
       </span>
${ writeService(":", direction) }
<br />
      % endfor
% endfor
</td>
% endfor

<td>
  % for sensor in message.sensors:
    % if sensor.name.value:
    <a class="popup_menu_toggle">${ sensor.name.value }</a>
    <span class="popup_menu">
      ${ writeInlineFilter(sensor.name, _("Filter on this Analyzer")) }
    </span>
    % endif
    % if sensor["node.name"].value:
    (<a class="popup_menu_toggle">${ sensor["node.name"].value }</a>)
    <span class="popup_menu">
      ${ writeInlineFilter(sensor["node.name"], _("Filter on this Host")) }
    </span>
    % endif
    <br/>
  % endfor
</td>

<td>
  % if message.aggregated:
    % if message.time_min.value == message.time_max.value:
      ${ message.time_min.value }
    % elif order_by == "time_asc":
      ${ message.time_min.value }<br />
      ${ message.time_max.value }
    % else:
      ${ message.time_max.value }<br />
      ${ message.time_min.value }
    % endif
  % else:
    ${ timeWrite(message.time.time_url, message.time.value) }
    % if message.analyzer_time.value:
      ${ _("sent at %s") % message.analyzer_time.value }
    % endif
  % endif
</td>

% for link in message.extra_link:
 <td>
   <div style="float:left;">
     ${ link | n }
   </div>
 </td>
% endfor
</%def>

<%block name="message_extra_footer">
  % if env.request.user.has("IDMEF_ALTER"):
  <div class="pull-right">
    <div class="form-inline">
      <input type="submit" class="btn btn-primary" name="listing_apply" value="${ _("Apply") }" data-confirm="${ _("Delete the selected alerts?") }" />
      <div class="form-group">
        <select class="form-control" name="action" id="action">
          <option value="delete_message">${ _('Delete') }</option>
        </select>
      </div>
    </div>
  </div>
  % endif
</%block>
