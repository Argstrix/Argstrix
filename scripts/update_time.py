"""
Rewrites assets/local-time.svg with the current time in Asia/Kolkata (IST).
Meant to be run frequently by .github/workflows/update-time.yml so the badge
stays roughly "live" between commits.

Run manually:  python scripts/update_time.py
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

SVG_PATH = "assets/local-time.svg"
TZ = ZoneInfo("Asia/Kolkata")


def render_time_line(now: datetime) -> str:
    return now.strftime("%I:%M %p IST").lstrip("0")


def render_day_line(now: datetime) -> str:
    return now.strftime("%a, %d %b") + " &middot; Chennai, IN"


def update_svg(svg_path: str) -> bool:
    with open(svg_path, "r", encoding="utf-8") as f:
        content = f.read()

    now = datetime.now(TZ)
    time_str = render_time_line(now)
    day_str = render_day_line(now)

    content, n1 = re.subn(
        r"(<!--TIME_START-->.*?font-weight=\"700\" fill=\"#e8eaed\">)([^<]*)(</text><!--TIME_END-->)",
        lambda m: f"{m.group(1)}{time_str}{m.group(3)}",
        content,
    )
    content, n2 = re.subn(
        r"(<!--DAY_START-->.*?fill=\"#8b96a3\">)([^<]*)(</text><!--DAY_END-->)",
        lambda m: f"{m.group(1)}{day_str}{m.group(3)}",
        content,
    )

    if n1 == 0 or n2 == 0:
        print("Warning: time/day markers not found, no changes made.")
        return False

    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


if __name__ == "__main__":
    changed = update_svg(SVG_PATH)
    print("Local time badge updated." if changed else "No changes made.")
