$(document).on("submit", "#main form", function(event) {
        var timeline_data = $(this).find("#timeline :input").serialize();

        /*
         * FIXME: centralized menu settings
         */
        if ( timeline_data ) {
                $("#topmenu").find(".topmenu_item_active").parent().find("div.topmenu_item a").each(function() {
                        $(this).attr("href", $(this).attr("href").split("?")[0] + "?" + timeline_data);
                });
        }
});


function PageReloader(callback, html_counter_cb) {
        this.second_reload  = 0;
        this.elapsed = 0;
        this.callback = callback;
        this.callback_installed = false;
        this.autorefresh_enabled = false;
        this.html_counter_callback = html_counter_cb;

        this.__pad = function(number) {
                if ( number < 10 )
                    return "0" + number;
                else
                    return number;
        };

        this.__autoApplyCounter = function() {
                this.started = false;

                if ( this.autorefresh_enabled == false )
                        return;

                if ( this.second_reload == 0 )
                        return this.__start();

                this.elapsed += 1;
                this.html_counter_callback(Math.floor(this.elapsed / 60) + ":" + this.__pad((this.elapsed % 60)));

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

        this.setTimeout = function(timestr) {
                var old = this.second_reload;
                var parselimit = timestr.split(":");

                if ( parselimit[0] && parselimit[1] && parselimit[2] )
                        this.second_reload = parselimit[0] * 3600 + parselimit[1] * 60 + parselimit[2] * 1;

                else if ( parselimit[0] && parselimit[1] )
                        this.second_reload = parselimit[0] * 60 + parselimit[1] * 1;

                else
                        this.second_reload = timestr;

                if ( this.second_reload != old || this.second_reload <= this.elapsed )
                        this.elapsed = 0;
        };

        this.reset = function(timestr) {
                this.elapsed = 0;
        };
};


window.mainmenu = new PageReloader(function() { $("#main form").submit() },
                                   function(elapsed) { $("#auto_apply_current").html(elapsed) });

if ( ! $("#timeline input[name=auto_apply_value]").val() )
       $("#timeline input[name=auto_apply_value]").val("1:00");
window.mainmenu.setTimeout($("#timeline input[name=auto_apply_value]").val());

$(document).on("focus", "#main form input[name='auto_apply_value']", function() {
        window.mainmenu.stop();
});


$(document).on("blur", "#main form input[name='auto_apply_value']", function() {
        var input = $("#timeline input[name=auto_apply_value]");

        if ( ! $(input).val() )
                $(input).val("1:00");

        window.mainmenu.setTimeout($(input).val());
        window.mainmenu.start();
});


$(document).on("click", ".auto_apply_button", function() {
        if ( $("#timeline input[name=auto_apply_enable]").val() == "true" ) {
                window.mainmenu.stop();

                $("#timeline input[name=auto_apply_enable]").val("false");
                $("#timeline #auto_apply_image").attr("src", "prewikka/images/play.png");
        } else {
                window.mainmenu.start();

                $("#timeline input[name=auto_apply_enable]").val("true");
                $("#timeline #auto_apply_image").attr("src", "prewikka/images/pause.png");
        }
});


$(document).on("click", "a[href]", function() {
        window.mainmenu.stop();
});
