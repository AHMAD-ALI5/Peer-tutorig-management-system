"""HTTP helper used by the Tkinter window. Talks to Flask on port 5050."""
import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

BASE_URL = "http://127.0.0.1:5050"


class ApiError(Exception):
    """A readable error message for the window to show."""


def request(path, data=None, params=None):
    """GET when data is None, otherwise POST. Returns the decoded JSON dictionary."""
    url = BASE_URL + path
    if params:
        url += "?" + urlencode(params)
    body = urlencode(data).encode("utf-8") if data is not None else None
    try:
        with urlopen(url, data=body, timeout=5) as reply:
            return json.loads(reply.read().decode("utf-8"))
    except HTTPError as error:  # Flask answered with 400 / 401 / 404 and JSON
        try:
            message = json.loads(error.read().decode("utf-8")).get("error")
        except ValueError:
            message = None
        raise ApiError(message or f"Server error {error.code}.") from None
    except URLError:
        raise ApiError("Cannot connect to the server. Start Flask on port 5050, then try again.") from None
    except socket.timeout:
        raise ApiError("The server took too long to reply. Try again.") from None
