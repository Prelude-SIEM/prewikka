<script type="text/javascript">
<%!
from prewikka.utils import json
%>

var current_type = '${fltr.type or "alert"}';

var _FILTER_HTML = <%block filter="json.dumps">
<div class="form-horizontal form-filter" id="form_filter_example" data-value="example">
  <div class="form-group">
    <label class="col-sm-2 control-label" id="label_example"></label>
    <div class="col-sm-10">
      <div class="col-sm-4">
        <select class="form-control" id="object_example" name="object_example">
          <option value="" disabled selected>${ _("Select an IDMEF path") }</option>
        </select>
      </div>

      <div class="col-sm-8">
        <div class="col-xs-3">
          <select class="form-control" id="operator_example" name="operator_example">
            <option value="" disabled selected>${ _("Operator") }</option>
          % for operator, description in operators:
            <option value="${operator}" title="${description}">${operator}</option>
          % endfor
          </select>
        </div>

        <div class="col-xs-9">
          <div class="input-group">
            <input type="text" class="form-control" id="value_example" name="value_example" placeholder="${ _("value") }">
            <span class="input-group-btn">
              <div class="btn btn-default add_entry"><i class="fa fa-plus"></i></div>
              <div class="btn btn-default del_entry" id="button_example"><i class="fa fa-minus"></i></div>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</%block>


function resetFilterType(type)
{
    current_type = type
    $("#form_filter_objects").html("");
    newFilterElement('A', '', '', '');
}

function newFilterElement(name, idmef_object, idmef_operator, object_value) {
    var last_name = $(".form-filter").last().data("value");
    if ( ! name ) {
        if ( last_name !== undefined ) {
            name = last_name;
            if ( name.charAt(name.length - 1) == "Z" ) {
                name = name.concat("A");
            } else {
                name = name.substr(0, name.length - 1) +
                             String.fromCharCode(name.charCodeAt(name.length - 1) + 1);
            }
        } else {
            name = "A";
        }
    }

    if ( current_type === 'alert' ) {
        var options = ${alert_objects | n,json.dumps};
    } else {
        var options = ${generic_objects | n,json.dumps};
    }

    $("#form_filter_objects").append(_FILTER_HTML);

    $.each(options, function(index, option) {
        $('#object_example').append($("<option></option>").attr("value", option).text(option));
    });

    $("#form_filter_example").data("value", name).attr("id", "form_filter_" + name);
    $("#label_example").html(name).attr("id", "label_" + name);
    $("#object_example").attr("name", "object_" + name).val(idmef_object).attr("id", "object_" + name);
    $("#operator_example").attr("name", "operator_" + name).val(idmef_operator).attr("id", "operator_" + name);
    $("#value_example").attr("name", "value_" + name).val(object_value).attr("id", "value_" + name);
    $("#button_example").attr("id", "button_" + name);

}

$(document).ready(function() {

    $("input[value=filter]").click(function() {
        $(".fieldset_heading legend").text("${ _("Available filters") }");
        $("#curtype").prop("value", "filter");
        $(".filter_only").show();
    });
    $("input[value=filter]").trigger("click");


    $("#form_filter_objects").on("click", ".add_entry", function() {
        newFilterElement('', '', '', '');
    });

    $("#form_filter_objects").on("click", ".del_entry", function() {
        var entry = $(this).parents('.form-filter');
        if ( entry.data("value") != "A" ) {
            entry.remove();
        }
    });

    $("#filter_type").change(function() {
        resetFilterType($(this).val());
    });
});

</script>

<div class="container">

<form action="${document.href}" method="post">

<fieldset class="fieldset_heading">
<legend>${ _("Available filters") }</legend>

  <div class="input-group">
    <select class="filter_only form-control" name="filter_name">
      <option value="">${ _("Select a filter") }</option>
    % for f in filter_list:
      <option value="${f}" ${'class="selected"' if f == fltr.name else '' | n }>${f}</option>
    % endfor
    </select>
    <span class="input-group-btn">
      <button class="btn btn-default" type="submit" name="mode" value="${ _("Load") }"><i class="fa fa-cloud-download"></i> ${ _("Load") }</button>
      <button class="btn btn-danger" type="submit" name="mode" value="${ _("Delete") }" data-confirm="${ _("Delete this filter?") }"><i class="fa fa-trash"></i> ${ _("Delete") }</button>
    </span>
  </div>
</fieldset>

</form>

<form action="${document.href}" method="post">

<fieldset class="fieldset_heading">
<legend>${ _("Add / Modify") }</legend>

<div class="filter_only">
<p>
 <i>${ _("You are in the process of creating a new Prelude filter.") }</i>
</p>
<p>
 <i>${ _("Filters can be selected while on the alerts view, using the control menu in the top right corner.") }</i>
</p>
</div>

<br />

<div class="form-horizontal">
  <div class="form-group">
    <label for="filter_type" class="col-sm-2 control-label">${ _("Filter Type:") }</label>

    <div class="col-sm-10">
      <select id="filter_type" class="form-control" name="filter_type">
        %for type, name in (("alert", _("Alert")), ("heartbeat", _("Heartbeat")), ("generic", _("Generic (Alert and Heartbeat)"))):
          <option ${ selected(type == fltr.type) } value="${type}">${name}</option>
        %endfor
      </select>
    </div>
  </div>
</div>
<hr/>

<div id="form_filter_objects">
</div>

<script type="text/javascript"><!--
$.each(${elements | n,json.dumps}, function(i, element) {
    newFilterElement(element.name, element.object, element.operator, element.value);
});
//--></script>

<br />

<div class="form-horizontal">
  <div class="form-group">
    <label for="filter_formula" class="col-sm-2 control-label">${ _("Formula:") }</label>
    <div class="col-sm-10">
      <input class="form-control" type="text" id="filter_formula" name="filter_formula" value="${fltr.formula}" placeholder="${ _("Eg. (A AND B) OR (C AND D)") }"/>
    </div>
  </div>

  <div class="form-group">
    <label for="filter_name" class="col-sm-2 control-label">${ _("Name:") }</label>
    <div class="col-sm-10">
      <input class="form-control" type="text" id="filter_name" name="filter_name" value="${fltr.name}" placeholder="${ _("Filter name") }"/>
    </div>
  </div>

  <div class="form-group">
    <label for="filter_comment" class="col-sm-2 control-label">${ _("Comment:") }</label>
    <div class="col-sm-10">
      <textarea class="form-control" id="filter_comment" name="filter_comment" rows="4" cols="55">${fltr.comment}</textarea>
    </div>
  </div>
</div>

<button class="pull-right btn btn-primary" type="submit" name="mode" value="${ _("Save") }"><i class="fa fa-save"></i> ${ _("Save") }</button>
</fieldset>

% if fltr.name:
  <input type="hidden" name="load" value="${fltr.name}">
% endif
</form>

</div>
