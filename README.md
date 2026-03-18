# Experience Economy News Scraper

Automatically scrapes the top 10 sports/live events news sources weekly and feeds new events into the timeline on the Experience Economy Map.

## How It Works

```
Every Monday 8am UTC
        │
        ▼
  GitHub Actions runs scraper.py
        │
        ▼
  Pulls RSS from 10 sources
        │
        ▼
  Filters by relevance score (≥6/10)
        │
        ▼
  Appends new events to events.json
        │
        ▼
  inject_events.py merges historical
  + scraped into experience-economy-map.html
        │
        ▼
  Auto-commits back to main branch
        │
        ▼
  GitHub Pages redeploys automatically
        │
        ▼
  Live site updated ✅
```

## Sources

| # | Source | Type | Coverage |
|---|--------|------|----------|
| 1 | Front Office Sports | RSS | Sports business, deals |
| 2 | Sportico | RSS | Franchise valuations, PE |
| 3 | The Fourth Quarter | Substack RSS | Sports/entertainment VC |
| 4 | Pollstar News | RSS | Live music, venues |
| 5 | Billboard Business | RSS | Music industry |
| 6 | Business of Experience | Substack RSS | Experiential economy |
| 7 | Axios Sports | RSS | Fast-moving sports biz |
| 8 | SportsPro | RSS | Global rights, sponsorship |
| 9 | Sports Business Journal | RSS | Deals, venues, sponsorship |
| 10 | Variety Business | RSS | Entertainment industry |

## Relevance Scoring

Each article is scored 0–10 based on:
- **Company name match** (+3) — direct mention of any of the 134 mapped companies
- **High signal terms** (+1.5) — acquisitions, raises, deals, valuations, etc.
- **Keyword density** (+0–2) — sector-specific terminology
- **Source weight** (×1.0–1.3) — higher-signal sources boosted

**Threshold: 6/10** (medium filter)

Only events scoring **7+** are added to the visual timeline.

## Setup (One Time)

### 1. Clone this repo to your GitHub

The workflow runs automatically once the repo is public and GitHub Pages is enabled.

### 2. File structure

```
your-repo/
├── experience-economy-map.html    ← the main map (auto-updated)
├── scraper/
│   ├── scraper.py                 ← main scraper script
│   ├── inject_events.py           ← merges events into HTML
│   ├── events.json                ← scraped events database
│   └── requirements.txt           ← Python dependencies
└── .github/
    └── workflows/
        └── scraper.yml            ← GitHub Actions config
```

### 3. Verify it's running

Go to your repo → **Actions** tab → you'll see "Experience Economy Scraper" running every Monday.

To run manually: Actions → "Experience Economy Scraper" → "Run workflow"

## Adding Events Manually

Edit `scraper/events.json` and add an object:

```json
{
  "id": "manual_001",
  "date": "2026-03",
  "headline": "Your headline here",
  "company": "Company Name",
  "layer": 0,
  "access": "public",
  "source": "Manual",
  "url": "https://...",
  "score": 10
}
```

**Layer codes:**
- `0` = Content & IP
- `1` = Physical Infrastructure
- `2` = Operators & Distribution
- `3` = Service Providers
- `4` = Technology Enablers

**Access codes:** `public`, `pe`, `venture`, `ref`

## Keyword List

The scraper watches for 134 mapped companies + ~200 sector keywords including:

**Deal signals:** acquires, raises, funding, Series A/B/C, valuation, IPO, media rights, broadcast deal, merger, stake...

**Companies:** Live Nation, Ticketmaster, Sphere, WNBA, Topgolf, Sportradar, CAA, TKO Group, Arctos Partners, [all 134 mapped companies]...

**Sector terms:** sports franchise, venue, ticketing, experience economy, sports PE, women's sports, media rights inflation, streaming rights...
