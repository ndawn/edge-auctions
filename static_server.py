import os
from pathlib import Path

from flask import Flask
from flask import Response


app = Flask(__name__)


@app.get("/<path:path>")
def get_image(path: str) -> Response:
    path = Path(os.curdir).absolute() / path

    if not path.exists():
        return Response("Not found", status=404)

    return Response(path.read_bytes(), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, ssl_context="adhoc")
