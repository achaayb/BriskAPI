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
    slugs: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode()

    @property
    def json(self) -> object:
        return json.loads(self.body)
    
    @property
    def dict(self) -> object:
        return {
            "path": self.path,
            "method": self.method,
            "headers": self.headers,
            "query": self.query,
            "slugs": self.slugs,
            "body": self.text
        }