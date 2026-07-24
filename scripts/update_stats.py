"""
Rewrites assets/github-stats.svg with live GitHub stats (stars, commits,
PRs, issues) for USERNAME. Replaces the old github-readme-stats.vercel.app
embed, whose shared public demo instance can go down independently of this
repo. Meant to run daily via .github/workflows/update-github-cards.yml.

Run manually (needs GITHUB_TOKEN in the environment for the GraphQL call):
    GITHUB_TOKEN=... python scripts/update_stats.py
"""

import sys

from github_api import graphql, list_public_repos

USERNAME = "Argstrix"
SVG_PATH = "assets/github-stats.svg"

CONTRIBUTIONS_QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
    }
  }
}
"""


def fetch_stats(username):
    stars = sum(r.get("stargazers_count", 0) for r in list_public_repos(username))
    data = graphql(CONTRIBUTIONS_QUERY, {"login": username})
    contrib = data["user"]["contributionsCollection"]
    return {
        "stars": stars,
        "commits": contrib["totalCommitContributions"],
        "prs": contrib["totalPullRequestContributions"],
        "issues": contrib["totalIssueContributions"],
    }


def render_svg(stats):
    rows = [
        ("Stars", str(stats["stars"])),
        ("Commits", f"{stats['commits']} (this yr)"),
        ("PRs", str(stats["prs"])),
        ("Issues", str(stats["issues"])),
    ]
    row_y_start = 78
    row_gap = 32
    row_lines = "\n".join(
        f'    <text x="30" y="{row_y_start + i * row_gap}">'
        f'<tspan fill="#f2a93b">{label}</tspan>'
        f'<tspan fill="#5b6670"> :</tspan> {value}</text>'
        for i, (label, value) in enumerate(rows)
    )
    height = row_y_start + (len(rows) - 1) * row_gap + 30

    return f"""<svg width="360" height="{height}" viewBox="0 0 360 {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="border" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f2a93b"/>
      <stop offset="100%" stop-color="#45d6b5"/>
    </linearGradient>
    <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000000" flood-opacity="0.45"/>
    </filter>
  </defs>
  <g filter="url(#soft)">
    <rect x="4" y="4" width="352" height="{height - 8}" rx="14" fill="url(#border)" opacity="0.55"/>
    <rect x="6" y="6" width="348" height="{height - 12}" rx="12" fill="#0b0e11"/>
    <rect x="6.5" y="6.5" width="347" height="{height - 13}" rx="11.5" fill="none" stroke="#232a32" stroke-width="1"/>
  </g>
  <text x="30" y="34" font-family="Consolas,Menlo,Monaco,'Courier New',monospace" font-size="14" font-weight="700" fill="#45d6b5">madhan@Argstrix ~ github stats</text>
  <line x1="30" y1="42" x2="330" y2="42" stroke="#45d6b5" stroke-width="1.5"/>
  <g font-family="Consolas,Menlo,Monaco,'Courier New',monospace" font-size="14" fill="#e8eaed">
{row_lines}
  </g>
</svg>
"""


def update_svg(svg_path, stats):
    new_content = render_svg(stats)
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
        stats = fetch_stats(USERNAME)
    except Exception as exc:
        print(f"Warning: failed to fetch stats, no changes made: {exc}", file=sys.stderr)
        sys.exit(0)
    changed = update_svg(SVG_PATH, stats)
    print(f"Computed stats: {stats}")
    print("SVG updated." if changed else "SVG left as-is.")
