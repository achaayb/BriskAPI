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
    HTTP_422_UNPROCESSABLE_ENTITY
)

from jsonschema import Draft7Validator


class GAPI:
    def __init__(self: "GAPI", debug: bool = True):
        self.debug = debug
        self._routes = []

    def route(self, path, methods=["GET"], request_schema=None, response_schema=None):
        """Decorator for adding routes to the router."""

        compiled_request_schema = None
        compiled_response_schema = None

        if path.endswith("/"):
            path = path[:-1]

        if request_schema:
            compiled_request_schema = Draft7Validator(request_schema)
        
        if response_schema:
            compiled_response_schema = Draft7Validator(response_schema)

        def decorator(handler):
            self._add_route(path, methods, handler, compiled_request_schema, compiled_response_schema)
            return handler

        return decorator

    def _add_route(self, path, methods, handler, compiled_request_schema, compiled_response_schema):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._routes.append((re.compile(path_re), methods, handler, compiled_request_schema, compiled_response_schema))
        return handler

    def _match(self, environ):
        path_info = environ.get("PATH_INFO", "/")
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        request_method = environ.get("REQUEST_METHOD", "GET")
        for path, methods, handler, compiled_request_schema, compiled_response_schema in self._routes:
            # Skip if invalid method
            if not request_method in methods:
                continue
            m = path.match(path_info)
            if m is not None:
                # Extract and return parameter values
                path_params = m.groupdict()
                return {
                    "path_params": path_params,
                    "handler": handler,
                    "compiled_request_schema": compiled_request_schema,
                    "compiled_response_schema": compiled_response_schema
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
    
    def _validate_request(self, request: Request, compiled_request_schema):
        request_validation_errors = []
        # Validate request is a json
        try:
            request_json = request.json
        except ValueError:
            return ["Invalid request body"]
        # Validate request json
        if compiled_request_schema:
            for error in compiled_request_schema.iter_errors(request.json):
                request_validation_errors.append(error.message)
        return request_validation_errors

    def _validate_response(self, response: JSONResponse, compiled_response_schema):
        response_validation_errors = []
        # Validate request json
        if compiled_response_schema:
            for error in compiled_response_schema.iter_errors(response.data):
                response_validation_errors.append(error.message)
        return response_validation_errors

    def __call__(self, environ, start_response):
        """__call__ magic method called by WSGIServer per request"""


        # Match to router and extract slugs
        match = self._match(environ)
        if match is None:
            response = JSONResponse(status=HTTP_404_NOT_FOUND, data={"message": "Resource not found"})
            return self._http_handler(start_response, response)

        path_params = match["path_params"]
        handler = match["handler"]
        
        # Exctract schemas
        compiled_request_schema = match["compiled_request_schema"]
        compiled_response_schema = match["compiled_response_schema"]

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


        # Validate request
        request_validation_errors = self._validate_request(request, compiled_request_schema)
        
        if request_validation_errors:
            response = JSONResponse(status=HTTP_422_UNPROCESSABLE_ENTITY, data={"message": "validation error", "details": request_validation_errors})
            return self._http_handler(start_response, response)

        # Prepare Response
        handler_response = handler(request)

        # Check JSONResponse is returned
        if not isinstance(handler_response, JSONResponse):
            raise ValueError("Invalid response object")

        # Validate response
        response_validation_errors = self._validate_response(handler_response, compiled_response_schema)
        if response_validation_errors:
            raise ValueError("Response validation failed {response_validation_errors}")

        return self._http_handler(start_response, handler_response)

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