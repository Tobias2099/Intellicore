from __future__ import annotations

import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def database_url_with_ssl(database_url: str | None = None) -> str:
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL must be set to the Supabase Postgres connection string.")

    parsed = urlparse(url)
    scheme = parsed.scheme
    if scheme == "postgresql":
        scheme = "postgresql+psycopg"

    query = dict(parse_qsl(parsed.query))
    query.setdefault("sslmode", "require")
    return urlunparse(parsed._replace(scheme=scheme, query=urlencode(query)))
