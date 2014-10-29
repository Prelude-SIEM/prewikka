import prelude

def _normalizeName(name):
    return "".join([ i.capitalize() for i in name.split("_") ])


def getOperatorList(type):
    if type == prelude.IDMEFValue.TYPE_STRING:
        return ["<>*", "<>", "=", "~*", "~", "!" ]

    elif type == prelude.IDMEFValue.TYPE_DATA:
        return ["<>*", "<>", "~", "~*", "=", "<", ">", "!" ]

    else:
        return ["=", "<", ">", "<=", ">=" ]


def getHTML(rootcl, rootidx=0):
    out = "<ul>"
    for subcl in rootcl:
        if subcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
            out += '<li><a href="#">%s</a>' % subcl.getName()
        else:
            out += '<li class="idmef-leaf" id="%s"><a href="#">%s</a>' % (subcl.getPath(rootidx=rootidx), subcl.getName())

        if subcl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
            out += getHTML(subcl, rootidx)

        out += '</li>'

    return out + "</ul>"
