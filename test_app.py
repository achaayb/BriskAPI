from briskapi.applications import BriskAPI
from briskapi.request import Request
from briskapi.response import JSONResponse
from briskapi.connection import WebSocketConnection
from briskapi.status import HTTP_202_ACCEPTED
app = BriskAPI()


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