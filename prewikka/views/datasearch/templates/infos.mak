<table class="table table-condensed">
  <tr>
    <td>${ _("Field") }</td>
    <td colspan=2>${ selected_field }</td>
  </tr>
  % for idx, (value, occur) in enumerate(selected_occur):
  <tr>
    % if idx == 0:
    <td rowspan=${ len(selected_occur) }>${ _("Occurrence") }</td>
    % endif
    <td><span class="badge">${ occur }</span></td>
    <td>${ value }</td>
  </tr>
  % endfor
</table>
