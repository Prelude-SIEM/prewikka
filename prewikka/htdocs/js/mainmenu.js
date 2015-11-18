function disable_date () {
    $("#hidden_timeline_start").val("");
    $("#hidden_timeline_end").val("");
    $("#main_menu_ng .form-group-date input").addClass("disabled");
}

function MainMenuInit (date_format) {
    function enable_date () {
        $("#hidden_timeline_value").val("");
        $("#hidden_timeline_unit").val("");
        $("#main_menu_ng .form-group-date input").removeClass("disabled");
        $("#timeline_quick_selected").html($("#timeline_quick_select_custom").html());
        update_date();
    }

    function update_date() {
        var start = $("#timeline_start").datetimepicker("getDate");

        if ( start ) {
            $("#hidden_timeline_start").val(start.getTime()/1000);
        } else {
            $("#hidden_timeline_start").val("");
        }

        var end = $("#timeline_end").datetimepicker("getDate");

        if ( end ) {
            $("#hidden_timeline_end").val(end.getTime()/1000);
        } else {
            $("#hidden_timeline_end").val("");
        }
    }

    $('#timeline_start').add('#timeline_end').datetimepicker({
        "dateFormat": date_format,
        "onSelect": function() {
            $("#main_menu_form_submit").removeClass("disabled");
            enable_date();
        }
    })
    .change(function() {
        update_date();
    });

    $("#main_menu_extra :input").on("change", function() {
        $("#main_menu_form_submit").removeClass("disabled");
    });

    $("#refresh-select a").on("click", function() {
        $("#refresh-value").html($(this).html());
        $("#main_menu_form_submit").removeClass("disabled");
    });

    $("#timeline_quick_select a").on("click", function() {
        $("#main_menu_form_submit").removeClass("disabled");
        $("#hidden_timeline_value").val($(this).data("value"));
        $("#hidden_timeline_unit").val($(this).data("unit"));
        $("#timeline_quick_selected").html($(this).html());

        if ( $(this).data("value") === "" ){
            enable_date();
        } else {
            disable_date();
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

