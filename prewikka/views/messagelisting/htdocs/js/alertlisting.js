var global_id = 0;

function _MessageListing() {

     this.set = function(type, state, columns_data) {
                if ( state == "default" )
                        return this.setDefault(type, columns_data);

                var ustate = (state == "current") ? "" : "_" + state;
                var tabletbl = columns_data[type + ustate];
                var table_aggregtbl = columns_data["aggregated_" + type + ustate];
                var special_data = columns_data["special"];

                this.setZero(type);

                var table = $("#" + type + " table.filter_table > tbody");
                var agtable = $("#" + type + " table.aggregation_table > tbody");

                this.setSpecial(type, state, columns_data);

                var cnt = 0;
                var got_append = 0;
                $(tabletbl).each(function(idx, values) {
                        var path = values[0]; var op = values[1]; var val = values[2];

                        if ( cnt++ > 0 ) {
                                got_append = 1;
                                table.find("tr:last a.append_entry").trigger('click');
                        }

                        if ( ! path )
                                return true;

                        table.find("tr:last .popup_input_field").prop("value", val);
                        table.find("tr:last .popup_input_field option").parent("select").val(val); /* select value */

                        if ( path != "__all__" ) {
                                table.find("tr:last .popup_select_field option[value='" + path + "']").prop("selected", true);

                                /*
                                 * the option might not exist at this time, so we have to explicitly create it (otherwise,
                                 * using Equals() later on will always return false since there is no operator selected).
                                 * The other fields will be populated on the .trigger("change").
                                 */
                                table.find("tr:last .popup_operator_select").html("<option value='" + op + "' selected='selected' />");

                                if ( got_append == 0 )
                                        table.find("tr:last .expert_mode").trigger("click");
                                else
                                        table.find("tr:last .popup_select_field").trigger("change");
                        } else {

                                table.find("tr:last .popup_select_field").hide();
                                table.find("tr:last .popup_select_field").prop("disabled", true);
                                table.find("tr:last .popup_select_field").trigger("change");
                        }
                });

                var cnt = 0;
                $(table_aggregtbl).each(function(idx, path) {
                        if ( cnt++ > 0 )
                                agtable.find("tr:last a.append_entry").trigger('click');

                        agtable.find("tr:last .popup_input_field option[value='" + path + "']").prop("selected", true);
                });
        };

        this.setSpecial = function(type, state, columns_data) {
                var ustate = (state == "current") ? "" : "_" + state;
                var special_data = columns_data["special"];

                $(special_data[type]).each(function(idx, path) {
                        var allval = columns_data[path + "_default"];
                        var checked_val = columns_data[path + ustate];

                        $(allval).each(function(idx, value) {
                                if ( $.inArray(value, checked_val) >= 0 )
                                        $("input[value='" + value + "']").prop("checked", true);
                                else
                                        $("input[value='" + value + "']").prop("checked", false);
                        });
                });
        };

        this.setZero = function(type) {
                var filter_table = $("#" + type + " table.filter_table > tbody");
                filter_table.find("tr:not(':first')").remove()
                filter_table.find("input[type=text]").val("")
                $("#" + type + " table.aggregation_table tr:not(':first')").remove()

                // reset to non expert mode.
                if ( filter_table.find(".td_container_path").children().is(":visible") )
                        filter_table.find(".expert_mode").click();
        };

        this.setDefault = function(type, columns_data) {
                this.setZero(type);
                this.setSpecial(type, "default", columns_data);

                var table = $("#" + type + " table.aggregation_table > tbody");
                var data = columns_data["aggregated_" + type + "_default"];

                var cnt = 0;
                $(data).each(function(idx, path) {
                        if ( cnt++ > 0 )
                                table.find("tr:last a.append_entry").trigger('click');

                        table.find("tr:last .popup_input_field option[value='" + path + "']").prop("selected", true);
                });
        };


        this._cloneForm = function (form) {
                var clone = $(form).clone();
                var selvals = [];

                $(form).filter("select").each(function() {
                        selvals.push($(this).val());
                });

                $(clone).filter("select").each(function() {
                        $(this).val(selvals.shift());
                });

                return clone;
        }


        this._inputEqual = function(a, b) {
                if ( a.type == "button" && b.type == "button" )
                        return true;

                if ( a.name != b.name )
                        return false;

                if ( a.checked != b.checked )
                        return false;

                if ( a.selected != b.selected )
                        return false;

                if ( a.value != b.value )
                        return false;

                return true;
        }

        this._equals = function (a, b) {
                if( ! a || ! b )
                        return false;

                if ( a.length != b.length )
                        return false;

                for ( var k = 0; k < a.length; k++ ) {
                        r = this._inputEqual(a[k], b[k]);
                        if ( r == false )
                                return false;
                }

                return true;
        };

        this.get_next_state = function(saved_forms, id, cstate) {
                var nextstate = null;
                var selector = "#" + id + " :input";

                if ( cstate == "current" ) {
                        if ( saved_forms[id]["saved"] && ! this._equals($(selector), saved_forms[id]["saved"]) )
                                nextstate = "saved";

                        else if ( saved_forms[id]["default"] && ! this._equals($(selector), saved_forms[id]["default"]) )
                                nextstate = "default";
                }

                else if ( cstate == "saved" ) {
                        if ( saved_forms[id]["default"] && ! this._equals($(selector), saved_forms[id]["default"]) )
                                nextstate = "default";

                        else if ( saved_forms[id]["current"] && ! this._equals($(selector), saved_forms[id]["current"]) )
                                nextstate = "current";
                }

                else if ( cstate == "default" ) {
                        if ( saved_forms[id]["current"] && ! this._equals($(selector), saved_forms[id]["current"]) )
                                nextstate = "current";

                        else if ( saved_forms[id]["saved"] && ! this._equals($(selector), saved_forms[id]["saved"]) )
                                nextstate = "saved";
                }

                return nextstate;
        };


        this.createSelectFromArray = function(varray, sclass, name_attr, selected) {
                var select = $("<select>").attr("name", name_attr).attr("class", sclass);

                $(varray).each(function() {
                        var option = $("<option>").attr("value", this).text(this);

                        if ( _messagelisting_title_array[this] )
                                option.attr("title", _messagelisting_title_array[this]);

                        select.append(option);
                });

                select.val(selected);
                return select;
        };
}


