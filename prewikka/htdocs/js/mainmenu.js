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



function update_date() {
    var start = $("#timeline_start").datetimepicker("getDate");
    $("#hidden_timeline_start").val(start ? start.getTime() / 1000 : "");

    var end = $("#timeline_end").datetimepicker("getDate");
    $("#hidden_timeline_end").val(end ? end.getTime() / 1000 : "");
}


function MainMenuInit (date_format) {
    $('#timeline_start').add('#timeline_end').datetimepicker({
        "dateFormat": date_format,
        "onSelect": function() { trigger_custom_date(true); }
    })
    .change(function() {
        update_date();
    });

    $("#main_menu_extra :input").on("change", function() {
        $("#main_menu_form_submit").removeClass("disabled");
    });

    $("#refresh-select a").on("click", function() {
        $("#refresh-value").text($(this).text());
        $("#main_menu_form_submit").removeClass("disabled");
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

if ( ! $("#hidden_auto_apply_value").val() )
    $("#hidden_auto_apply_value").val("60");
window.mainmenu.setTimeout($("#hidden_auto_apply_value").val());


$(document).on("click", "#auto_apply_button", function() {
    if ( $("#hidden_auto_apply_enable").val() == "true" ) {
        window.mainmenu.stop();

        $("#hidden_auto_apply_enable").val("false");
    } else {
        window.mainmenu.start();
        $("#hidden_auto_apply_enable").val("true");
    }
});

$(document).on("click", "#refresh-select a", function() {
    var second_reload = parseInt($(this).data("value"));

    if ( second_reload > 0 ) {
        $("#hidden_auto_apply_value").val(second_reload);
        $("#hidden_auto_apply_enable").val("true");

        window.mainmenu.setTimeout(second_reload);
        window.mainmenu.start();
    } else {
        $("#hidden_auto_apply_value").val("");
        $("#hidden_auto_apply_enable").val("false");

        window.mainmenu.stop();
    }
});

$(document).on("click", "a[href]", function() {
    window.mainmenu.stop();
});

