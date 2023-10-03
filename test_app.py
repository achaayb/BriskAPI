from hyperapi.applications import HyperAPI
from hyperapi.request import Request
from hyperapi.response import JSONResponse
from hyperapi.connection import WebSocketConnection
from hyperapi.status import HTTP_202_ACCEPTED
app = HyperAPI()


@app.route(
    "/{hello}",
    methods=["POST"],
    request_schema={
        "type": "object",
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name", "age"],
    }
)
def hello_world(request: Request):
    hello = request.slugs["hello"]
    response = JSONResponse(data={"name": request.headers["foo"]}, status=HTTP_202_ACCEPTED)
    response.set_header("Hello", "World")
    return response

@app.ws("/")
async def foo(connection: WebSocketConnection):
    await connection.accept()
    while True:
        message = await connection.receive_message()
        if message == "close":
            await connection.close()
            return
        await connection.send_message(str(message))