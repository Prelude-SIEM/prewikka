$(document).on("click", "legend a", function() {
    $(this).parent().next().toggle('normal');
    return false;
});