<%inherit file="/prewikka/templates/htmldocument.mak" />

<%!
from prewikka import utils, env
software = env.config.interface.get("software", "<img src='prewikka/images/prelude-logo.png' alt='Prelude' />")
%>

<div id="prewikka-notifications-container"></div>
<div id="prewikka-notification" class="prewikka-notification">
    <div class="alert">
        <button type="button" class="close">
            <span aria-hidden="true">&times;</span>
        </button>
        <i class="fa"></i>
        <b class="title"></b>
        <span class="content"></span>
    </div>
</div>

<div id="top_view">
    <nav class="navbar navbar-fixed-top navbar-primary" id="top_view_navbar">
        <div class="navbar-header">
            <div class="navbar-brand visible-xs-block">${software | n}</div>
            <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#main_navbar_collapse" aria-expanded="false">
                <i class=" fa fa-bars fa-2x"></i>
            </button>
        </div>

        <div class="collapse navbar-collapse" id="main_navbar_collapse">
            <%block name="toplayout_menu" />
            <ul class="nav navbar-nav navbar-right" id="nav_top_view_header">
                <li class="visible-lg-inline">
                    <div class="navbar-brand">${software | n}</div>
                </li>
                % for content in toplayout_extra_content:
                  ${content}
                % endfor
            </ul>
        </div>
    </nav>

    <%block name="toplayout_content" />

    <div id="_main_viewport"></div>
    <div id="_main">
      <%block name="main_content" />
    </div>

</div>

<div id="prewikka-dialog-container" class="container">
  <div id="prewikka-dialog-confirm" class="modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="true" data-keyboard="true" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
          <h5 class="modal-title" id="dialogLabel">${ _('Please Confirm') }</h5>
        </div>
        <div class="modal-body content"></div>
        <div class="modal-footer">
          <button class="btn btn-default cancel" data-dismiss="modal" aria-hidden="true">${ _('Cancel') }</button>
          <a class="btn btn-primary ok" aria-hidden="true" data-dismiss="modal" id="prewikka-dialog-confirm-OK">${ _('OK') }</a>
        </div>
      </div>
    </div>
  </div>

  <div id="prewikka-dialog-standard" class="modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="true" data-keyboard="true" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
          <h5 class="modal-title" id="dialogLabel">${ _('Prelude Dialog') }</h5>
        </div>
        <div class="modal-body content"></div>
        <div class="modal-footer">
          <a class="btn btn-primary ok" aria-hidden="true" data-dismiss="modal">${ _('OK') }</a>
        </div>
      </div>
    </div>
  </div>

  <div id="prewikka-dialog-connection-error" class="modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="static" data-keyboard="true" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header alert-danger">
          <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
          <h5 class="modal-title" id="dialogLabel">${ _('Connection error') }</h5>
        </div>
        <div class="modal-body content">
        ${ _("Connection failed, the server may be down or you may be experiencing network issues.") }
        </div>
        <div class="modal-footer">
          <a class="btn btn-primary ok" aria-hidden="true" data-dismiss="modal">${ _('OK') }</a>
        </div>
      </div>
    </div>
  </div>
</div>
