function trigger_custom_date(enabled)
{
    $("#hidden_timeline_start").prop("disabled", !enabled);
    $("#hidden_timeline_end").prop("disabled", !enabled);
    $("#hidden_timeline_value").prop("disabled", enabled);
    $("#hidden_timeline_unit").prop("disabled", enabled);
    $("#hidden_timeline_absolute").prop("disabled", enabled);

    $("#main_menu_ng .form-group-date input").toggleClass("disabled", !enabled);

    if ( enabled ) {
        $("#main_menu_form_submit").removeClass("disabled");
        $("#timeline_quick_selected").html($("#timeline_quick_select_custom").text());
        update_date();
    }
}


function get_time(dt)
{
        return (dt.getTime() - (dt.getTimezoneOffset() * 60000)) / 1000;
}


function update_date_input() {
    var start = $("#timeline_start").datetimepicker("getDate");
    $("#hidden_timeline_start").val(start ? get_time(start) : "");

    var end = $("#timeline_end").datetimepicker("getDate");
    $("#hidden_timeline_end").val(end ? get_time(end) : "");

    return [start, end];
}

function update_date() {
    var ret = update_date_input();
    var start = ret[0], end = ret[1];

    if ( start > end ) {
        $(".input-timeline-datetime").closest(".form-group").addClass('has-error');
        $("#main_menu_form_submit").prop('disabled', true).addClass('error-date');
    } else {
        $(".input-timeline-datetime").closest(".form-group").removeClass('has-error');
        $("#main_menu_form_submit").prop('disabled', false).removeClass('error-date');
    }
}

function MainMenuInit (date_format) {
    $(".input-timeline-datetime").datetimepicker({
        "dateFormat": date_format,
        "onSelect": function() { trigger_custom_date(true); },
        "onClose": function() { trigger_custom_date(true); },
    });

    $(".main_menu_extra :input").on("change", function() {
        $("#main_menu_form_submit").removeClass("disabled");
    });

    $("#refresh-select a").on("click", function() {
        $("#refresh-value").text($(this).text());
        $("#main_menu_form_submit").removeClass("disabled");

        var second_reload = parseInt($(this).data("value"));
        if ( second_reload > 0 ) {
            $("#hidden_auto_apply_value").val(second_reload);
            window.mainmenu.setTimeout(second_reload);
            window.mainmenu.start();
        } else {
            $("#hidden_auto_apply_value").val("");
            window.mainmenu.stop();
        }
    });

    $("#timeline_quick_select a").on("click", function() {
        $("#hidden_timeline_value").val($(this).data("value"));
        $("#hidden_timeline_unit").val($(this).data("unit"));
        $("#hidden_timeline_absolute").val($(this).data("absolute"));
        $("#timeline_quick_selected").text($(this).text());

        if ( $(this).data("value") === "" ){
            trigger_custom_date(true);
        } else {
            trigger_custom_date(false);
            $("#main form").submit();
        }
     });
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


window.mainmenu = new PageReloader(function() { $("#main form").submit() },
                                   parseInt($("#hidden_auto_apply_value").val()));
