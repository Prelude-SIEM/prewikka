$(document).on("click", "a.section-toggle", function() {
    $(this).closest(".panel-heading").siblings(".panel-body:first").slideToggle();
    return false;
});