<label for="menu_filter_select" class="label-xs">${ _("Filter:") }</label>
<select id="menu_filter_select" name="filter" class="form-control input-sm" data-toggle="tooltip" title="${ _("Available filters") }" data-trigger="hover" data-container="#main">
    <option value="">${ _("No filter") }</option>
    % for fltr in filter_list:
    <option value="${fltr}" ${ selected(fltr == current_filter) }>${fltr}</option>
    % endfor
</select>
