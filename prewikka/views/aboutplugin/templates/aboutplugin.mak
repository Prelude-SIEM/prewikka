<link rel="stylesheet" type="text/css" href="aboutplugin/css/aboutplugin.css" />

<script type="text/javascript">
    var slice = 0;

    $.fn.shiftcheckbox = function() {
        var allbox = $(this);

        var lastChecked = null;

        $(allbox).click(function(e) {
            if ( ! lastChecked ) {
                lastChecked = this;
                return;
            }

            if ( e.shiftKey ) {
                var start = allbox.index(this);
                var end = allbox.index(lastChecked);
                allbox.slice(Math.min(start, end), Math.max(start, end) + 1).prop("checked", lastChecked.checked);
            }

            lastChecked = this;
        });
    };

    $("input[type=checkbox]:not(:disabled)").shiftcheckbox();

    function update_log(data, nb_plugin) {
            if ( data["logs"] === undefined ) {
                var curval = parseFloat($('.progress-bar').attr('aria-valuenow'));
                var newval = curval + slice;
                $('.progress-bar').css('width', newval + '%').attr('aria-valuenow', newval).text(Math.round(newval) + '%');

<%text>
                $("table.update_log tbody").append(`<tr data-toggle="collapse" data-target="#detail${(nb_plugin + 1)}">
                                                      <td>${data["module"]}</td><td>${data["script"]}</td><td class="result">...</td>
                                                     </tr>`);
</%text>

            }

            else {
                var result = data["error"] ? '${ _("ERROR") }' : '${ _("OK") }';
                var classname = data["error"] ? "danger" : "success";

                if ( data["error"] )
                    $('#update-dialog .progress-bar').addClass('progress-bar-danger').text('${ _("Update failed") }');

                $("table.update_log tbody tr:last").addClass(classname);
                $("table.update_log tbody tr:last td.result").text(result);
<%text>
                $("table.update_log tbody").append(`<tr><td colspan="3" class="hiddenRow">
                                                           <div class="collapse panel panel-${classname}" id="detail${nb_plugin}">
                                                           <div class="panel-heading">${data["error"] || ''}</div>
                                                           <pre>${data["logs"]}</pre>
                                                          </div>
                                                     </td></tr>`);
</%text>
            }
    }


    $(".update-button").click(function() {

        var nb_plugin = 0;

        $("#update-dialog tbody").empty();
        $("#update-dialog .btn").prop("disabled", true);
        $('#update-dialog .progress-bar').removeClass('progress-bar-danger').addClass('active').css('width', '0%').attr('aria-valuenow', 0).text("0%");
        $("#update-dialog").modal();

        prewikka_EventSource({
            url: "${ url_for('.update') }",

            events: {
                "begin": function(data) {
                    slice = 100 / data["total"];
                },
                "finish": function(data) {
                    $("#update-dialog .btn").prop("disabled", false);
                    $('#update-dialog .progress-bar').removeClass('active')
                },
            },

            message: function(data) {
                update_log(data, nb_plugin++);
            }
        });

        return false;
    });

    $('.collapse').on('show.bs.collapse', function () {
        $('.collapse.in').collapse('hide');
    });

    $("#update-dialog .btn").click(function() {
            location.replace(prewikka_location().href);
            return false;
    });

</script>


<div class="container">
  <div id="update-dialog" class="modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="static" data-keyboard="false">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="dialogLabel">${ _('Update Dialog') }</h5>
        </div>
        <div class="modal-body content">
          <div class="progress">
            <div class="progress-bar progress-bar-striped" role="progressbar" style="width:0%" aria-valuenow="0">0%</div>
          </div>
          <div>
            <table class="table table-condensed table-hover update_log">
             <thead>
              <tr>
               <th>${ _("Plugin") }</th>
               <th>${ _("Script") }</th>
               <th>${ _("Result") }</th>
              </tr>
             </thead>
             <tbody>
             </tbody>
            </table>
          </div>
        </div>
        <div class="modal-footer">
          <a class="btn btn-primary" aria-hidden="true" data-dismiss="modal">${ _('Close') }</a>
        </div>
      </div>
    </div>
  </div>
</div>

<form method="POST" action="${ url_for('.enable') }">

% if len(maintenance) > 0:
  <div class="panel panel-theme">
    <div class="panel-heading">
      <h5 class="panel-title">${ _("Plugin Maintenance") }</h5>
    </div>
    <div class="panel-body">
      <div style="text-align: center; font-weight: bold; color:red;">${ _("The following apps need to be updated before they can be loaded into the system") }</div>

      % for name, list in sorted(maintenance.items()):
      <fieldset class="fieldset_heading">
        <legend>${ _(name) }</legend>
        <table class="table table-striped table-condensed">
          <tr>
            <th style="width:20%">${ _("Name") }</th>
            <th>${ _("Description") }</th>
            <th style="width:10%">${ _("Version") }</th>
            <th class="text-center" style="width:15%">${ _("Current database version") }</th>
            <th class="text-right" style="width:15%">${ _("Required database update") }</th>
          </tr>

        % for mod, fv, uplist in sorted(list, key=lambda x: x[0].plugin_name or x[0].full_module_name):
          <tr>
            <td>${ mod.plugin_name or mod.full_module_name }</td>
            <td>${ _(mod.plugin_description) }</td>
            <td>${ mod.plugin_version }</td>
            <td class="text-center">${ fv or '-' }</td>
            <td class="text-right">${ ", ".join([text_type(i) for i in uplist]) }</td>
          </tr>
        % endfor
        </table>
      </fieldset>
    % endfor
      <div class="pull-right">
        <button class="update-button btn btn-danger" ${ disabled(maintenance_total == 0) }>${ _("Install update") }</button>
      </div>
    </div>
  </div>
% endif

  <div class="panel panel-theme">
    <div class="panel-heading">
      <h5 class="panel-title">${ _("Installed Apps") }</h5>
    </div>
    <div class="panel-body">
      % for name, list in sorted(installed.items()):
      <fieldset class="fieldset_heading">
        <legend>${ _(name) }</legend>
        <table class="table table-striped table-condensed">
          <tr>
            <th style="width:20%">${ _("Name") }</th>
            <th>${ _("Description") }</th>
            <th style="width:10%">${ _("Version") }</th>
            <th class="text-center" style="width:15%">${ _("Database version") }</th>
            <th class="text-right" style="width:5%">${ _("Active") }</th>
          </tr>

        % for mod, enabled in sorted(list, key=lambda x: x[0].plugin_name or x[0].full_module_name):
          <tr class="${ 'danger' if mod.error and enabled else 'disabled-app' if not enabled else '' }">
            <td>${ mod.plugin_name or mod.full_module_name }</td>
            <td>${ _(mod.plugin_description) }</td>
            <td>${ mod.plugin_version }</td>
            <td class="text-center">${ mod.plugin_database_version or '-' }</td>
            <td class="text-right">
              % if mod.error and enabled:
              <a data-content="${ _(getattr(mod.error, 'message', mod.error)) }" data-toggle="popover" data-placement="left"><i class="fa fa-exclamation-triangle text-danger"></i></a>
              % endif
              <input type="checkbox" name="enable_plugin[]" value="${ mod.full_module_name }" ${ checked(enabled) } ${ disabled(mod.plugin_mandatory) } />
            </td>
          </tr>
        % endfor
        </table>
      </fieldset>
      % endfor
      <div class="pull-right">
        <button class="btn btn-warning activate-button" data-confirm="${ _("Update the selected apps?") }"><i class="fa fa-refresh"></i> ${ _("Update") }</button>
      </div>
    </div>
  </div>

</form>
