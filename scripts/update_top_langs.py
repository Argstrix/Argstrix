"""
Rewrites assets/top-langs.svg with the top-5 languages (by bytes) across all
public, non-fork repos owned by USERNAME. Replaces the old
github-readme-stats.vercel.app/api/top-langs/ embed, whose shared public
demo instance can go down independently of this repo. Meant to run daily
via .github/workflows/update-github-cards.yml.

Run manually:  python scripts/update_top_langs.py
(GITHUB_TOKEN is optional here - it raises the REST rate limit but this
script works fine unauthenticated too, unlike update_stats.py.)
"""

import sys
from collections import Counter

from github_api import list_public_repos, rest_get

USERNAME = "Argstrix"
SVG_PATH = "assets/top-langs.svg"
TOP_N = 5

LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "TypeScript": "#3178c6",
    "JavaScript": "#f1e05a",
    "C++": "#f34b7d",
    "Java": "#b07219",
    "Solidity": "#AA6746",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B",
    "Go": "#00ADD8",
    "Rust": "#dea584",
}
DEFAULT_COLOR = "#8b96a3"


def fetch_top_languages(username, top_n=TOP_N):
    totals = Counter()
    for repo in list_public_repos(username):
        langs = rest_get(f"/repos/{username}/{repo['name']}/languages")
        for lang, byte_count in langs.items():
            totals[lang] += byte_count
    ranked = totals.most_common(top_n)
    total_top = sum(count for _, count in ranked) or 1
    return [(lang, count / total_top) for lang, count in ranked]


def render_svg(languages):
    bar_y_start = 74
    bar_gap = 30
    bar_max_width = 260
    rows = []
    for i, (lang, share) in enumerate(languages):
        y = bar_y_start + i * bar_gap
        width = max(6, round(bar_max_width * share))
        color = LANGUAGE_COLORS.get(lang, DEFAULT_COLOR)
        pct = f"{share * 100:.1f}%"
        rows.append(
            f'    <text x="30" y="{y}" font-size="12.5" fill="#e8eaed">{lang}</text>\n'
            f'    <rect x="30" y="{y + 8}" width="{bar_max_width}" height="8" rx="4" fill="#232a32"/>\n'
            f'    <rect x="30" y="{y + 8}" width="{width}" height="8" rx="4" fill="{color}"/>\n'
            f'    <text x="{30 + bar_max_width + 10}" y="{y + 15}" font-size="11.5" fill="#8b96a3">{pct}</text>'
        )
    height = bar_y_start + (len(languages) - 1) * bar_gap + 44
    rows_svg = "\n".join(rows)

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
  <text x="30" y="34" font-family="Consolas,Menlo,Monaco,'Courier New',monospace" font-size="14" font-weight="700" fill="#45d6b5">madhan@Argstrix ~ top languages</text>
  <line x1="30" y1="42" x2="330" y2="42" stroke="#45d6b5" stroke-width="1.5"/>
  <g font-family="Consolas,Menlo,Monaco,'Courier New',monospace">
{rows_svg}
  </g>
</svg>
"""


def update_svg(svg_path, languages):
    new_content = render_svg(languages)
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
        languages = fetch_top_languages(USERNAME)
    except Exception as exc:
        print(f"Warning: failed to fetch top languages, no changes made: {exc}", file=sys.stderr)
        sys.exit(0)
    changed = update_svg(SVG_PATH, languages)
    print(f"Computed top languages: {languages}")
    print("SVG updated." if changed else "SVG left as-is.")
