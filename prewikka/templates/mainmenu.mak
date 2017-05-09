<script type="text/javascript">
$(document).ready(function() {
  % if inline:
    $('#main_menu_ng label').addClass("label-xs");
    $('#main_menu_ng input, #main_menu_ng select').addClass("form-control input-sm");
    $('#main_menu_ng button').addClass("btn-sm");
  % else:
    $('#main_menu_ng_block div.form-group > div:first-child').addClass("control-label col-sm-2")
    $('#main_menu_ng_block div.form-group > div:last-child').addClass("col-sm-10")
    $('#main_menu_ng_block button').addClass("btn-block");
  % endif
});

$LAB.script("prewikka/js/mainmenu.js", "prewikka/js/moment.min.js").wait(function() {
    window.mainmenu.reset();

  % if auto_apply_value > 0:
    window.mainmenu.start();
  % endif

    MainMenuInit("${timeline.time_format}", ${ int(inline) });

    $('#timeline_end').datetimepicker("setDate", new Date(moment("${timeline.end}")));
    $('#timeline_start').datetimepicker("setDate", new Date(moment("${timeline.start}")));
    update_date_input();

  % if timeline.quick_custom:
    trigger_custom_date(true);
  % else:
    trigger_custom_date(false);
  % endif

    $('#main_menu_ng').trigger('mainmenu_ready');
});
</script>

<div id="${ 'main_menu_ng' if inline else 'main_menu_ng_block'}">
  <input type="hidden" name="_save" value="1" />
  <div class="${ 'form-inline pull-right' if inline else ''}" id="main_menu_navbar">
    % for i in menu_extra:
      <div class="form-group main_menu_extra">
        ${i}
      </div>
    % endfor

    % if refresh:
      <input type="hidden" name="auto_apply_value" id="hidden_auto_apply_value" value="${auto_apply_value}" />
      <div class="form-group">
        <div>
          <label>${ _("Refresh:") }</label>
        </div>

        <div>
          <div class="dropdown" id="dropdown-refresh">
            <div data-toggle="tooltip" title="${ _("Update frequency of the current page") }" data-trigger="hover" data-container="#main">
              <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" data-target="#dropdown-refresh">
                   <span class="reload-icon">&#8634;</span><span id="refresh-value">${timeline.refresh_selected}</span><span class="caret"></span>
              </button>
            </div>

            <ul class="dropdown-menu" id="refresh-select">
              % for label, value in timeline.refresh:
                <li><a data-value="${value}">${label}</a></li>
              % endfor

              <li role="separator" class="divider"></li>
              <li><a data-value="0">${ _("Inactive") }</a></li>
            </ul>
          </div>
        </div>
      </div>
    % endif

    % if period:
      <input type="hidden" name="timeline_value" id="hidden_timeline_value" value="${timeline.value}" ${disabled(timeline.quick_custom)} />
      <input type="hidden" name="timeline_unit" id="hidden_timeline_unit" value="${timeline.unit}" ${disabled(timeline.quick_custom)} />
      <input type="hidden" name="timeline_absolute" id="hidden_timeline_absolute" value="${timeline.absolute}" ${disabled(timeline.quick_custom)} />
      <input type="hidden" name="timeline_end" id="hidden_timeline_end" value="${timeline.end}" ${disabled(not timeline.quick_custom)} />
      <input type="hidden" name="timeline_start" id="hidden_timeline_start" value="${timeline.start}" ${disabled(not timeline.quick_custom)} />

      <div class="form-group">
        <div>
          <label>${ _("Period:") }</label>
        </div>

        <div>
          <div class="dropdown" id="dropdown-period">
            <div data-toggle="tooltip" title="${ _("Period to visualize") }" data-trigger="hover" data-container="#main">
              <button type="button" class="btn btn-default dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" data-target="#dropdown-period">
                 <span id="timeline_quick_selected">${timeline.quick_selected}</span> <span class="caret" />
              </button>
            </div>
            <ul class="dropdown-menu" id="timeline_quick_select">
              <li><a data-value="" data-unit="" data-absolute="" id="timeline_quick_select_custom">${ _("Custom") }</a></li>
              <li role="separator" class="divider"></li>

              % for label, value, unit, absolute in timeline.quick:
                 <li><a data-value="${value}" data-unit="${unit}" data-absolute="${absolute}">${label}</a></li>
              % endfor
            </ul>
          </div>
        </div>
      </div>

      % if not(inline):
      <div class="form-group collapse" style="margin-top: -15px;">
        <div class="col-sm-2">&nbsp;</div>
        <div class="col-sm-10">
      % endif

          <div class="form-group-date ${ 'form-group' if inline else 'col-sm-6' }">
            <div>
              <label class="label-xs" for="timeline_start">${ _("Start:") }</label>
            </div>
            <div>
              <input class="form-control input-timeline-datetime" type="text" id="timeline_start" placeholder="${ _("start") }" data-toggle="tooltip" title="${ _("Start date") }" data-trigger="hover" data-container="#main">
            </div>
          </div>

          <div class="form-group-date ${ 'form-group' if inline else 'col-sm-6' }">
            <div>
              <label class="label-xs" for="timeline_end">${ _("End:") }</label>
            </div>

            <div>
              <input class="form-control input-timeline-datetime" type="text" id="timeline_end" placeholder="${ _("end") }" data-toggle="tooltip" title="${ _("End date") }" data-trigger="hover" data-container="#main">
            </div>
          </div>

      % if not(inline):
        </div>
      </div>
      % endif
    % endif

    % if inline:
      <button class="btn btn-primary btn-submit disabled" id="main_menu_form_submit" type="submit">${ _("Go!") }</button>
    % endif
  </div>
</div>
