"""
Shared GitHub REST/GraphQL helpers for the profile-card generator scripts
(update_stats.py, update_top_langs.py, update_trophies.py).

Uses GITHUB_TOKEN from the environment when present (always auto-provided
in GitHub Actions runs); falls back to unauthenticated requests otherwise.
Unauthenticated REST calls work fine at a lower rate limit, but GraphQL
calls require a token.
"""

import json
import os
import urllib.parse
import urllib.request

API_ROOT = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"


def _headers(extra=None):
    headers = {
        "User-Agent": "profile-readme-card-generator",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers


def rest_get(path, params=None):
    url = f"{API_ROOT}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def rest_get_all_pages(path, params=None, per_page=100):
    results = []
    page = 1
    params = dict(params or {})
    params["per_page"] = per_page
    while True:
        params["page"] = page
        batch = rest_get(path, params)
        if not batch:
            break
        results.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return results


def graphql(query, variables=None):
    if not os.environ.get("GITHUB_TOKEN"):
        raise RuntimeError("GITHUB_TOKEN is required for GraphQL API calls")
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers=_headers({"Content-Type": "application/json"}),
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode())
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


def list_public_repos(username, include_forks=False):
    repos = rest_get_all_pages(f"/users/{username}/repos", {"type": "owner"})
    if include_forks:
        return repos
    return [r for r in repos if not r.get("fork")]
