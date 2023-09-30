import json
from typing import Any, List, Tuple, Union

from gapi.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class Request:
    path: str
    method: str
    headers: dict[str, str]
    query: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode()

    @property
    def json(self) -> object:
        return json.loads(self.body)


class Response:
    def __init__(
        self,
        data: Union[bytes, str, list, dict, None] = None,
        status: str = HTTP_200_OK,
        headers: dict[str, str] = [],
    ):
        self.data = data
        self.status = status
        self.headers = headers

    @property
    def body(self) -> bytes:
        if self.data is None:
            return b""
        elif isinstance(self.data, bytes):
            return self.data
        elif isinstance(self.data, str):
            return self.data.encode()
        elif isinstance(self.data, (dict, list)):
            return json.dumps(self.data).encode()
        else:
            raise TypeError(type(self.data))

    @property
    def status_to_str(self) -> str:
        return str(self.status)
