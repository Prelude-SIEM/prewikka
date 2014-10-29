import cgi
from prewikka import Core, Request

defined_status = {
        200: 'OK',
        400: 'BAD REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT FOUND',
        405: 'METHOD NOT ALLOWED',
        500: 'INTERNAL SERVER ERROR',
}

class WSGIRequest(Request.Request):
    def init(self, environ, start_response):
        self._environ = environ
        self._start_response = start_response

        Request.Request.init(self)

        if self.getMethod() == 'POST':
            self.arguments = cgi.parse_qs(environ['wsgi.input'].read())
        else:
            self.arguments = cgi.parse_qs(self.getQueryString())

        for name, value in self.arguments.items():
            self.arguments[name] = (len(value) == 1) and value[0] or value

    def getMethod(self):
        return self._environ['REQUEST_METHOD']

    def write(self, data):
        self._write(data)

    def sendHeaders(self, code=200, status_text=None):
        if self.output_cookie:
            self.output_headers.extend(("Set-Cookie", c.OutputString()) for c in self.output_cookie.values())

        if not status_text:
            status_text = defined_status.get(code, "Unknown")

        self._write = self._start_response("%d %s" % (code, status_text), self.output_headers)

    def getRemoteUser(self):
        return self._environ.get('REMOTE_USER')

    def getQueryString(self):
        return self._environ.get('QUERY_STRING')

    def getCookieString(self):
        return self._environ.get('HTTP_COOKIE', '')

    def getReferer(self):
        return self._req.headers_in.get('HTTP_REFERER', '')

    def getClientAddr(self):
        return self._environ.get('REMOTE_ADDRESS')


def application(environ, start_response):
        req = WSGIRequest()
        req.init(environ, start_response)

        # Check whether the URL got a trailing "/", if not perform a redirect
        if not environ["PATH_INFO"]:
                start_response('301 Redirect', [('Location', environ['SCRIPT_NAME'] + "/"),])

        # If the user did not configure Apache to directly serve static files, do it ourselve
        elif req.getMethod() == "GET" and environ["PATH_INFO"].startswith("/prewikka/"):
                return req.processStatic(environ["PATH_INFO"], lambda fd: fd) or []

        else:
                Core.Core(environ.get("PREWIKKA_CONFIG", None)).process(req)

        return []