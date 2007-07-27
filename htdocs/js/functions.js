var cur_visible = null;
var autorefresh_possible = true;


function toggleVisibility(section_id) {
    section = document.getElementById(section_id);

    if ( section.style.display != 'block' ) {
        autorefresh_possible = false;
        section.style.display = 'block';
    } else {
        autorefresh_possible = true;
        section.style.display = 'none';
    }
}


function toggleVisibilityUnique(section_id)
{
    if ( cur_visible )
        cur_visible.style.display = 'none';

    section = document.getElementById(section_id);
    if ( cur_visible == section ) {
        cur_visible = null;
        autorefresh_possible = true;
        return;
    }

    toggleVisibility(section_id);

    if ( section.style.display == 'block' )
        cur_visible = section;
    else
        cur_visible = null;
}


function toggleFilteredColumnVisibility(column_id) {
    toggleVisibilityUnique(column_id);
}

function checkBoxByName(name, value) {
    for (var i = 0; i < document.forms[0].elements.length; i++ ) {
         var elem = document.forms[0].elements[i];

        if ( elem.name == name ) {
             elem.checked = value;
         }
     }
}