function MessageListing() {
        if ( ! window._messagelisting )
                window._messagelisting = new _MessageListing();

        return window._messagelisting;
}


 $(document).on("click", ".remove_entry", function() {
        $(this).parent().parent().remove();
 });

 $(document).on("click", ".append_entry", function() {
   var tr = _messagelisting._cloneForm($(this).parent().parent());
   var select = $(tr).children("td.td_container_path").children();
   var div_id = $(this).parent().parent().parent().parent().parent().parent().parent().parent().parent().prop("id");

   if ( $(this).parent().parent().parent().parent().is("table.aggregation_table") )
        $(select).prop("name", "aggregated_" + div_id);

   else {
        global_id += 1;

        var input = $(tr).children("td.td_container_value").children();
        $(tr).children("td.td_container_operator").children().prop("name", div_id + "_operator_" + global_id);
        $(input).prop("name", div_id + "_value_" + global_id);
        $(input).prop("value", "");
        $(input).find("option[value='none']").prop("selected", true);
        $(select).prop("name", div_id + "_object_" + global_id);
   }

   $(this).parents(".inline_filter").after(tr);
   $(select).trigger("change");
   $(tr).children("td.td_container_remove").html("<a class=\"remove_entry\">-</a>");
 });

  $(document).on("change", ".popup_select_field", function() {
          var td = $(this).parent();
          var str = $(this, "> option:selected").prop("value");
          var input = $(td).siblings(".td_container_value").children();

          // do not use visible here, this is called before the parent element is visible
          var advanced_mode = $(this).css("display") != "none";

          if ( _messagelisting_operator_array[str] && advanced_mode ) {
                var old_select = $(td).siblings(".td_container_operator").children();
                var old_value = $(old_select).children(":selected").prop("value");

                select = _messagelisting.createSelectFromArray(_messagelisting_operator_array[str], "popup_operator_select", $(old_select).prop("name"), old_value);
                $(old_select).replaceWith(select);
          }

          if ( _messagelisting_value_array[str] && advanced_mode ) {
                  select = _messagelisting.createSelectFromArray(_messagelisting_value_array[str], "popup_input_field", $(input).prop("name"), $(input).prop("value"));
                  $(input).replaceWith(select);
          }

          else {
                var n = document.createElement("input");
                n.setAttribute("type", "text");
                n.setAttribute("name", $(input).prop("name"));
                n.setAttribute("class", "popup_input_field");

                if ( $(input).prop("type") != "select-one" )
                        n.setAttribute("value", $(input).prop("value"));

                if ( old_value == '!' )
                        n.setAttribute("disabled", "disabled");

                $(input).replaceWith(n);
          }
 });


 $(document).on("click", ".expert_mode", function() {
        var tr = $(this).parent().parent();
        var td_container_path = $(tr).children(".td_container_path");
        var td_container_operator = $(tr).children(".td_container_operator");

        if ( ! $(td_container_path).children().is(":visible") ) {
                $(this).text("simple");
                $(this).parent().parent().children(".td_container_operator").children().show()
                $(td_container_path).children("select").show()
                $(td_container_path).children("input").prop("disabled", true)
                $(td_container_path).children("select").prop("disabled", false)
                $(td_container_operator).children("select").prop("disabled", false);
        } else {
                $(this).text("advanced");
                $(td_container_path).children().hide()
                $(this).parent().parent().children(".td_container_operator").children().hide()
                $(td_container_path).children("input").prop("disabled", false)
                $(td_container_path).children("select").prop("disabled", true)
                $(td_container_operator).children("select").prop("disabled", true);
        }

        // This is required so that the input is changed (from/to enum) when required.
        $(td_container_path).children("select").trigger("change");
});

$(document).on("change", ".popup_operator_select", function() {
        var str = $(this, "> option:selected").prop("value");
        if ( str == "!" )
                $(this).parent().next().children(".popup_input_field").prop("disabled", true);
        else
                $(this).parent().next().children(".popup_input_field").prop("disabled", false);
});
