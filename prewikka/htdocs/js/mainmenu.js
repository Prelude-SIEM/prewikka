"use strict";

function MainMenuInit(inline, start, end, date_format) {

    var that = this;

    that._root = $((inline) ? "#main_menu_ng" : "#main_menu_ng_block");
    that._start_picker = that._root.find(".timeline_start");
    that._end_picker = that._root.find(".timeline_end");

    this._init = function(start, end, date_format) {

        var options = {
            "dateFormat": date_format,
            "onSelect": function() { that.trigger_custom_date(true); },
            "onClose": function() { that.trigger_custom_date(true); },
        };

        that._start_picker = DatetimePicker(that._start_picker, start, options);
        that._end_picker = DatetimePicker(that._end_picker, end, options);
    };

    this.trigger_custom_date = function(enabled) {
        that._root.find("[name=timeline_start]").prop("disabled", !enabled);
        that._root.find("[name=timeline_end]").prop("disabled", !enabled);
        that._root.find("[name=timeline_value]").prop("disabled", enabled);
        that._root.find("[name=timeline_unit]").prop("disabled", enabled);
        that._root.find("[name=timeline_absolute]").prop("disabled", enabled);

        that._root.find(".form-group-date input").toggleClass("disabled", !enabled);

        if ( enabled ) {
            that._root.find(".main_menu_form_submit").removeClass("disabled");
            that._root.find(".timeline_quick_selected").html($(that._root.find(".timeline_quick_select_custom")).text());
            that.update_date();
        }

        /*
         * This will trigger a collapse only in non-inline mode.
         */
        that._root.find(".form-group.collapse").collapse((enabled) ? "show" : "hide");
    };

    this.update_date = function() {
        var start = that._start_picker.get_value();
        var end = that._end_picker.get_value() + 59 /* up to the end of the minute*/;

        if ( start > end ) {
            that._root.find(".input-timeline-datetime").closest(".form-group").addClass('has-error');
            that._root.find(".main_menu_form_submit").prop('disabled', true).addClass('error-date');
        } else {
            that._root.find(".input-timeline-datetime").closest(".form-group").removeClass('has-error');
            that._root.find(".main_menu_form_submit").prop('disabled', false).removeClass('error-date');
        }
    };

    that._root.find(".main_menu_extra :input").on("change", function() {
        that._root.find(".main_menu_form_submit").removeClass("disabled");
    });

    that._root.find(".refresh-select a").on("click", function() {
        that._root.find(".refresh-value").text($(this).text());
        that._root.find(".main_menu_form_submit").removeClass("disabled");

        var second_reload = parseInt($(this).data("value"));
        if ( second_reload > 0 ) {
            that._root.find("[name=auto_apply_value]").val(second_reload);
            window.mainmenu.setTimeout(second_reload);
            window.mainmenu.start();
        } else {
            that._root.find("[name=auto_apply_value]").val("");
            window.mainmenu.stop();
        }
    });

    that._root.find(".timeline_quick_select a").on("click", function() {
        that._root.find("[name=timeline_value]").val($(this).data("value"));
        that._root.find("[name=timeline_unit]").val($(this).data("unit"));
        that._root.find("[name=timeline_absolute]").val($(this).data("absolute"));
        that._root.find(".timeline_quick_selected").text($(this).text());

        if ( $(this).data("value") === "" ){
            that.trigger_custom_date(true);
        } else {
            that.trigger_custom_date(false);
            if ( inline )
                $(this).closest("form").submit();
        }
    });

    this._init(start, end, date_format);

}


function PageReloader(callback, second) {
    this.second_reload = second;
    this.elapsed = 0;
    this.callback = callback;
    this.callback_installed = false;
    this.autorefresh_enabled = false;

    this.__autoApplyCounter = function() {
        this.started = false;

        if ( this.autorefresh_enabled == false )
            return;

        if ( this.second_reload == 0 )
            return this.__start();

        this.elapsed += 1;

        if ( this.elapsed != this.second_reload )
            return this.__start();

        else if ( this.elapsed == this.second_reload ) {
            this.elapsed = 0;

            if ( $.active == 0 )
                this.callback();
        }
    };

    this.__start = function() {
        if ( this.autorefresh_enabled && ! this.started ) {
            setTimeout($.proxy(this.__autoApplyCounter, this), 1000);
            this.started = true;
        }
    };

    this.start = function() {
        this.autorefresh_enabled = true;
        this.__start();
    };

    this.stop = function() {
        this.autorefresh_enabled = false;
    };

    this.setTimeout = function(second) {
        this.second_reload = second;
    };

    this.reset = function(timestr) {
        this.elapsed = 0;
    };
};


window.mainmenu = new PageReloader(function() { $("#main_menu_ng").closest("form").submit() },
                                   parseInt($("#main_menu_ng [name=auto_apply_value]").val()));
