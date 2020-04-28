function startRiskOverviewRefresh(url) {
    var reloader;

    function reload() {
        $.ajax({
            url: url,
            prewikka: { bypass: true, spinner: false, target: PrewikkaAjaxTarget.LAYOUT }
        }).done(function(data) {
            $("#nav_top_view_header .top_view_header_riskoverview").remove();
            $("#nav_top_view_header").append(data.content);
        }).fail(function(xhr, status, error) {
            if ( xhr.status == 401 )
                reloader.stop();
        });
    }

    reloader = AjaxReloader(reload, 60);

    $(document).on("submit", "#main form", function() {
        if ( $(this).find("#main_menu_ng").length )
            reloader.stop();
    });

    $(document).on("submit-complete", "#main form", function() {
        if ( $(this).find("#main_menu_ng").length ) {
            reloader.stop();
            reload();
            reloader.start();
        }
    });

    reload();

}

