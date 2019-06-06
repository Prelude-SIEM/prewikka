<%!
import datetime
from prewikka import view
%>

<table class="table table-condensed subgrid">
  <tbody>
    % for field in fields_info:
    <%
      try:
          value = fields_value[field]
      except view.MissingParameterError:
          continue

      icon_type = "paragraph"
      if isinstance(value, (int, float)):
          icon_type = "hashtag"
      elif isinstance(value, datetime.datetime):
          icon_type = "clock-o"
      elif isinstance(value, bytes):
          value = "\\x" + value.encode("hex")
    %>
    <tr>
      <td class="field" data-field="${ field }">
        <i class="fa fa-${ icon_type }"></i>
        <a data-container="#main" data-toggle="tooltip" title="${ _("Group by %s") % field }" href="${ url_for('.forensic', groupby=[field]) }">${ field }</a>
      </td>
      <td class="filter">
        <span>
          <i data-field="${field}" data-value="${value}" data-toggle="tooltip" title="${ _("Add to search") }" data-container="#main" class="fa fa-search-plus add_search"></i>
          <i data-field="${field}" data-value="${value}" data-toggle="tooltip" title="${ _("Exclude from search") }" data-container="#main" class="fa fa-search-minus del_search"></i>
        </span>
      </td>
      <td>${value}</td>
    </tr>
    % endfor
  </tbody>
</table>
