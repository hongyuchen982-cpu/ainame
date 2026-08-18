"""Serve the built frontend briefly and verify its root page over HTTP."""

import functools
import http.server
import threading
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "frontend" / "dist"


def main() -> None:
    if not (DIST / "index.html").is_file():
        raise RuntimeError("frontend/dist is missing; run npm run build first")
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(DIST),
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
            body = response.read().decode("utf-8")
            if response.status != 200 or 'id="root"' not in body:
                raise RuntimeError("built index did not contain the React root")
            if 'type="module"' not in body or '/assets/' not in body:
                raise RuntimeError("built index did not reference production assets")
            print(
                {
                    "http": response.status,
                    "root": True,
                    "bytes": len(body.encode("utf-8")),
                }
            )
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
