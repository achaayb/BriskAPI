import json
import re
from pprint import pp
from urllib.parse import parse_qs, urlparse
import gevent

from gevent.pywsgi import WSGIServer
from gevent import sleep
from gevent.pool import Group

from gapi.requests import Request
from gapi.responses import JSONResponse
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

    def _match(self, environ):
        path_info = environ.get("PATH_INFO", "/")
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        request_method = environ.get("REQUEST_METHOD", "GET")
        for path, methods, handler in self._routes:
            # Skip if invalid method
            if not request_method in methods:
                continue
            m = path.match(path_info)
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

    def _http_handler(self, start_response, response: JSONResponse):
        start_response(response.status_to_str, response.headers)
        return [response.body]

    def __call__(self, environ, start_response):
        """__call__ magic method called by WSGIServer per request"""


        # Match to router and extract slugs
        match = self._match(environ)
        if match is None:
            response = JSONResponse(status=HTTP_404_NOT_FOUND, data={"message": "Resource not found"})
            return self._http_handler(start_response, response)

        path_params = match["path_params"]
        handler = match["handler"]

        # Parse request dependencies
        headers = self._parse_headers(environ)
        query_params = self._parse_qs(environ)
        body = self._parse_body(environ)

        # Prepare Request object
        path_info = environ.get("PATH_INFO", "/")
        request_method = environ.get("REQUEST_METHOD", "GET")
        
        request = Request()
        request.headers = headers
        request.method = request_method
        request.path = path_info
        request.slugs = path_params
        request.query = query_params
        request.body = body

        # Prepare Response
        handler_response = handler(request)

        if isinstance(handler_response, JSONResponse):
            return self._http_handler(start_response, handler_response)
        else:
            raise ValueError("Invalid response object")

    def run(self, host: str, port: int):
        pp("Starting GAPI instance")
        server = WSGIServer((host, port), self)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pp("KeyboardInterrupt received. Cleaning up...")
        finally:
            pp("Graceful shutdown...")
            pp("Goodbye! ૮₍ ˶ᵔ ᵕ ᵔ˶ ₎ა")