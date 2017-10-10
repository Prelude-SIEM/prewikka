"use strict";

function JSONRegistry() {
    var ret = {};

    ret._prototypes = {};

    ret["register"] = function(name, proto) {
        ret._prototypes[name] = proto;
    }

    return ret;
}

window.json_registry = JSONRegistry();


function _revive(obj)
{
    var type = obj["__prewikka_class__"][0];
    var kwargs = obj["__prewikka_class__"][1];
    var proto = window.json_registry._prototypes[type];

    if ( ! proto ) {
        var msg = "Class " + type + " not found.";
        console.warn(msg);  /* Make sure this is logged, since LABjs swallows exceptions */
        throw new TypeError(msg);
    }

    return proto(kwargs);
}


function _can_revive(obj)
{
    return (obj && typeof(obj) == "object" && obj["__prewikka_class__"]);
}


function _reviver_func(name, value)
{
    return (_can_revive(value)) ? _revive(value) : value;
}


function _prewikka_revive(obj)
{
    if ( typeof(obj) != "object" )
        return obj;

    for ( var i in obj ) {
        var elem = _prewikka_revive(obj[i]);

        if ( _can_revive(elem) )
            obj[i] = _revive(elem);
        else
            obj[i] = elem;
    }

    return obj;
}



var _orig_func = JSON.parse;
JSON.parse = function(input) {
    return _orig_func(input, _reviver_func);
};
