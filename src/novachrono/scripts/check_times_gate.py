import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main() -> None:
    url = "http://:9000/divoom_api"

    payload = {
        "Command": "Channel/GetAllConf",
        "LocalToken": "",
    }

    request = Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(f"Connecting to {url} ...")

    try:
        with urlopen(request, timeout=8) as response:
            body = response.read().decode("utf-8")
    except HTTPError as error:
        print(f"HTTP error: {error.code} {error.reason}")
        return
    except URLError as error:
        print(f"Connection failed: {error.reason}")
        return
    except TimeoutError:
        print("Connection timed out.")
        return

    print("Response:")
    print(body)


if __name__ == "__main__":
    main()
