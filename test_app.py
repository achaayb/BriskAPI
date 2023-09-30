from gapi.applications import GAPI
from gapi.classes import Request, Response

app = GAPI()


@app.route("/{hello}/{haha}")
def hello_world(request: Request):
    bodi = request.json
    return Response(data=bodi)


@app.route("/goodbye")
def goodbye_world(request_data):
    return {"message": "Goodbye, World!"}


if __name__ == "__main__":
    app.run("0.0.0.0", 8000)
