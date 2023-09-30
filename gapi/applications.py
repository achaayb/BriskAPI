import json
import re
from pprint import pp
from urllib.parse import parse_qs, urlparse

from gevent.pywsgi import WSGIServer

from gapi.classes import Request, Response
from gapi.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class GAPI:
    def __init__(self: "GAPI", debug: bool = True):
        self.debug = debug
        self._routes = []

    def route(self, path, methods=["GET"]):
        """Decorator for adding routes to the router."""

        if path.endswith("/"):
            path = path[:-1]

        def decorator(handler):
            self._add_route(path, methods, handler)
            return handler

        return decorator

    def _add_route(self, path, methods, handler):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._routes.append((re.compile(path_re), methods, handler))
        return handler

    def _match(self, request_path, method):
        for path, methods, handler in self._routes:
            # Skip if invalid method
            if not method in methods:
                continue
            m = path.match(request_path)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {
                    "path_params": path_params,
                    "method": methods,
                    "handler": handler,
                }

    def _parse_qs(self, environ):
        query_string = environ.get("QUERY_STRING", None)
        if not query_string:
            return {}
        parsed = parse_qs(query_string)
        pp(parsed)
        return {
            key: value[0] if len(value) == 1 else value for key, value in parsed.items()
        }

    def _parse_headers(self, environ):
        headers = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = value
        return headers

    def _parse_body(self, environ):
        try:
            content_length = int(environ.get("CONTENT_LENGTH", "0"))
            request_body = environ["wsgi.input"].read(content_length)
        except ValueError:
            request_body = b""
        return request_body

    def _http_handler(self, start_response, response: Response):
        start_response(response.status_to_str, response.headers)
        return [response.body]

    def __call__(self, environ, start_response):
        """__call__ magic method called by WSGIServer per request"""

        # TODO: User defined response headers
        # TODO: url params
        # TODO: string params
        # TODO: header params

        path_info = environ.get("PATH_INFO", "/")
        request_method = environ.get("REQUEST_METHOD", "GET")

        if path_info.endswith("/"):
            path_info = path_info[:-1]

        match = self._match(path_info, request_method)
        if match is None:
            response = Response(status=HTTP_404_NOT_FOUND, data="Resource not found")
            return self._http_handler(start_response, response)

        handler = match["handler"]

        # Prepare Request object
        headers = self._parse_headers(environ)
        query_params = self._parse_qs(environ)
        body = self._parse_body(environ)

        request = Request()
        request.headers = headers
        request.method = request_method
        request.path = path_info
        request.query = query_params
        request.body = body

        # Prepare Response
        handler_response = handler(request)

        if isinstance(handler_response, Response):
            return self._http_handler(start_response, handler_response)

        error_response = Response(
            status=HTTP_500_INTERNAL_SERVER_ERROR, data="Internal server error"
        )
        return self._http_handler(start_response, error_response)

    def run(self, host: str, port: int):
        pp("Starting GAPI instance")
        server = WSGIServer((host, port), self)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pp("KeyboardInterrupt received. Cleaning up...")
        finally:
            pp("Graceful shutdown...")
            server.stop()
            pp("Goodbye! ૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა")
