<div>
  <label>${ _("Filter:") }</label>
</div>

<div>
  <select class="form-control input-${ input_size } menu-filter" name="filter" data-toggle="tooltip" title="${ _("Available filters") }" data-trigger="hover" data-container="#main">
    <option value="">${ _("No filter") }</option>
    % for fltr in filter_list:
    <option value="${fltr.name}" data-type="${ " ".join(fltr.criteria.keys()) }" ${ selected(fltr.name == current_filter) }>${fltr.name}</option>
    % endfor
  </select>
</div>
