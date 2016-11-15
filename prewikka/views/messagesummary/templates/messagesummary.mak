<link rel="stylesheet" type="text/css" href="messagesummary/css/messagesummary.css">

<script type="text/javascript">
    $LAB.script("messagesummary/js/messagesummary.js");
</script>

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

        % if table["odd_even"]:
            <table class="${table["class"]} table_row_${loop.cycle('even', 'odd')}" style="${table["style"]}">
        % else:
            <table class="${table["class"]}" style="${table["style"]}">
        % endif

        <% row_class = "" %>

        % for row in table["rows"]:
            <tr class="${row_class}" style="">
            % for col in row:
                % if col["header"]:
                    <th>${col["name"]}</th>
                    <% row_class = "table_row_even" %>
                % elif col["tables"]:
                    <td>${ display_table(col, depth + 1) }</td>
                    <% row_class = "" %>
                % else:
                    <td class="${col["class"]}">${col["name"]}</td>
                % endif
            % endfor
            </tr>
        % endfor
            </table>
    % endfor
</%def>


<%def name="display_node(sections)">
    % for section in sections:
        <fieldset class="fieldset_heading">
            <legend><a href="#">${section["title"]}</a></legend>
            <div style="display: ${section["display"]}; width: 100%;">
            ${ display_table(section, 0) }

            % if section["entries"]:
                <table class="section_alert_entries">
                % for entry in section["entries"]:
                    <tr class="section_alert_entry table_row_${loop.cycle('even', 'odd')}">
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
    </fieldset>
    % endfor
</%def>

<div id="fieldset_page">
 ${ display_node(sections) }
</div>
