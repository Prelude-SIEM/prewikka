<% root_id = 'main_menu_ng' if inline else 'main_menu_ng_block' %>

<div>
  <label>${ _("Filter:") }</label>
</div>

<div>
  <script>
      $("#${root_id} select[name=filter]").select2_container({
          dropdownAutoWidth: true,
          templateResult: function(obj) {
              if ( obj.element && obj.element.className == "no-filter" )
                  return $('<span><i class="fa fa-ban text-danger"></i> ' + _.escape(obj.text) + '</span>');

              if ( obj.element && obj.element.className == "new-filter" )
                  return $('<span><i class="fa fa-plus text-success"></i> ' + _.escape(obj.text) + '</span>');

              return obj.text;
          }
      })
      .on("select2:selecting", function(e) {
          var obj = e.params.args.data;
          if ( obj.element && obj.element.className == "new-filter" ) {
              prewikka_ajax(obj.element.dataset.url);
              $(this).select2("close");
              return false;
          }
      });
  </script>

  <div class="dropdown dropdown-fixed dropdown-filter">
    <select name="filter" class="form-control input-${input_size}" value="${current_filter}">
      <option value="" class="no-filter">${ _("No filter") }</option>
      % if inline:
      <option value="" class="new-filter" data-url="${ url_for('FilterView.edit') }">${ _("New filter") }</option>
      % endif
      % for category, filters in sorted(filter_categories.items()):
      <optgroup label="${category or _("No category")}">
        % for fltr in filters:
        <option name="${fltr.name}" title="${fltr.description}" data-type="${ " ".join(fltr.criteria.keys()) }" ${ selected(fltr.name == current_filter) }>${fltr.name}</option>
        % endfor
      </optgroup>
      % endfor
    </select>
  </div>
</div>
