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
- builtin jsonschema validation
- high performance
- minimal codebase

example:
> app.py
```py
from hyperapi import HyperAPI
from hyperapi.requests import Request
from hyperapi.responses import JSONResponse
from hyperapi.status import HTTP_202_ACCEPTED

app = HyperAPI()

@app.route("/{hello}",
    methods=["POST"],
    request_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"],
        }, 
    response_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name", "age"],
        }
    )
def hello_world(request: Request):
    hello = request.slugs["hello"]
    response =  JSONResponse(data={"message": "Hello World"}, status=HTTP_202_ACCEPTED)
    response.set_header("Hello", "World")
    return response
```

running the api:
```bash
uvicorn app:app
```