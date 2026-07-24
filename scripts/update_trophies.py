"""
Rewrites assets/trophies.svg with two achievement tiles (Stars, Public
Repos) for USERNAME, each with a tier label from simple local thresholds.
Replaces the old github-profile-trophy.vercel.app embed, whose shared
public demo instance can go down independently of this repo. These tiers
are an arbitrary local scale for flavor, not a claim about GitHub-wide
ranking. Meant to run daily via .github/workflows/update-github-cards.yml.

Run manually:  python scripts/update_trophies.py
"""

import sys

from github_api import list_public_repos, rest_get

USERNAME = "Argstrix"
SVG_PATH = "assets/trophies.svg"

STAR_TIERS = [(9, "Bronze"), (49, "Silver"), (99, "Gold")]
REPO_TIERS = [(9, "Bronze"), (24, "Silver"), (49, "Gold")]
TOP_TIER = "Platinum"


def tier_for(value, tiers):
    for ceiling, name in tiers:
        if value <= ceiling:
            return name
    return TOP_TIER


def fetch_achievements(username):
    repos = list_public_repos(username)
    stars = sum(r.get("stargazers_count", 0) for r in repos)
    profile = rest_get(f"/users/{username}")
    public_repos = profile.get("public_repos", len(repos))
    return {
        "stars": stars,
        "stars_tier": tier_for(stars, STAR_TIERS),
        "public_repos": public_repos,
        "public_repos_tier": tier_for(public_repos, REPO_TIERS),
    }


def render_tile(x, label, value, tier):
    return f"""  <g transform="translate({x},0)">
    <rect x="0" y="0" width="164" height="120" rx="12" fill="#12161c" stroke="#232a32"/>
    <text x="16" y="30" font-family="Consolas,Menlo,Monaco,'Courier New',monospace" font-size="13" fill="#8b96a3">{label}</text>
    <text x="16" y="66" font-family="Consolas,Menlo,Monaco,'Courier New',monospace" font-size="30" font-weight="700" fill="#e8eaed">{value}</text>
    <text x="16" y="94" font-family="Consolas,Menlo,Monaco,'Courier New',monospace" font-size="13" font-weight="700" fill="#f2a93b">{tier}</text>
  </g>"""


def render_svg(achievements):
    tiles = "\n".join(
        [
            render_tile(20, "Stars", achievements["stars"], achievements["stars_tier"]),
            render_tile(196, "Public Repos", achievements["public_repos"], achievements["public_repos_tier"]),
        ]
    )
    return f"""<svg width="380" height="140" viewBox="0 0 380 140" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000000" flood-opacity="0.4"/>
    </filter>
  </defs>
  <g filter="url(#soft)">
{tiles}
  </g>
</svg>
"""


def update_svg(svg_path, achievements):
    new_content = render_svg(achievements)
    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = None
    if old_content == new_content:
        return False
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return True


if __name__ == "__main__":
    try:
        achievements = fetch_achievements(USERNAME)
    except Exception as exc:
        print(f"Warning: failed to fetch achievements, no changes made: {exc}", file=sys.stderr)
        sys.exit(0)
    changed = update_svg(SVG_PATH, achievements)
    print(f"Computed achievements: {achievements}")
    print("SVG updated." if changed else "SVG left as-is.")
