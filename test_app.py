from gapi.applications import GAPI
from gapi.requests import Request
from gapi.responses import JSONResponse
from gevent import sleep
app = GAPI()

@app.route("/{hello}", methods=["GET"])
def hello_world(request: Request):
    name = request.slugs["hello"]
    response =  JSONResponse(data=["foo"])
    sleep(3)
    return response

@app.route("/goodbye")
def goodbye_world(request_data):
    return {"message": "Goodbye, World!"}


if __name__ == "__main__":
    app.run("0.0.0.0", 8000)
