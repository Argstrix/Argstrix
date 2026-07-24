"""
Fetches the account creation date for GITHUB_USERNAME from the public GitHub API,
computes how long the account has existed, and rewrites the <!--UPTIME_START--> ...
<!--UPTIME_END--> block inside assets/neofetch.svg with the new value.

Run manually:  python scripts/update_uptime.py
Run in CI:     see .github/workflows/update-uptime.yml
"""

import re
import sys
import urllib.request
import json
from datetime import datetime, timezone

USERNAME = "Argstrix"
SVG_PATH = "assets/neofetch.svg"


def fetch_created_at(username: str) -> datetime:
    url = f"https://api.github.com/users/{username}"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-readme-uptime-script"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    return datetime.strptime(data["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def format_uptime(created_at: datetime) -> str:
    now = datetime.now(timezone.utc)
    days = (now - created_at).days
    years = days // 365
    remaining_days = days % 365
    if years >= 1:
        return f"~{years} yr{'s' if years != 1 else ''} on GitHub"
    return f"{remaining_days} days on GitHub"


def update_svg(svg_path: str, new_uptime: str) -> bool:
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"(<!--UPTIME_START-->.*?Uptime</tspan><tspan fill=\"#5b6670\"> :</tspan> )([^<]*)(</text><!--UPTIME_END-->)")
    new_content, count = pattern.subn(lambda m: f"{m.group(1)}{new_uptime}{m.group(3)}", content)

    if count == 0:
        print("Warning: uptime marker not found, no changes made.", file=sys.stderr)
        return False

    if new_content == content:
        print("Uptime unchanged, nothing to commit.")
        return False

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


if __name__ == "__main__":
    created_at = fetch_created_at(USERNAME)
    uptime_str = format_uptime(created_at)
    changed = update_svg(SVG_PATH, uptime_str)
    print(f"Computed uptime: {uptime_str}")
    print("SVG updated." if changed else "SVG left as-is.")
