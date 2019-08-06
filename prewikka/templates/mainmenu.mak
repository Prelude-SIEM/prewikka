<% root_id = 'main_menu_ng' if inline else 'main_menu_ng_block' %>

<script type="text/javascript">
"use strict";

%if update:
  $("#${root_id}").data("mainmenu").set_date("${timeline.start}", "${timeline.end}");
%else:

  % if not inline:
  $('#main_menu_ng_block div.form-group-date > div:first-child').addClass("control-label col-sm-${label_width} input-${input_size}");
  $('#main_menu_ng_block div.form-group > div:first-child').addClass("control-label col-sm-${label_width} input-${input_size}");
  $('#main_menu_ng_block div.form-group > div:last-child').addClass("col-sm-${12 - label_width}");
  $('#main_menu_ng_block button').addClass("btn-block");
  % endif

$LAB.script("prewikka/js/mainmenu.js").script("prewikka/js/moment.min.js").wait(function() {
    window.mainmenu.stop();

  % if auto_apply_value > 0:
    window.mainmenu.start();
  % endif

    var menu = MainMenuInit(${ int(inline) }, "${timeline.start}", "${timeline.end}", "${timeline.time_format}", "${mainmenu_url}");
    menu.trigger_custom_date("${timeline.mode}" == "custom");
});

%endif
</script>

%if not update:
<div id="${ root_id }">
  <div class="main_menu_navbar${ ' form-inline pull-right' if inline else ''}">
    % for i in menu_extra:
      <div class="form-group main_menu_extra">
        ${i}
      </div>
    % endfor

    % if refresh:
      <input type="hidden" name="auto_apply_value" value="${auto_apply_value}" />
      <div class="form-group">
        <div>
          <label>${ _("Refresh:") }</label>
        </div>

        <div>
          <div class="dropdown dropdown-fixed dropdown-refresh">
            <div data-toggle="tooltip" title="${ _("Update frequency of the current page") }" data-trigger="hover" data-container="#main">
              <button type="button" class="btn btn-default btn-${ input_size } dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" data-target="#${root_id} .dropdown-refresh">
                   <span class="reload-icon">&#8634;</span><span class="refresh-value">${timeline.refresh_selected}</span><span class="caret"></span>
              </button>
            </div>

            <ul class="dropdown-menu refresh-select">
              % for value, label in timeline.refresh.items():
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
      <input type="hidden" name="timeline_mode" value="${timeline.mode}" />
      <input type="hidden" name="timeline_value" value="${timeline.value}" ${disabled(timeline.mode == "custom")} />
      <input type="hidden" name="timeline_unit" value="${timeline.unit}" ${disabled(timeline.mode == "custom")} />
      <input type="hidden" name="timeline_offset" value="${timeline.offset}" ${disabled(timeline.mode == "custom")} />

      <div class="form-group">
        <div>
          <label>${ _("Period:") }</label>
        </div>

        <div>
          <div class="dropdown dropdown-fixed dropdown-period">
            <div data-toggle="tooltip" title="${ _("Period to visualize") }" data-trigger="hover" data-container="#main">
              <button type="button" class="btn btn-default btn-${ input_size } dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false" data-target="#${root_id} .dropdown-period">
                 <span class="timeline_quick_selected">${timeline.quick_selected}</span> <span class="caret" />
              </button>
            </div>
            <ul class="dropdown-menu dropdown-fixed timeline_quick_select">

              % if period_optional:
              <li><a data-mode="">${ _("None") }</a></li>
              % endif

              <li><a data-mode="custom" class="timeline_quick_select_custom">${ _("Custom") }</a></li>
              <li role="separator" class="divider"></li>

              % for (value, unit, absolute, offset), label in timeline.quick.items():
                 <li><a data-value="${value}" data-unit="${unit}" data-mode="${'absolute' if absolute else 'relative'}" data-offset="${offset}">${label}</a></li>
              % endfor
            </ul>
          </div>
        </div>
      </div>

      % if not(inline):
      <div class="form-group collapse" style="margin-top: -15px;">
        <div class="col-sm-${label_width}">&nbsp;</div>
        <div class="col-sm-${12 - label_width}">
      % endif

          <div class="form-group-date ${ 'form-group' if inline else 'col-sm-6' }">
            <div>
              <label>${ _("Start:") }</label>
            </div>
            <div>
              % if "timeline_start" in env.request.menu_parameters:
                <input type="hidden" name="timeline_start" value="${env.request.menu_parameters['timeline_start']}" />
              % endif
              <input class="form-control input-${input_size} input-timeline-datetime timeline_start" type="text" placeholder="${ _("start") }" data-toggle="tooltip" title="${ _("Start date") }" data-trigger="hover" data-container="#main" data-name="timeline_start">
            </div>
          </div>

          <div class="form-group-date ${ 'form-group' if inline else 'col-sm-6' }">
            <div>
              <label>${ _("End:") }</label>
            </div>

            <div>
              % if "timeline_end" in env.request.menu_parameters:
               <input type="hidden" name="timeline_end" value="${env.request.menu_parameters['timeline_end']}" />
              % endif
              <input class="form-control input-${input_size} input-timeline-datetime timeline_end" type="text" placeholder="${ _("end") }" data-toggle="tooltip" title="${ _("End date") }" data-trigger="hover" data-container="#main" data-name="timeline_end">
            </div>
          </div>

      % if not(inline):
        </div>
      </div>
      % endif
    % endif

    % if inline:
      <button class="btn btn-primary btn-${ input_size } btn-submit disabled main_menu_form_submit" type="submit">
        <i class="fa fa-search fa-lg fa-fw"></i>
      </button>
    % endif
  </div>
</div>
%endif