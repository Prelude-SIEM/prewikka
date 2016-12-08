<div class="container">
    <form class="form-horizontal usersettings" action="${ url_for(".modify") }" method="POST">
        <input type="hidden" name="name" value="${object.name}"/>

        <div class="form-group">
            <label for="inputUserId" class="col-sm-2 control-label">${ _("Login:") }</label>
            <div class="col-sm-10">
                <input type="text" id="inputUserId" class="form-control disabled" disabled value="${object.name}">
            </div>
        </div>

        <div class="form-group">
            <label for="inputUserName" class="col-sm-2 control-label">${ _("Name:") }</label>
            <div class="col-sm-10">
                <input class="form-control" type="text" name="fullname" id="inputUserName" value="${fullname}" placeholder="${ _("Name") }"/>
            </div>
        </div>

        <div class="form-group">
            <label for="inputUserEmail" class="col-sm-2 control-label">${ _("Email:") }</label>
            <div class="col-sm-10">
                <input class="form-control" type="email" name="email" id="inputUserEmail" value="${email}" placeholder="${ _("Email") }"/>
            </div>
        </div>

        <div class="form-group">
            <label for="inputUserLanguage" class="col-sm-2 control-label">${ _("Language:") }</label>
            <div class="col-sm-10">
                <select id="inputUserLanguage" class="form-control" name="language">
                % for lang, identifier in available_languages:
                    <option value="${identifier}" ${ selected(identifier == language) }>${lang}</option>
                % endfor

                </select>
            </div>
        </div>

        <div class="form-group">
            <label for="inputUserTheme" class="col-sm-2 control-label">${ _("Theme:") }</label>
            <div class="col-sm-10">
                <select id="inputUserTheme" class="form-control" name="theme">
                % for theme in available_themes:
                    <option value="${theme}" ${ selected(theme == selected_theme) }>${theme}</option>
                % endfor
                </select>
            </div>
        </div>

        <div class="form-group">
            <label for="inputUserTimezone" class="col-sm-2 control-label">${ _("Timezone:") }</label>
            <div class="col-sm-10">
                <select id="inputUserTimezone" class="form-control" name="timezone">
                % for tz in available_timezones:
                    <option value="${tz}" ${ selected(tz == timezone) }>${tz}</option>
                % endfor
                </select>
            </div>
        </div>

        <div class="pull-right">
            <input class="btn btn-default widget-control widget-only usersettings cancel" type="button" value="${ _('Cancel') }" />
            <button class="btn btn-primary widget-control usersettings submit" type="submit"><i class="fa fa-save"></i> ${ _("Save") }</button>
        </div>
    </form>
</div>
