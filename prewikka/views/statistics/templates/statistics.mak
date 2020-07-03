<link rel="stylesheet" type="text/css" href="statistics/css/statistics.css">

## We put the following styles here to ensure they are applied
## before the JS execution to avoid chart sizing problems

<style>
/* Force the scrollbar as soon as the page loads, to
 * have the correct width in the computation of the grid
 */
body, body.modal-open {
    overflow-y: scroll;
}

/* Adjust panel and grid */
.grid-stack .panel > .panel-body {
    padding: 0;
    height: calc(100% - 33px); /* 33px for the panel-heading height (height+border+padding in bootstrap) */
}

/* Period display to avoid scrollbar */
.period-display {
    position: absolute;
    bottom: 5px;
    width: 100%;
    text-align: center;
    display: none;
}
<%block name="statistics_styles_extension">
</%block>

</style>

<%
    labels = dict((label, _(label)) for label in (
        N_("Connection error"),
        N_("Failed to import the dashboard."),
    ))
%>

<div class="prewikka-view-config collapse">
  <p class="list-group-item">
    <input id="limit" name="limit" type="number" min="-1" max="${ 2**31-1 }" value="${ limit }" class="form-control input-sm" />
    <label for="limit">${ _("Limit") }</label>
  </p>

<%block name="statistics_view_parameters_extension">
</%block>

</div>

<%block name="statistics_header">
</%block>

<div class="grid-stack widget-listener" data-gs-column="12"></div>

<script type="text/javascript">
  $LAB.script("statistics/js/gridstack.all.js").wait()
       .script("statistics/js/uuid.js").wait()
       .script("statistics/js/dashboard.js").wait(function() {
<%block name="dashboard_scripts_extension">
</%block>
        prewikka_resource_register(Dashboard(${ html.escapejs(options) }));
  });
</script>
