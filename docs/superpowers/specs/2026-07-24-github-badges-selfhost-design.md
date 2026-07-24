# Self-hosted GitHub profile cards (stats / top-langs / trophies)

## Problem

Three README badges depend on shared public third-party demo services that are
currently down for everyone, not just this repo:

- `github-readme-stats.vercel.app/api` (stats card) → `503 DEPLOYMENT_PAUSED`
- `github-readme-stats.vercel.app/api/top-langs/` → `503 DEPLOYMENT_PAUSED`
- `github-profile-trophy.vercel.app` → `402 DEPLOYMENT_DISABLED`

These are shared demo instances hitting their own hosting quota — nothing in
this repo can fix that. The fix is to stop depending on them: fetch the same
underlying data directly from the GitHub API and render our own SVGs, the same
way `scripts/update_uptime.py` already does for the `Uptime` field.

Out of scope: `github-readme-streak-stats` badge (currently working, already
migrated to its maintained `streak-stats.demolab.com` domain in a prior change).

## Architecture

New files:

- `scripts/github_api.py` — shared helper used by all three scripts below:
  - authenticated REST GET (adds `Authorization: Bearer $GITHUB_TOKEN` header
    when the env var is set; works unauthenticated too, just at a lower rate
    limit)
  - authenticated GraphQL POST to `api.github.com/graphql`
  - repo-list pagination helper (`GET /users/{username}/repos`)
- `scripts/update_stats.py` → writes `assets/github-stats.svg`
- `scripts/update_top_langs.py` → writes `assets/top-langs.svg`
- `scripts/update_trophies.py` → writes `assets/trophies.svg`
- `.github/workflows/update-github-cards.yml` — one workflow, three steps (one
  per script), `cron: "0 4 * * *"` + `workflow_dispatch`, same
  checkout → setup-python → run → commit pattern as `update-uptime.yml`.
  Uses `secrets.GITHUB_TOKEN` (auto-provided by Actions, no extra setup).

Modified:

- `README.md` — swap the three external `<img>` embeds for local
  `![...](./assets/...)` references pointing at the new SVGs.

Each script is independently responsible for exactly one card: fetch its own
data, render its own SVG, fail on its own without affecting the other two.

## Visual design

All three cards reuse the visual language already established in
`assets/neofetch.svg`: `#0b0e11` background, amber (`#f2a93b`) → teal
(`#45d6b5`) gradient border, rounded corners, `feDropShadow`, monospace
(`Consolas,Menlo,Monaco,'Courier New',monospace`) font, `Label : value`
row formatting.

### `github-stats.svg` (~500×160)

Four rows, same `Label : value` style as the neofetch card:

- `Stars` — sum of `stargazers_count` across all public repos
- `Commits` — `totalCommitContributions` from `contributionsCollection`
  (last 365 days)
- `PRs` — `totalPullRequestContributions` from the same query
- `Issues` — `totalIssueContributions` from the same query

One GraphQL query covers Commits/PRs/Issues together; Stars comes from the
REST repo list (already fetched for top-langs, but this script fetches its
own copy to stay independent per the architecture above).

### `top-langs.svg` (~500×220)

Title row + top-5 horizontal bars, one per language:

- Data: `GET /repos/{owner}/{repo}/languages` summed (bytes) across all
  public, non-fork repos
- Bar width proportional to that language's share of total bytes across the
  top 5 (i.e. percentages re-normalized to the top 5, not to all languages)
- Bar color: GitHub's real per-language color (small hardcoded lookup table
  covering the languages that actually show up in this account — Python,
  TypeScript, JavaScript, C++, Solidity, etc. — with a neutral gray fallback
  for anything not in the table)
- Percentage label at the end of each bar

### `trophies.svg` (~500×160)

Two tiles, side by side:

- **Stars** — raw count + tier word: 0–9 Bronze, 10–49 Silver, 50–99 Gold,
  100+ Platinum
- **Public Repos** — raw count + tier word: 0–9 Bronze, 10–24 Silver, 25–49
  Gold, 50+ Platinum

These thresholds are our own arbitrary local scale for flavor — explicitly
not a claim about GitHub-wide percentile ranking (which is what the original
trophy service computed and we have no access to).

## Data flow

1. Workflow runs daily (or on manual dispatch), checks out the repo, sets up
   Python.
2. Step 1: `python scripts/update_stats.py` — GraphQL contributionsCollection
   + REST stars sum → writes `assets/github-stats.svg`.
3. Step 2: `python scripts/update_top_langs.py` — REST repo list → REST
   languages per repo → writes `assets/top-langs.svg`.
4. Step 3: `python scripts/update_trophies.py` — REST stars sum + REST public
   repo count → writes `assets/trophies.svg`.
5. Commit step: stage all three SVGs, commit if changed, push (same
   `git commit ... || echo "No changes to commit"` pattern as the existing
   workflows).

Each script writes its full output file directly (not a regex-substitution
into a static template) since bar counts/tile counts are dynamic. Unlike
`update_time.py`/`update_uptime.py`, there is no shared static SVG shell to
preserve — regenerating the whole file each run is correct here.

## Error handling

Each script wraps its API calls in a try/except. On any failure (network
error, non-2xx response, unexpected/missing JSON field), it prints a warning
to stderr and exits `0` without writing to its SVG file — mirroring the
existing "no changes made" behavior in `update_time.py`. This means:

- A GitHub API outage or rate-limit hit leaves the last-known-good SVG in
  place instead of blanking/corrupting it.
- One card's failure doesn't fail the workflow run or block the other two
  cards' steps (each script's own internal handling makes this true without
  needing `continue-on-error` in the workflow YAML).

## Testing

- Each script will be run for real against the live GitHub API for
  `Argstrix` during implementation.
- Resulting SVGs will be rendered via headless Chrome screenshot (same
  technique used earlier to verify `neofetch.svg`) to visually confirm
  layout, bar proportions, and text fit before considering the work done.
- The GraphQL-based Commits/PRs/Issues numbers require an authenticated
  token; CI gets this automatically via `secrets.GITHUB_TOKEN`. Local
  verification during implementation will exercise the REST-only paths
  (stars, top-langs, trophies) directly, and the GraphQL query shape will be
  verified by careful review against GitHub's documented schema since no
  local token is available in this environment.

## README changes

Replace:

```md
<img src="https://github-readme-stats.vercel.app/api?..." ... />
<img src="https://github-readme-streak-stats.herokuapp.com/?..." ... />
<img src="https://github-readme-stats.vercel.app/api/top-langs/?..." ... />
...
<img src="https://github-profile-trophy.vercel.app/?..." ... />
```

With local references to `./assets/github-stats.svg`, `./assets/top-langs.svg`,
`./assets/trophies.svg`, keeping the streak-stats external embed unchanged.
