<%!
from prewikka.utils import html
%>

<script type="text/javascript">
"use strict";

(function() {
    /*
     * Remove any previously loaded error.
     */
    $(".cronjob-error-dialog").remove();

    var erridx = 0;
    var grid = CommonListing('table#cronjobs', {'title': "${_('Scheduled Jobs')}" }, {
        colModel: [
            {name: 'name', label: "${ _('Name') }", width: 10},
            {name: 'schedule', label: "${ _('Schedule') }", width: 8, sortable: false},
            {name: 'user', label: "${ _('User') }", width: 10},
            {name: 'last', label: "${ _('Last execution') }", width: 10},
            {name: 'next', label: "${ _('Next execution') }", width: 10},
        ],
        datatype: "json",
        url: "${url_for('CrontabView.ajax_listing')}",
        multiSort: false,
        useSearchbar: true,
        pager: false,
        reloadInterval: 10,

        rowattr: function(rd, cur, rowid) {
            var cl = "";

            if ( cur.error ) {
                prewikka_json_dialog(cur.error, {
                    class: "cronjob-error-dialog cronjob-error-dialog-" + erridx,
                    allow_error_duplicates: true
                });
                erridx += 1;
            }

            if ( typeof(rd.last) == "object" )
                cl += " danger";

            if ( cl )
                return { "class": cl };
        }
    }, ${html.escapejs(env.request.parameters["jqgrid_params_cronjobs"])}).done(function() {
        $('[data-toggle="popover"]').popover();
    });

    $(".cronjob-enable").click(function(e) {
        grid.ajax({ url: "${ url_for('.enable') }" });
    });

    $(".cronjob-disable").click(function(e) {
        grid.ajax({ url: "${ url_for('.disable') }" });
    });

    $("#cronjobs").on("click", ".cronjob-error", function(e) {
        $(".cronjob-error-dialog-" + $(".cronjob-error").index(this)).modal('show');
    });
})();

</script>

<table id="cronjobs"></table>

<div class="footer-buttons form-inline">
    <button type="button" class="btn btn-danger needone cronjob-disable"><i class="fa fa-times"></i> ${ _("Disable") }</button>
    <button type="button" class="btn btn-success needone cronjob-enable"><i class="fa fa-check"></i> ${ _("Enable") }</button>
</div>
