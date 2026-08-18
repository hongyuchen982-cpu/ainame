"""Start Uvicorn with an event loop compatible with async Psycopg on Windows."""

import argparse
import asyncio
import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI Name FastAPI service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        loop=asyncio.SelectorEventLoop,
    )


if __name__ == "__main__":
    main()
