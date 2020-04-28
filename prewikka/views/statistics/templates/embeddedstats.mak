<div class="container">
  <div class="widget ui-front" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="false" data-draggable="true" data-widget-options="modal-xl">
    <link rel="stylesheet" type="text/css" href="statistics/css/statistics.css">

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">&times;</button>
      <h5 class="modal-title">${ modal_title }</h5>
    </div>

    <div class="modal-body">
      ## The goal of this form is to avoid opening a modal when the mainmenu
      ## is submitted, in case the page was opened in a new tab
      <form action="${ url_render }" class="no-widget"></form>
      <%block name="dashboard_intro">
      </%block>

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
    height: calc(100% - 48px); /* 48px for the panel-heading height (height+border+padding in bootstrap) */
}

<%block name="dashboard_styles_extension">
</%block>

</style>

<%
    labels = dict((label, _(label)) for label in (
        N_("Connection error"),
    ))
%>

<div class="grid-stack ${typestats}stats" data-gs-column="12"></div>

<script type="text/javascript">

  $LAB.script("statistics/js/gridstack.all.js").wait()
       .script("statistics/js/uuid.js").wait()
       .script("statistics/js/dashboard.js").wait(function() {

<%block name="dashboard_scripts_extension">
</%block>
        prewikka_resource_register(Dashboard(${ html.escapejs(options) }));
  });

</script>
  </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${_("Close")}</button>
      </div>
  </div>
</div>
