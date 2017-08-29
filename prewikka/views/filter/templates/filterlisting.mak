<style>
.check-green {
    font-size: 18px;
    color: green;
    line-height: 1;
}

.check-green:after {
    content: "\2713";
}
</style>

<script type="text/javascript">

function type_formatter(cellValue, options, rowObject) {
    var elem = $("<p>", {"class": cellValue ? "check-green" : ""});
    return elem[0].outerHTML;
}

$LAB.wait(function() {

    var text = {'title': "${_('Filters')}", 'new': "${_('New filter')}"};

    CommonListing('table#filters', text, {
        editLink: "${url_for('FilterView.edit')}",
        deleteLink: "${url_for('FilterView.delete')}",
        colNames: ["${_('Name')}"].concat(${html.escapejs(col_names)}).concat(["${_('Description')}"]),
        colModel: [
            {name: 'name', width: 20},
            % for typ in col_idents:
            {name: "${typ}", width: 10, align: "center", formatter: type_formatter},
            % endfor
            {name: 'description', width: 50, sortable: false}
        ],
        data: ${html.escapejs(data)}
    });

});

</script>

<div>
  <table id="filters"></table>
  <div class="footer-buttons">
    <button type="button" class="btn btn-primary button-add"><i class="fa fa-plus"></i> ${_("Create")}</button>
    <button type="button" class="justone btn btn-primary button-duplicate"><i class="fa fa-clone"></i> ${_("Duplicate")}</button>
    <button type="button" class="needone btn btn-danger button-delete" data-confirm="${_("Delete the selected filters?")}"><i class="fa fa-trash"></i> ${_("Delete")}</button>
  </div>
</div>
