var cur_visible = null;

function toggleVisibility(section_id, mode) {
	section = document.getElementById(section_id);
	
	if ( section.style.display != mode ) {
		cur_visible = section;
		section.style.display = mode;
	} else {
		section.style.display = 'none';
	}
}


function toggleVisibilityUnique(section_id, mode) 
{
	if ( cur_visible )
		section.style.display = 'none';

	section = document.getElementById(section_id);
	if ( section == cur_visible ) {
		cur_visible = null;
		return;
	}

	toggleVisibility(section_id, mode);
}


function toggleFilteredColumnVisibility(column_id) {
	columns = new Array("classification", "source", "target", "analyzer");

	for ( var i=0; i < columns.length; i++ ) {
		popup = document.getElementById(columns[i]);

		if ( column_id == columns[i] ) {
			if ( popup.style.display != 'block' ) {
				popup.style.display = 'block';
			} else {
				popup.style.display = 'none';
			}
		} else {
			popup.style.display = 'none';
		}
	}
}

function checkBoxByName(name, value) {
	for (var i = 0; i < document.forms[0].elements.length; i++ ) {
 		var elem = document.forms[0].elements[i];
 		
		if ( elem.name == name ) {
 			elem.checked = value;
 		}
 	}
}
