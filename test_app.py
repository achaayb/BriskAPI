from gapi.applications import GAPI
from gapi.requests import Request
from gapi.responses import JSONResponse
from gevent import sleep
app = GAPI()

@app.route("/{hello}", methods=["POST"], request_schema={
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}, response_schema={
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "foo": {"type": "string"}
    },
    "required": ["name", "age", "foo"],
})
def hello_world(request: Request):
    name = request.slugs["hello"]
    response =  JSONResponse(data=request.json)
    return response

@app.route("/goodbye")
def goodbye_world(request_data):
    return {"message": "Goodbye, World!"}


if __name__ == "__main__":
    app.run("0.0.0.0", 8000)
