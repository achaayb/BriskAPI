import re
from pprint import pp
from urllib.parse import parse_qs

from hyperapi.requests import Request
from hyperapi.responses import JSONResponse
from hyperapi.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from jsonschema import Draft7Validator


class HyperAPI:
    def __init__(self: "HyperAPI", debug: bool = True):
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
            self._add_route(
                path,
                methods,
                handler,
                compiled_request_schema,
                compiled_response_schema,
            )
            return handler

        return decorator

    def _add_route(
        self, path, methods, handler, compiled_request_schema, compiled_response_schema
    ):
        param_re = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"
        path_re = r"^" + re.sub(param_re, r"(?P<\1>\\w+)", path) + r"$"
        self._routes.append(
            (
                re.compile(path_re),
                methods,
                handler,
                compiled_request_schema,
                compiled_response_schema,
            )
        )
        return handler

    def _match(self, scope):
        path_info = scope["path"]
        # Remove trailing slash
        if path_info.endswith("/"):
            path_info = path_info[:-1]

        request_method = scope["method"]
        for (
            path,
            methods,
            handler,
            compiled_request_schema,
            compiled_response_schema,
        ) in self._routes:
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
                    "compiled_response_schema": compiled_response_schema,
                }

    def _parse_qs(self, scope):
        query_string = scope["query_string"]
        if not query_string:
            return {}
        parsed = parse_qs(query_string)
        return {
            key: value[0] if len(value) == 1 else value for key, value in parsed.items()
        }

    def _parse_headers(self, scope):
        headers = dict()
        for header in scope["headers"]:
            headers[header[0].decode("utf-8")] = header[1].decode("utf-8")
        return headers

    def _parse_body(self, environ):
        try:
            content_length = int(environ.get("CONTENT_LENGTH", "0"))
            request_body = environ["wsgi.input"].read(content_length)
        except ValueError:
            request_body = b""
        return request_body

    async def _read_body(self, receive):
        body = bytearray()
        while True:
            msg = await receive()
            body += msg["body"]
            if not msg.get("more_body"):
                break
        return bytes(body)

    def _validate_http_request(self, request: Request, compiled_request_schema):
        request_validation_errors = []
        # Validate request is a json
        try:
            request.json
        except ValueError:
            return ["Invalid request body"]
        # Validate request json
        if compiled_request_schema:
            for error in compiled_request_schema.iter_errors(request.json):
                request_validation_errors.append(error.message)
        return request_validation_errors

    def _validate_http_response(self, response: JSONResponse, compiled_response_schema):
        response_validation_errors = []
        # Validate request json
        if compiled_response_schema:
            for error in compiled_response_schema.iter_errors(response.data):
                response_validation_errors.append(error.message)
        return response_validation_errors

    async def _http_response(self, response, send):
        await send(
            {
                "type": "http.response.start",
                "status": response.status,
                "headers": [(k.encode(), v.encode()) for k, v in response.headers],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": response.body,
            }
        )

    async def _http_handler(self, scope, receive, send):
        # Match to router and extract slugs
        match = self._match(scope)
        if match is None:
            response = JSONResponse(
                status=HTTP_404_NOT_FOUND, data={"message": "Resource not found"}
            )
            await self._http_response(response, send)
            return

        path_params = match["path_params"]
        handler = match["handler"]

        # Exctract schemas
        compiled_request_schema = match["compiled_request_schema"]
        compiled_response_schema = match["compiled_response_schema"]

        # Parse request dependencies
        headers = self._parse_headers(scope)
        query_params = self._parse_qs(scope)
        body = await self._read_body(receive)

        # Prepare Request object
        path_info = scope["path"]
        request_method = scope["method"]

        request = Request()
        request.headers = headers
        request.method = request_method
        request.path = path_info
        request.slugs = path_params
        request.query = query_params
        request.body = body

        # Validate request
        request_validation_errors = self._validate_http_request(
            request, compiled_request_schema
        )

        if request_validation_errors:
            response = JSONResponse(
                status=HTTP_422_UNPROCESSABLE_ENTITY,
                data={
                    "message": "validation error",
                    "details": request_validation_errors,
                },
            )
            await self._http_response(response, send)
            return

        # Prepare Response
        handler_response = handler(request)

        # Check JSONResponse is returned
        if not isinstance(handler_response, JSONResponse):
            raise ValueError("Invalid response object")

        # Validate response
        response_validation_errors = self._validate_http_response(
            handler_response, compiled_response_schema
        )
        if response_validation_errors:
            raise ValueError("Response validation failed {response_validation_errors}")

        # Flow success
        await self._http_response(handler_response, send)

    async def __call__(self, scope, receive, send):
        """__call__ magic method called by WSGIServer per request"""

        if scope["type"] == "http":
            await self._http_handler(scope, receive, send)
        elif scope["type"] == "lifespan":
            await self.lifespan_handler(scope, receive, send)
