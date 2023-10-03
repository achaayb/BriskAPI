from hyperapi.applications import HyperAPI
from hyperapi.requests import Request
from hyperapi.responses import JSONResponse
from hyperapi.status import HTTP_202_ACCEPTED

app = HyperAPI()


@app.route(
    "/{hello}",
    methods=["POST"],
    request_schema={
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    },
    response_schema={
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    },
)
def hello_world(request: Request):
    hello = request.slugs["hello"]
    response = JSONResponse(data={"name": "Ali", "age": 3}, status=HTTP_202_ACCEPTED)
    response.set_header("Hello", "World")
    return response
