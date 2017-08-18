"use strict";

function JSONRegistry() {
    var ret = {};

    ret._prototypes = {};

    ret["register"] = function(proto) {
        ret._prototypes[proto.name] = proto;
    }

    return ret;
}

window.json_registry = JSONRegistry();


function _reviver_func(name, value) {
    if ( value !== null && typeof value === "object" && value["__prewikka_class__"] ) {
        var type = value["__prewikka_class__"][0];
        var kwargs = value["__prewikka_class__"][1];
        var proto = window.json_registry._prototypes[type];

        if ( ! proto )
            throw new TypeError("Class " + type + " not found.");

        return proto(kwargs);
    }

    return value;
}

var _orig_func = JSON.parse;
JSON.parse = function(input) {
    return _orig_func(input, _reviver_func);
};
