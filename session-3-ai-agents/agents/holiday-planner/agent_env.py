"""Load .env / .env.local from the holiday planner agent folder and each parent directory."""

from __future__ import annotations

from pathlib import Path


def load_agent_environment() -> None:
    """Walk from this package directory up the tree and load env files.

    Later (deeper / closer-to-agent) files override earlier ones so a local
    holiday-planner/.env.local wins over ../../.env.local at the monorepo root.
    """
    from dotenv import load_dotenv

    agent_dir = Path(__file__).resolve().parent
    chain: list[Path] = []
    d = agent_dir
    while d != d.parent:
        chain.append(d)
        d = d.parent

    for directory in reversed(chain):
        for name in (".env", ".env.local"):
            path = directory / name
            if path.is_file():
                load_dotenv(path, override=True)
