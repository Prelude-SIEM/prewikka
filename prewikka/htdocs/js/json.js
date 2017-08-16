"use strict";

function JSONRegistry() {
    this.prototypes = {};

    this.register = function(proto) {
        this.prototypes[proto.name] = proto;
    };
}

window.json_registry = new JSONRegistry();


function _reviver_func(name, value) {
    if ( value !== null && typeof value === "object" && value["__prewikka_class__"] ) {
        var type = value["__prewikka_class__"][0];
        var kwargs = value["__prewikka_class__"][1];
        var proto = window.json_registry.prototypes[type];

        if ( ! proto )
            throw new TypeError("Class " + type + " not found.");

        return new proto(kwargs);
    }

    return value;
}

var _orig_func = JSON.parse;
JSON.parse = function(input) {
    return _orig_func(input, _reviver_func);
};
