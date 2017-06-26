<%!
from datetime import datetime
from prewikka.localization import format_datetime

entry_value_classes = ("section_alert_entry_value_normal", "section_alert_entry_value_emphasis")
%>

<%def name="display_table(section, depth)">
    % for table in section["tables"]:
        % if depth == 0 and loop.index > 0 and table["style"].find("inline") == -1:
            <br/>
        % endif

        <table class="${table["class"]}" style="${table["style"]}">

        % for row in table["rows"]:
            <tr>
            % for col in row:
                % if col["header"]:
                    <th>${col["name"]}</th>
                % elif col["tables"]:
                    <td>${ display_table(col, depth + 1) }</td>
                % else:
                    <td>${col["name"]}</td>
                % endif
            % endfor
            </tr>
        % endfor
            </table>
    % endfor
</%def>


<%def name="display_node(sections)">
    % for section in sections:
        <div class="panel panel-theme">
            <div class="panel-heading">
                <h3 class="panel-title">
                    <a class="section-toggle">${section["title"]}</a>
                </h3>
            </div>
            <div class="panel-body" style="display: ${section["display"]}; width: 100%;">
            ${ display_table(section, 0) }

            % if section["entries"]:
                <table class="section_alert_entries">
                % for entry in section["entries"]:
                    <tr class="section_alert_entry">
                    % if entry["name"]:
                        <th style="text-align: left; width:150px;">${entry["name"]}</th>
                    % endif

                    <%
                        if isinstance(entry.value, datetime):
                            entry.value = format_datetime(entry.value)
                    %>

                        <td class="${entry_value_classes[entry["emphase"]]}">${entry["value"]}</td>
                    </tr>
                % endfor
                </table>
            % endif

        % if section["sections"]:
            ${ display_node(section["sections"]) }
        % endif

        </div>
    </div>
    % endfor
</%def>

<div class="container">
  <div class="widget" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="false" data-draggable="true" data-widget-options="modal-lg">

    <script type="text/javascript">
        $LAB.script("messagesummary/js/messagesummary.js");
    </script>

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">&times;</button>
      <h4 class="modal-title">${ _("Summary") }</h4>
    </div>

    <div class="modal-body">
      ${ display_node(sections) }
    </div>

    <div class="modal-footer">
      <button class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${ _('Close') }</button>
    </div>
  </div>
</div>
