<div>
  <label for="menu_filter_select">${ _("Filter:") }</label>
</div>

<div>
  <select id="menu_filter_select" class="form-control" name="filter" data-toggle="tooltip" title="${ _("Available filters") }" data-trigger="hover" data-container="#main">
    <option value="">${ _("No filter") }</option>
    % for fltr in filter_list:
    <option value="${fltr}" ${ selected(fltr == current_filter) }>${fltr}</option>
    % endfor
  </select>
</div>