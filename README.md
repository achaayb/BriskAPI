# HyperAPI
HyperAPI - The Hyper lightweight API Framework.

```
  _  _                    _   ___ ___ 
 | || |_  _ _ __ ___ _ _ /_\ | _ |_ _|
 | __ | || | '_ / -_| '_/ _ \|  _/| | 
 |_||_|\_, | .__\___|_|/_/ \_|_| |___|
       |__/|_|                        
```

HyperAPI is a high-performance lightweight framework for building API's in python with minimal dependencies

features:
- elegant routing
- jsonschema validation
- high performance
- websocket support

example:
> app.py
```py
from hyperapi.applications import HyperAPI
from hyperapi.request import Request
from hyperapi.response import JSONResponse
from hyperapi.connection import WebSocketConnection
from hyperapi.status import HTTP_202_ACCEPTED

app = HyperAPI()

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