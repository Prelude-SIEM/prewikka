<link rel="stylesheet" type="text/css" href="usermanagement/css/usermanagement.css">

<%
text = { "User": { "title": _("Users"),
                   "name": _("Login"),
                   "create": _("Create user"),
                   "delete": _("Delete the selected users?")},
         "Group": { "title": _("Groups"),
                    "name": _("Group Name"),
                    "create": _("Create group"),
                    "delete": _("Delete the selected groups?")}
}
%>

<script type="text/javascript">

$LAB.wait(function() {

    var permissions = [];
    var group_headers = [];
    var current_group = null;

    % for perm in all_permissions:
      var name = "${ perm }";
      var group = name.split("_")[0];
      var label = name.split("_")[1];
      permissions.push({
          name: name,
          label: label,
          description: "${ _(perm) }"
      });
      if ( current_group && current_group.titleText == group )
          current_group.numberOfColumns++;
      else {
          current_group = {
              startColumnName: name,
              numberOfColumns: 1,
              titleText: group
          };
          group_headers.push(current_group);
      }
    % endfor

    var multiselect = true;
    % if not backend_can_delete:
        multiselect = false;
    % endif

    var text = {'title': "${ text[type]['title'] }", 'new': "${ text[type]['create'] }", 'search': "${ _("Search:") }"};

    var grid = CommonListing("table#users", text, {
        editLink: "${ url_for(type + 'Settings.edit') }",
        deleteLink: "${ url_for(type + 'ListingAjax.delete') }",
        globalSearch: true,
        datatype: "json",
        url: "${ url_for(type + 'ListingAjax.listing') }",
        colModel: [{name: 'name', label: "${ text[type]['name'] }"}].concat($.map(permissions, function(perm) {
            return {name: perm.name, label: perm.label, sortable: false, search: false, headerTitle: perm.description, align: 'center', formatter: function(cellValue) {
                if ( cellValue ) return "<i class=\"fa fa-check text-success\"></i>";
                else return "";
            }};
        })),
        multiselect: multiselect,
    }, ${html.escapejs(env.request.parameters["jqgrid_params_users"])});

    grid.jqGrid("setGroupHeaders", {groupHeaders: group_headers});
});
</script>


<table id="users"></table>

<div class="footer-buttons">
% if backend_can_create:
     <button type="button" title="${ text[type]['create'] }" class="btn btn-primary button-add"><i class="fa fa-plus"></i> ${ _("Create") }</button>
% endif
% if backend_can_delete:
     <button type="button" class="needone btn btn-danger button-delete" data-confirm="${ text[type]['delete'] }"><i class="fa fa-trash"></i> ${ _("Delete") }</button>
% endif
</div>
