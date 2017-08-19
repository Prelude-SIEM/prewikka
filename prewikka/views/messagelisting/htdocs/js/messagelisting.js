$("#main").click(function() {
    $(".filter_popup_link + div").hide();
});

$(".filter_popup_link + div").click(function(evt) {
    evt.stopPropagation();
});
