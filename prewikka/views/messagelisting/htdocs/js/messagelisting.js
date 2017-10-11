function hidePopup() {
    $(".filter_popup_link + div").hide();
}

// Using #top_view avoids handling right click on Firefox
$(document).on("click", "#top_view", hidePopup);

$("#main").on("click", ".filter_popup_link + div", function(evt) {
    // Stop event propagation to top_view, but do not prevent default
    evt.stopPropagation();
});

prewikka_resource_register({
    destroy: function() {
        $(document).off("click", hidePopup);
    }
});
