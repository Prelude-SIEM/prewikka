<%! from prewikka import view %>

<table class="table table-condensed subgrid">
  <tbody>
    % for field in fields_info:
    <%
      try:
          float(fields_value[field])
          icon_type = "hashtag"
      except ValueError:
          icon_type = "paragraph"
      except view.MissingParameterError:
          continue
    %>
    <tr>
      <td class="field hover-details gbonly" data-field="${ field }"><i class="fa fa-${ icon_type }"></i>${ field }</td>
      <td class="filter">
        <span>
          <i data-field="${field}" data-value="${ fields_value[field] }" data-toggle="tooltip" title="${ _("Add to search") }" data-container="#main" class="fa fa-search-plus add_search"></i>
          <i data-field="${field}" data-value="${ fields_value[field] }" data-toggle="tooltip" title="${ _("Exclude from search") }" data-container="#main" class="fa fa-search-minus del_search"></i>
        </span>
      </td>
      <td>${ fields_value[field] }</td>
    </tr>
    % endfor
  </tbody>
</table>
