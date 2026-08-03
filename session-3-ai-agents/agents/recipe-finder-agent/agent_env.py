"""Load .env / .env.local from this agent folder and parent directories."""

from __future__ import annotations

from pathlib import Path


def load_agent_environment() -> None:
    """Walk up directory tree and load env files with local override priority."""
    from dotenv import load_dotenv

    agent_dir = Path(__file__).resolve().parent
    chain = []
    directory = agent_dir
    while directory != directory.parent:
        chain.append(directory)
        directory = directory.parent

    for current in reversed(chain):
        for name in (".env", ".env.local"):
            path = current / name
            if path.is_file():
                load_dotenv(path, override=True)
