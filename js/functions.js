/*function toggleVisibility(parent_id) {
 	top_section = document.getElementById(parent_id)
	child_nodes = top_section.childNodes
	child_divs = [ ]
	sections = top_section.getElementsByTagName("div")
 	
	for ( var i = 0; i < child_nodes.length; i++ ) {
		if ( child_nodes[i].className == "section" ) {
			child_divs.push(child_nodes[i])
		}
	}

	if ( child_divs[0]) {
		if  ( child_divs[0].style.display == 'none' ) {
			new_display = 'block';
		} else {
			new_display = 'none';
		}
	}
	
	for ( var i = 0; i < child_divs.length; i++ ) {
		child_divs[i].style.display = new_display;
	}
}
*/

function toggleVisibility(section_id) {
	section = document.getElementById(section_id);
	
	if ( section.style.display == 'none' ) {
		section.style.display = 'block';
	} else {
		section.style.display = 'none';
	}
}


function toggleFilteredColumnVisibility(column_id) {
	columns = new Array("classification", "source", "target", "analyzer");

	for ( var i=0; i < columns.length; i++ ) {
		popup = document.getElementById(columns[i]);

		if ( column_id == columns[i] ) {
			if ( popup.style.display == 'none' ) {
				popup.style.display = 'block';
			} else {
				popup.style.display = 'none';
			}
		} else {
			popup.style.display = 'none';
		}
	}
}
