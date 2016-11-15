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
            if ( ! data["logs"] ) {
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


    $(".activate-button").click(function(e) {
        if ( ! $(this).attr("data-confirm") ) {
              $.ajax({url: prewikka_location().href,
                     type: "POST",
                     data: $("input[type=checkbox]").serialize(),
                     dataType: "json"})
              .done(function(data) {
                  location.reload();
                  return false;
              });

              return false;
        }
    });

    $(".update-button").click(function() {

        var nb_plugin = 0;

        $("#update-dialog tbody").empty();
        $("#update-dialog .btn").prop("disabled", true);
        $('#update-dialog .progress-bar').removeClass('progress-bar-danger').addClass('active').css('width', '0%').attr('aria-valuenow', 0).text("0%");
        $("#update-dialog").modal();

        prewikka_EventSource({
            url: prewikka_location().pathname + "?apply_update=true",

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

<style>
    .fieldset_heading .right {
        text-align: right;
    }

    table.update_log {
        border-collapse: collapse;
    }

    table.update_log tbody {
        height: 200px;
        overflow-y: auto;
    }

    table.update_log td.result {
        font-weight: bold;
    }

    .hiddenRow {
        padding: 0 !important;
    }
</style>


<div class="container">
<div id="update-dialog" title="Applying Updates" class="modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="static" data-keyboard="false">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title title" id="dialogLabel">${ _('Update Dialog') }</h3>
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

<div id="fieldset_page">
% if len(maintenance) > 0:
  <div class="panel panel-theme">
    <div class="panel-heading">
      <h3 class="panel-title">${ _("Plugin Maintenance") }</h3>
    </div>
    <div class="panel-body">
      <p>
        <center><b style="color:red;">${ _("The following apps need to be updated before they can be loaded into the system") }</b></center>
      </p>

      % for name, list in sorted(maintenance.items()):
      <fieldset class="fieldset_heading">
        <legend>${ _(name) }</legend>
        <table>
          <tr><th style="width:20%">${ _("Name") }</th><th>${ _("Description") }</th><th style="width:10%">${ _("Version") }</th><th style="width:15%">${ _("Current Database Version") }</th><th class="right" style="width:15%">${ _("Required Database Update") }</th></tr>

        % for mod, fv, uplist in sorted(list, key=lambda x: x[0].full_module_name):
          <tr class="table_row_${loop.cycle('even', 'odd')}">
            <td>${ mod.plugin_name or mod.full_module_name }</td><td>${ _(mod.plugin_description) }</td><td>${ mod.plugin_version }</td>
            <td>${ fv or '-' }</td>
            <td class="right">${ ", ".join([text_type(i) for i in uplist]) }</td>
          </tr>
        % endfor
        </table>
      </fieldset>
    % endfor
      <div class="pull-right">
        <button class="update-button btn btn-danger" ${ disabled(maintenance_total == 0) }>${ _("Install Update") }</button>
      </div>
    </div>
  </div>
% endif

  <div class="panel panel-theme">
    <div class="panel-heading">
      <h3 class="panel-title">${ _("Installed Apps") }</h3>
    </div>
    <div class="panel-body">
      % for name, list in sorted(installed.items()):
      <fieldset class="fieldset_heading">
        <legend>${ _(name) }</legend>
        <table>
          <tr><th style="width:20%">${ _("Name") }</th><th>${ _("Description") }</th><th style="width:10%">${ _("Version") }</th><th style="width:10%">${ _("Database Version") }</th><th class="right" style="width:5%">${ _("Active") }</th></tr>

        % for mod, enabled in sorted(list, key=lambda x: x[0].__module__):
          <tr class="table_row_${loop.cycle('even', 'odd')}">
            <td>${ mod.plugin_name or mod.full_module_name }</td><td>${ _(mod.plugin_description) }</td><td>${ mod.plugin_version }</td>
            <td>${ mod.plugin_database_version or '-' }</td>
            <td class="right"><input type="checkbox" name="enable_plugin" value="${ mod.full_module_name }" ${ checked(enabled) } ${ disabled(mod.plugin_mandatory) } /></td>
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
</div>
