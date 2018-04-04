<%!
import datetime
%>

<%def name="GroupbyTable(search)">
<table class="table table-striped table-condensed">
  <thead>
    <tr>
      % for group in search.groupby:
      <th class="text-center">${ group }</th>
      % endfor
      <th class="text-center">${ _("Count") }</th>
    </tr>
  </thead>

<%
step = search.get_step()
%>

% for result in search.get_result():
  <tr>
    % for idx, group in enumerate(search.groupby):
     <%
      label = result[idx + 1]
      if isinstance(label, datetime.datetime):
          label = label.strftime(step.unit_format)
      %>

    <td class="text-center">
      <a href="${ search.get_groupby_link([group], [result[idx + 1]], step, cview='.forensic') }">${ label }</a>
    </td>
    % endfor

    <td class="text-center">
      <a href="${ search.get_groupby_link(search.groupby, result[1:], step, cview='.forensic') }">${ result[0] }</a>
    </td>
  </tr>
% endfor
</table>
</%def>
