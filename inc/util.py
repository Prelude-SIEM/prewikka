
#
# Copyright 2004 Miika Keskinen, Markus Alkio, Citadec Solutions OY
# Licensed under GPL
# 


def webify(data):
    data = data.replace("&", "&amp;")
    data = data.replace("\"", "&quot;")
    data = data.replace("'", "&rsquo;")
    data = data.replace("<", "&lt;") 
    data = data.replace(">", "&gt;") 
    data = data.replace("\n", "<br>") 
    return data

