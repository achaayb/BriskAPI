# BriskAPI

BriskAPI is a high-performance lightweight framework for building API's in python with minimal dependencies

features:
- elegant routing
- jsonschema validation
- high performance
- websocket support

example:
> app.py
```py
from briskapi.applications import BriskAPI
from briskapi.request import Request
from briskapi.response import JSONResponse
from briskapi.connection import WebSocketConnection
from briskapi.status import HTTP_202_ACCEPTED

app = BriskAPI()

# Http endpoint
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

# Websocket endpoint
@app.ws("/")
async def ping(connection: WebSocketConnection):
    await connection.accept()
    while True:
        message = await connection.receive_message()
        if message == "close":
            await connection.close()
            return
        await connection.send_message(str(message))
```

running the api:
```bash
uvicorn app:app
```