from layout import layoutManager


class Interface:
    def __init__(self, core, config, data):
        self._core = core
        self._config = config
        self._data = data
        self.headers = { "Content-type": "text/html" }

    def init(self):
        pass

    def build(self):
        pass

    def __str__(self):
        content = ""
        for key, value in self.headers.items():
            content += "%s: %s\r\n" % (key, value)
        return content + "\r\n"



class NormalInterface(Interface):
    def init(self):
        self._views = { }
        self._views["views"] = { }
        self._views["layout"] = "normal"
        self._views["views"]["modules"] = self._core.getContentModuleNames()
        self._views["views"]["software"] = self._config["software"]
        self._views["views"]["place"] = self._config["company"]
        self._views["views"]["title"] = self._config["title"]

    def setMenuName(self, name):
        self._views["views"]["module"] = name

    def setTabs(self, tabs):
        self._views["views"]["pages"] = tabs

    def setActiveTab(self, tab):
        self._views["views"]["active"] = tab

    def setMainContent(self, content):
        self._views["views"]["main"] = content

    def __str__(self):
        content = Interface.__str__(self)
        layout = layoutManager.getLayout(self._views["layout"], self._views["views"])
        return content + str(layout)
