<%!
import string

from prewikka import localization, version
%>

<%inherit file="/prewikka/templates/toplayout.mak" />

<%block name="main_content">
<% localization.set_locale(env.config.general.default_locale) %>

<link rel="stylesheet" type="text/css" href="loginform/css/loginform.css">

<div class="login_password col-sm-offset-3 col-md-offset-4 col-sm-6 col-md-4">
    <div class="panel panel-theme">
        <div class="panel-heading">
            <h3 class="panel-title">${ _("User authentication") }</h3>
        </div>

        <div class="panel-body">
            <form method="post" class="col-sm-12">
                ${csrftoken()}

                % if message:
                <div class="alert alert-danger">${_(message)}</div>
                % endif

                <div class="form-group">
                    <div class="input-group">
                        <span class="input-group-addon"><i class="fa fa-user fa-lg fa-fw"></i></span>
                        <input class="form-control" type="text" name="_login" placeholder="${_('Login')}" autofocus required/>
                    </div>
                </div>

                <div class="form-group">
                    <div class="input-group">
                        <span class="input-group-addon"><i class="fa fa-lock fa-lg fa-fw"></i></span>
                        <input class="form-control" type="password" name="_password" placeholder="${_('Password')}" autocomplete="off" required/>
                    </div>
                </div>

                <div class="pull-right">
                    <button type="submit" class="btn btn-primary">${_("Log in")}</button>
                </div>
            </form>
        </div>
    </div>
</div>

<% footer = env.config.session.get("footer") %>
% if footer:
<div class="prelude-version">${ string.Template(footer).safe_substitute(version=version.__version__) }</div>
% endif

</%block>
