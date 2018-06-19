<% root_id = 'main_menu_ng' if inline else 'main_menu_ng_block' %>

<div>
  <label>${ _("Filter:") }</label>
</div>

<div>
  <div class="dropdown dropdown-fixed dropdown-filter">
    <input type="hidden" name="filter" value="${current_filter}" />
    <div data-toggle="tooltip" title="${ _("Available filters") }" data-trigger="hover" data-container="#main">
      <button type="button" class="btn btn-default btn-${ input_size } dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" data-target="#${root_id} .dropdown-filter">
        <span class="selected-value">${current_filter or _("No filter")}</span>
        <span class="caret"></span>
      </button>
    </div>

    <ul class="dropdown-menu filter-select">
      <li><a data-value=""><i class="fa fa-ban text-danger"></i> ${ _("No filter") }</a></li>
      % if inline:
      <li><a href="${ url_for('FilterView.edit') }" class="new-filter"><i class="fa fa-plus text-success"></i> ${ _("New filter") }</a></li>
      % endif
      % if filters:
      <li role="separator" class="divider"></li>
      % endif
      % for fltr in filters:
        <li><a data-value="${fltr.name}" data-type="${ " ".join(fltr.criteria.keys()) }" data-toggle="tooltip" data-container="#main" data-placement="left" title="${fltr.description}">${fltr.name}</a></li>
      % endfor
    </ul>
  </div>
</div>
