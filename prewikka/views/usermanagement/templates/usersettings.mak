<%!
from prewikka import localization, theme
%>

<%def name="member_add_entry(value)">
  % if can_manage_group_members:
  <div class="input-group repeat-entry">
    <select name="member_object[]" class="form-control">
      % for val in object_list:
      <option ${ selected(val == value) }>${ val }</option>
      % endfor
    </select>
    <span class="input-group-btn">
      <div class="add_entry_row btn btn-default"><i class="fa fa-plus"></i></div>
      <div class="del_entry_row btn btn-default"><i class="fa fa-minus"></i></div>
    </span>
  </div>
  % else:
  <select name="member_object[]" class="form-control" disabled>
    <option>${ value }</option>
  </select>
  % endif
</%def>


<%
text = { "User": { "info": _("Account information"),
                   "name": _("Login:"),
                   "members": _("Groups:"),
                   "placeholder": _("Login")},

         "Group": { "info": _("Group information"),
                    "name": _("Group Name:"),
                    "members": _("Members:"),
                    "placeholder": _("Group Name")}
}

%>


<div class="container">
  <div class="widget" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="false" data-draggable="true" data-widget-options="modal-lg">
    <script type="text/javascript">
      $LAB.script("usermanagement/js/usermanagement.js").wait(function() {
          $("form.usersettings .allbox").on("click", function() {
              $(this.form).find('input[name="permissions[]"]:not([disabled])').check($(this).prop('checked'));
          });
          init_usersettings();
      });
    </script>

    <form class="form-horizontal usersettings " action="${ target }" method="POST">
      % if object:
      <input type="hidden" name="name" value="${ object.name }"/>
      % endif

  % if widget:
      <input type="hidden" name="fromlisting" value="true"/>
  % endif

      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
        <h5 class="modal-title" id="dialogLabel">${object.name if object else _(text[type]["info"]) }</h5>
      </div>

      <div class="modal-body">
        <div class="form-group">
          <label for="inputUserId" class="col-sm-2 control-label">${ text[type]["name"] }</label>
          <div class="col-sm-10">
          % if object:
            <input type="text" id="inputUserId" class="form-control disabled" disabled value="${ object.name }">
          % else:
            <input type="text" name="name" required id="inputUserId" class="form-control" placeholder="${ text[type]["placeholder"] }">
          % endif
          </div>
        </div>

      % if type == "User":
        <div class="form-group">
          <label for="inputUserName" class="col-sm-2 control-label">${ _("Name:") }</label>
          <div class="col-sm-10">
            <input class="form-control" type="text" name="fullname" id="inputUserName" value="${ fullname }" placeholder="${ _("Name") }"/>
          </div>
        </div>
        <div class="form-group">
          <label for="inputUserEmail" class="col-sm-2 control-label">${ _("Email:") }</label>
          <div class="col-sm-10">
            <input class="form-control" type="email" name="email" id="inputUserEmail" value="${ email }" placeholder="${ _("Email") }"/>
          </div>
        </div>

        <div class="form-group">
          <label for="inputUserLanguage" class="col-sm-2 control-label">${ _("Language:") }</label>
          <div class="col-sm-10">
            <select id="inputUserLanguage" class="form-control" name="language">
            % for identifier, lang in sorted(localization.get_languages().items()):
              <option value="${ identifier }" ${ selected(language == identifier) }>${ lang }</option>
            % endfor
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="inputUserTheme" class="col-sm-2 control-label">${ _("Theme:") }</label>
          <div class="col-sm-10">
            <select id="inputUserTheme" class="form-control" name="theme">
            % for i in theme.get_themes():
              <option value="${ i }" ${ selected(user_theme == i) }>${ i }</option>
            % endfor
            </select>
          </div>
        </div>

        <div class="form-group">
          <label for="inputUserTimezone" class="col-sm-2 control-label">${ _("Timezone:") }</label>
          <div class="col-sm-10">
            <select id="inputUserTimezone" class="form-control form-control-select2" name="timezone">
            % for tz in localization.get_timezones():
              <option value="${ tz }" ${ selected(tz == timezone) }>${ tz }</option>
            % endfor
            </select>
          </div>
        </div>
      % endif

      <!-- Group management -->
      % if can_manage_group_members or member_list:
        <div class="form-group">
          <label for="inputUserGroups" class="col-sm-2 control-label">${ text[type]["members"] }</label>
          <div class="col-sm-10">
          % for f in member_list:
            ${ member_add_entry(f) }
          % endfor

          % if not(member_list):
            ${ member_add_entry('') }
          % endif
          </div>
        </div>
      % endif
      <!-- End Group -->

      <!-- Extra settings -->
      % for i in extra_content:
        ${ i }
      % endfor
      <!-- -->

    <%
    disabled_general = ""
    if type == "User" and not (env.request.user.has("USER_MANAGEMENT") and env.auth.can_manage_permissions()):
        disabled_general = "disabled"
    %>

        <div class="form-group">
         <label for="inputUserPermissions" class="col-sm-2 control-label">${ _("Permissions:") }</label>
          <div class="col-sm-10">
            <ul class="list-group">
            % for perm, user_has_perm, group_has_perm in permissions:
              <input class="checkbox-inputgroup" type="checkbox" name="permissions[]" id="permissions-${ perm.lower() }" value="${ perm }" ${ checked(group_has_perm or user_has_perm) } ${ disabled(disabled_general or group_has_perm) } />
              <label for="permissions-${ perm.lower() }" class="list-group-item ${ disabled(disabled_general or group_has_perm) } list-bootstrap-label"><span class="badge"><a></a></span>${ _(perm) }</label>
            % endfor
            </ul>
            <input ${ disabled_general } class="checkbox-inputgroup allbox" type="checkbox" id="permissions-check-all"/>
            <label for="permissions-check-all" class="list-group-item ${ disabled_general } list-bootstrap-label list-bootstrap-label-all"><span class="badge"><a></a></span>${ _("Check All") }</label>
          </div>
        </div>

      % if type == "User" and env.auth.can_set_password():
        <hr>
        % if ask_current_password:
        <div class="form-group">
          <label for="inputUserPasswordCurrent" class="col-sm-2 control-label">${ _("Current password:") }</label>
          <div class="col-sm-10">
            <input class="form-control" type="password" name="password_current" id="inputUserPasswordCurrent" autocomplete="off" placeholder="${ _("Current password") }"/>
          </div>
        </div>
        % endif
        <div class="form-group">
          <label for="inputUserPasswordNew" class="col-sm-2 control-label">${ _("New password:") }</label>
          <div class="col-sm-10">
            <input class="form-control" type="password" name="password_new" id="inputUserPasswordNew" autocomplete="off" placeholder="${ _("New password") }"/>
          </div>
        </div>
        <div class="form-group">
          <label for="inputUserPasswordConfirm" class="col-sm-2 control-label">${ _("Confirm new password:") }</label>
          <div class="col-sm-10">
            <input class="form-control" type="password" name="password_new_confirmation" id="inputUserPasswordConfirm" autocomplete="off" placeholder="${ _("Confirm new password") }"/>
          </div>
        </div>
      % endif
      </div> <!-- modal-body -->

  <%
  action = "update" if object else "create"
  typetbl = { "User": { "create": _("Create user"),
                        "update": _("Save") },
              "Group": { "create": _("Create group"),
                         "update": _("Save") }
  }
  %>

      <div class="modal-footer standard clearfix">
        <div class="pull-right">
          <button type="button" class="btn btn-default widget-only" data-dismiss="modal">${ _('Cancel') }</button>
          <button type="submit" class="btn btn-primary" value="${ typetbl[type][action] }"><i class="fa fa-save"></i> ${ _("Save") }</button>
        </div>
      </div>

    </form>
  </div>
</div>
