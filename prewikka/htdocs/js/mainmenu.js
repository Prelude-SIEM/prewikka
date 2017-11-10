"use strict";

function MainMenuInit(inline, start, end, date_format) {
    var that = {};
    var root = $((inline) ? "#main_menu_ng" : "#main_menu_ng_block");

    var options = {
        "dateFormat": date_format,
        "onSelect": function() { that.trigger_custom_date(true); },
        "onClose": function() { that.trigger_custom_date(true); },
    };

    var start_picker = DatetimePicker(root.find(".timeline_start"), start, options);
    var end_picker = DatetimePicker(root.find(".timeline_end"), end, options, 59);

    that.trigger_custom_date = function(enabled) {
        root.find("[name=timeline_start]").prop("disabled", !enabled);
        root.find("[name=timeline_end]").prop("disabled", !enabled);
        root.find("[name=timeline_value]").prop("disabled", enabled);
        root.find("[name=timeline_unit]").prop("disabled", enabled);
        root.find("[name=timeline_absolute]").prop("disabled", enabled);

        root.find(".form-group-date input").toggleClass("disabled", !enabled);

        if ( enabled ) {
            root.find(".main_menu_form_submit").removeClass("disabled");
            root.find(".timeline_quick_selected").html($(root.find(".timeline_quick_select_custom")).text());
            that.update_date();
        }

        /*
         * This will trigger a collapse only in non-inline mode.
         */
        root.find(".form-group.collapse").collapse((enabled) ? "show" : "hide");
    };

    that.update_date = function() {
        var start = start_picker.get_value();
        var end = end_picker.get_value();

        if ( start > end ) {
            root.find(".input-timeline-datetime").closest(".form-group").addClass('has-error');
            root.find(".main_menu_form_submit").prop('disabled', true).addClass('error-date');
        } else {
            root.find(".input-timeline-datetime").closest(".form-group").removeClass('has-error');
            root.find(".main_menu_form_submit").prop('disabled', false).removeClass('error-date');
        }
    };

    root.find(".main_menu_extra :input").on("change", function() {
        root.find(".main_menu_form_submit").removeClass("disabled");
    });

    root.find(".refresh-select a").on("click", function() {
        root.find(".refresh-value").text($(this).text());
        root.find(".main_menu_form_submit").removeClass("disabled");

        var second_reload = parseInt($(this).data("value"));
        if ( second_reload > 0 ) {
            root.find("[name=auto_apply_value]").val(second_reload);
            window.mainmenu.setTimeout(second_reload);
            window.mainmenu.start();
        } else {
            root.find("[name=auto_apply_value]").val("");
            window.mainmenu.stop();
        }
    });

    root.find(".timeline_quick_select a").on("click", function() {
        root.find("[name=timeline_value]").val($(this).data("value"));
        root.find("[name=timeline_unit]").val($(this).data("unit"));
        root.find("[name=timeline_absolute]").val($(this).data("absolute"));
        root.find(".timeline_quick_selected").text($(this).text());

        if ( $(this).data("value") === "" ){
            that.trigger_custom_date(true);
        } else {
            that.trigger_custom_date(false);
            if ( inline )
                $(this).closest("form").submit();
        }
    });

    return that;
}


function PageReloader(callback, second) {
    var that = {}

    that.second_reload = second;
    that.elapsed = 0;
    that.callback = callback;
    that.callback_installed = false;
    that.autorefresh_enabled = false;

    that.__autoApplyCounter = function() {
        that.started = false;

        if ( that.autorefresh_enabled == false )
            return;

        if ( that.second_reload == 0 )
            return that.__start();

        that.elapsed += 1;

        if ( that.elapsed != that.second_reload )
            return that.__start();

        else if ( that.elapsed == that.second_reload ) {
            that.elapsed = 0;

            if ( $.active == 0 )
                that.callback();
        }
    };

    that.__start = function() {
        if ( that.autorefresh_enabled && ! that.started ) {
            setTimeout($.proxy(that.__autoApplyCounter, this), 1000);
            that.started = true;
        }
    };

    that.start = function() {
        that.autorefresh_enabled = true;
        that.__start();
    };

    that.stop = function() {
        that.autorefresh_enabled = false;
    };

    that.setTimeout = function(second) {
        that.second_reload = second;
    };

    that.reset = function(timestr) {
        that.elapsed = 0;
    };

    return that;
};


window.mainmenu = PageReloader(function() { $("#main_menu_ng").closest("form").submit() },
                               parseInt($("#main_menu_ng [name=auto_apply_value]").val()));
