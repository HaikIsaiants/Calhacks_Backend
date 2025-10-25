#!/usr/bin/env python
"""
Quick dev runner: loads .env and starts Uvicorn with reload.

Usage: python run.py

Respects env vars:
- PORT (default 8000)
- HOST (default 0.0.0.0)
"""

import os
from dotenv import load_dotenv
import uvicorn


def main() -> None:
    # Load .env into process env
    load_dotenv(override=False)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Start the ASGI app defined as `app` in app.py
    uvicorn.run("app:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()

