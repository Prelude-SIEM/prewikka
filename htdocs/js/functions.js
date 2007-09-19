var autorefresh_possible = true;

$(document).ready(function(){
  var $cache = null;
  var $cachef = null;

  $.fn.popupUnique = function(animshow, animhide) {
	if ( this.is(':visible') ) {
		$cachef($cache);
		$cache = null;
		autorefresh_possible = true;
	} else {
		autorefresh_possible = false;

		animshow(this);
		if ( $cache )
			$cachef($cache);
		$cachef = animhide;
		$cache = this;
	}
	
	return false;
  };

  $.fn.check = function(mode){
        return this.each(function() { this.checked = mode; } );
  };

  $(".popup_menu_toggle").click(function(){
    $(this).next().popupUnique(function(data){data.show('fast')}, function(data){data.hide('fast')});
  });


 if ( navigator.userAgent.indexOf("Konqueror") != -1 )
        $(".popup_menu").hide();
});
