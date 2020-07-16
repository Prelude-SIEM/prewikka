<%!
from prewikka import crontab
DEFAULT_OPTION = "0 * * * *"
%>

<%def name="crontab_settings(enabled=True)">
  <%
    is_custom = False
    custom_val = [ "", "", "", "", "" ]
    default_schedule_value = getattr(job, "schedule", DEFAULT_OPTION)

    default_schedule_label = crontab.DEFAULT_SCHEDULE.get(default_schedule_value)
    if not default_schedule_label:
        is_custom = True
        custom_val = default_schedule_value.split(" ")
        default_schedule_label = crontab.DEFAULT_SCHEDULE["custom"]

    if not getattr(job, "enabled", enabled):
        is_custom = False
        default_schedule_value = "disabled"
        default_schedule_label = crontab.DEFAULT_SCHEDULE.get(default_schedule_value)
  %>

  <script type="text/javascript">
      $("#cronjob_setup input.schedule").change(function(e) {
          $("#quick-schedule").val(
              $("#cronjob_setup input.schedule").map(function() {
                  return $(this).val();
              }).get().join(" ")
          );
      });

      $("#cronjob_setup .dropdown-menu li a").click(function(){
        var is_custom = $(this).hasClass("custom");

        $("#cronjob_setup div.collapse").collapse((is_custom) ? "show" : "hide");
        if ( ! is_custom )
            $("#quick-schedule").val($(this).data('value'));
        else
            $("#cronjob_setup input.schedule").trigger("change");

        $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');
        $(this).parents(".dropdown").find('.btn').val($(this).data('value'));
      });
  </script>

    % if job:
      <input type="hidden" name="cronjob-id" value="${ job.id }" />
    % endif

    <div id="cronjob_setup">
      <div class="form-group">
        <div>
          <label for="quick-schedule" class="col-sm-2 control-label">${ _("Schedule:") }</label>
        </div>

        <div class="col-sm-10">
          <input id="quick-schedule" name="quick-schedule" type="hidden" value="${default_schedule_value}" />
          <div class="dropdown">
              <button type="button" class="btn btn-default btn-block dropdown-toggle" data-toggle="dropdown">${ _(default_schedule_label) }
                 <span class="caret"></span>
              </button>
             <ul class="dropdown-menu">
                % for value, label in filter(lambda x: x[0] not in ("custom", "disabled"), crontab.DEFAULT_SCHEDULE.items()):
                   <li><a data-value="${value}">${ _(label) }</a></li>
                % endfor

                <li role="separator" class="divider"></li>
                <li><a data-value="custom" class="custom">${ _(crontab.DEFAULT_SCHEDULE["custom"]) }</a></li>
                <li><a data-value="disabled">${ _(crontab.DEFAULT_SCHEDULE["disabled"]) }</a></li>
              </ul>
          </div>
        </div>
      </div>

      <div class="form-group collapse ${'in' if is_custom else ''}">
        <label  class="col-sm-2 control-label">&nbsp;</label>
        <div class="col-sm-2">
          <label for="minute">${ _('Minute:') }</label>
          <input type="text" class="schedule form-control" name="minute" value="${custom_val[0]}" />
        </div>
        <div class="col-sm-2">
          <label for="hour">${ _('Hour:') }</label>
          <input type="text" class="schedule form-control" name="hour" value="${custom_val[1]}" />
        </div>
        <div class="col-sm-2">
          <label for="day">${ _('Day:') }</label>
          <input type="text" class="schedule form-control" name="day" value="${custom_val[2]}" />
        </div>
        <div class="col-sm-2">
          <label for="month">${ _('Month:') }</label>
          <input type="text" class="schedule form-control" name="month" value="${custom_val[3]}" />
        </div>
        <div class="col-sm-2">
          <label for="weekday">${ _('Weekday:') }</label>
          <input type="text" class="schedule form-control" name="weekday" value="${custom_val[4]}" />
        </div>
      </div>

    </div>
</%def>

<div id="prewikka-cronjob" class="widget modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="true" data-keyboard="true" tabindex="-1">
  <form class="form-horizontal" method="POST" action="${ url_for('.save', id=job.id) }">
    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
      <h5 class="modal-title" id="dialogLabel">${ _('Edit Job') }</h5>
    </div>

    <div class="modal-body content" style="overflow: visible;">
      <div class="form-group">
        <label for="job-name" class="col-sm-2 control-label">${ _("Name:") }</label>
        <div class="col-sm-10">
          <input class="form-control" type="text" value="${_(crontab.format(job.ext_type, job.name))}" disabled/>
        </div>
      </div>

      ${ crontab_settings() }
    </div>

    <div class="modal-footer">
      <button type="button" class="btn btn-default" data-dismiss="modal">${ _("Cancel") }</button>
      <button type="submit" class="btn btn-primary"><i class="fa fa-save"></i> ${ _('Save') }</button>
    </div>
  </form>
</div>
