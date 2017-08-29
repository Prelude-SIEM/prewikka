<%!
from prewikka.utils import html, json
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
        colNames: ["${ _('Name') }", "${ _('Schedule') }", "${ _('User') }", "${ _('Last execution') }", "${ _('Next execution') }" ],
        colModel: [
            {name: 'name', width: 10},
            {name: 'schedule', width: 8},
            {name: 'user', width: 10},
            {name: 'last', width: 10, search: false, sorttype: function(value, row) {return row.last_date;} },
            {name: 'next', width: 10, search: false, sorttype: function(value, row) {return row.next_date;} },
        ],
        multiselect: true,
        data: ${ html.escapejs(data) },
        globalSearch: false,

        rowattr: function(rd, cur, rowid) {
            var cl = "";

            if ( cur.error ) {
                prewikka_json_dialog(cur.error, { class: "cronjob-error-dialog cronjob-error-dialog-" + erridx });
                erridx += 1;
            }

            if ( typeof(rd.last) == "object" )
                cl += " danger";

            if ( cl )
                return { "class": cl };
        }
    }).done(function() {
        $('[data-toggle="popover"]').popover();
    });

    $(".cronjob-enable").click(function(e) {
        grid.ajax({ url: "${ url_for('.enable') }" });
    });

    $(".cronjob-disable").click(function(e) {
        grid.ajax({ url: "${ url_for('.disable') }" });
    });

    $(".cronjob-error").click(function(e) {
        $(".cronjob-error-dialog-" + $(".cronjob-error").index(this)).modal('show');
    });
})();

</script>

<table id="cronjobs"></table>

<div class="footer-buttons form-inline">
    <button type="button" class="btn btn-danger needone cronjob-disable"><i class="fa fa-times"></i> ${ _("Disable") }</button>
    <button type="button" class="btn btn-success needone cronjob-enable"><i class="fa fa-check"></i> ${ _("Enable") }</button>
</div>
