$(function() {
  $(document).on("click", "#top_view", function() {
    $(".filter_popup_link + div").hide();
  });

  $(document).on("click", ".filter_popup_link + div", function(evt) {
    evt.stopPropagation();
  });
});
