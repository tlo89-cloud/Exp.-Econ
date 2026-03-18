#!/usr/bin/env python3
"""
Experience Economy News Scraper
Pulls from RSS feeds + web, filters by relevance, appends to events.json
Run manually or via GitHub Actions (every Monday 8am UTC)
"""

import json
import hashlib
import re
import os
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

# ─── CONFIG ────────────────────────────────────────────────────────────────────

EVENTS_FILE = Path(__file__).parent / "events.json"
RELEVANCE_THRESHOLD = 6  # out of 10 — medium filter

# ─── RSS SOURCES ───────────────────────────────────────────────────────────────
# All free / publicly accessible RSS feeds

RSS_SOURCES = [
    {
        "name": "Front Office Sports",
        "url": "https://frontofficesports.com/feed/",
        "weight": 1.3,  # boost score from high-signal sources
    },
    {
        "name": "Sportico",
        "url": "https://www.sportico.com/feed/",
        "weight": 1.3,
    },
    {
        "name": "The Fourth Quarter",
        "url": "https://www.thefourthquarter.co/feed",
        "weight": 1.2,
    },
    {
        "name": "Pollstar News",
        "url": "https://news.pollstar.com/feed/",
        "weight": 1.2,
    },
    {
        "name": "Billboard Business",
        "url": "https://www.billboard.com/feed/",
        "weight": 1.1,
    },
    {
        "name": "Business of Experience (Substack)",
        "url": "https://businessofexperience.substack.com/feed",
        "weight": 1.1,
    },
    {
        "name": "Axios Sports",
        "url": "https://api.axios.com/feed/sports",
        "weight": 1.1,
    },
    {
        "name": "SportsPro",
        "url": "https://www.sportspromedia.com/rss.xml",
        "weight": 1.1,
    },
    {
        "name": "SBJ Daily",
        "url": "https://www.sportsbusinessjournal.com/SBJ/Issues/rss.aspx",
        "weight": 1.2,
    },
    {
        "name": "Variety Business",
        "url": "https://variety.com/v/biz/feed/",
        "weight": 1.0,
    },
]

# ─── LAYER MAPPING ─────────────────────────────────────────────────────────────
# layer: 0=Content&IP, 1=Physical Infra, 2=Operators&Dist, 3=Service, 4=Tech

LAYER_KEYWORDS = {
    0: [  # Content & IP
        "franchise", "sports league", "media rights", "NFL", "NBA", "MLB", "NHL",
        "Premier League", "Formula One", "F1", "UFC", "WWE", "TKO", "WNBA", "MLS",
        "LaLiga", "Bundesliga", "Champions League", "FIFA", "NCAA", "NIL",
        "women's sports", "NWSL", "PWHL", "college athletics", "sports IP",
        "Arctos", "Fenway Sports", "City Football", "RedBird", "MSG Sports",
        "Hipgnosis", "music catalog", "Coachella", "festival IP", "concert tour",
        "touring rights", "sports ownership", "franchise value", "league expansion",
        "broadcast rights", "streaming rights", "sports fund", "PE sports",
        "sovereign wealth sports", "sports valuation", "Angel City", "Kansas City Current",
    ],
    1: [  # Physical Infrastructure
        "stadium", "arena", "venue", "theme park", "Sphere", "Topgolf", "Meow Wolf",
        "COSM", "entertainment district", "mixed-use", "SoFi Stadium", "Intuit Dome",
        "MSG Entertainment", "Oak View Group", "Populous", "AEG", "ASM Global",
        "Legends Global", "Disney parks", "Universal Studios", "Six Flags", "Cedar Fair",
        "SeaWorld", "Merlin", "LEGOLAND", "competitive socializing", "immersive venue",
        "Puttshack", "Flight Club", "Five Iron Golf", "Battery Atlanta",
        "Cordish", "Hines", "venue construction", "arena renovation", "new stadium",
        "CapEx", "venue naming rights", "premium seating", "hospitality suite",
        "entertainment real estate", "sports real estate",
    ],
    2: [  # Operators & Distribution
        "Live Nation", "Ticketmaster", "AXS", "CTS Eventim", "StubHub", "SeatGeek",
        "Vivid Seats", "Viagogo", "secondary ticketing", "primary ticketing",
        "DOJ Live Nation", "antitrust ticketing", "dynamic pricing",
        "concert promoter", "festival operator", "Lollapalooza", "EDC", "Coachella",
        "Feld Entertainment", "Cirque du Soleil", "Broadway", "touring show",
        "DAZN", "Amazon sports", "Apple TV sports", "Netflix sports",
        "streaming rights", "media deal", "broadcast deal", "rights package",
        "Eventbrite", "Fever", "Dice FM", "ticket sales", "event discovery",
        "OCESA", "TEG", "Superstruct", "live event operator", "promoter",
        "Songkick", "concert discovery",
    ],
    3: [  # Service Providers
        "CAA", "WME", "UTA", "Endeavor", "talent agency", "sports agency",
        "Wasserman", "Octagon", "IMG", "Sportfive", "Two Circles",
        "Roc Nation", "Excel Sports", "athlete representation", "NIL deal",
        "endorsement deal", "sponsorship agency", "brand partnership",
        "Sodexo Live", "Delaware North", "Aramark", "venue hospitality",
        "food beverage venue", "F&B sports", "premium hospitality", "VIP sports",
        "On Location", "Legends hospitality", "event production",
        "TAIT", "NEP Group", "PRG", "stage production", "touring production",
        "Populous architect", "venue design",
    ],
    4: [  # Technology Enablers
        "Sportradar", "Genius Sports", "sports betting", "sports data",
        "betting infrastructure", "official data rights", "sportsbook",
        "Fanatics", "sports merchandise", "fan engagement", "LiveLike",
        "YinzCam", "VenueNext", "venue technology", "smart venue",
        "mobile ordering venue", "Hawk-Eye", "officiating technology",
        "EVS replay", "content production sports", "sports streaming tech",
        "Deltatre", "OTT sports", "Ross Video", "broadcast technology",
        "Kraft Analytics", "Monterosa", "sports analytics", "Digonex",
        "dynamic pricing software", "sports AI", "venue software",
        "Fortress ticketing", "sports tech startup", "fan app",
    ],
}

# ─── COMPANY KEYWORDS ──────────────────────────────────────────────────────────
# Direct company name matching gets a big score boost

COMPANY_NAMES = [
    "FIFA", "Formula One", "F1", "LaLiga", "Major League Baseball", "MLS",
    "Manchester City", "NASCAR", "NBA", "NFL", "NHL", "Premier League",
    "UEFA", "UFC", "WWE", "TKO", "Angel City FC", "Feld Motor Sports",
    "Kansas City Current", "LIV Golf", "Major League Pickleball", "PWHL",
    "Professional Bull Riders", "WNBA", "World Surf League", "Big 12",
    "NCAA", "SEC Conference", "Coachella", "Hipgnosis", "Nederlander",
    "Arctos Partners", "City Football Group", "Fenway Sports Group",
    "Madison Square Garden Sports", "RedBird Capital", "TKO Group",
    "AEG", "Intuit Dome", "Legends Global", "ASM Global", "MSG Entertainment",
    "Oak View Group", "Populous", "SoFi Stadium", "The O2", "Tottenham Stadium",
    "Wembley Stadium", "COSM", "Meow Wolf", "Sphere Entertainment",
    "Cedar Fair", "Disney Experiences", "Merlin Entertainments", "Six Flags",
    "SeaWorld", "Universal Studios", "Activate Games", "Five Iron Golf",
    "Flight Club", "Puttshack", "Topgolf", "Cordish Companies", "Hines",
    "Battery Atlanta", "Broadway Across America", "C3 Presents", "Cirque du Soleil",
    "Eventim Live", "Feld Entertainment", "Insomniac", "Live Nation",
    "OCESA", "Superstruct", "TEG", "teamLab", "AXS", "BookMyShow",
    "CTS Eventim", "Dice FM", "Paciolan", "SeatGeek", "Ticketek",
    "Ticketmaster", "Tixr", "GameTime", "MEGAseats", "StubHub",
    "TicketSwap", "Viagogo", "Vivid Seats", "Eventbrite", "Fever",
    "Songkick", "Amazon Prime Video", "Apple TV", "DAZN",
    "CAA", "Creative Artists Agency", "Endeavor Group", "Excel Sports",
    "Octagon", "Roc Nation Sports", "UTA", "WME Sports", "Wasserman",
    "Aramark", "Delaware North", "Legends", "On Location", "Sodexo Live",
    "Encore", "NEP Group", "PRG", "TAIT", "IMG", "Sportfive", "Two Circles",
    "Digonex", "Genius Sports", "Hawk-Eye", "Sportradar", "LiveLike",
    "Fortress", "VenueNext", "YinzCam", "Deltatre", "EVS", "PlayOn Sports",
    "Ross Video", "Fanatics", "Kraft Analytics", "Monterosa",
]

# ─── HIGH SIGNAL EVENT KEYWORDS ────────────────────────────────────────────────
# These indicate the event is significant — raises the score

HIGH_SIGNAL_TERMS = [
    # Deals & M&A
    "acquires", "acquisition", "merger", "merges with", "buys", "purchased",
    "takeover", "deal", "stake", "minority stake", "majority stake",
    "joint venture", "partnership", "strategic investment",

    # Fundraising
    "raises", "funding", "Series A", "Series B", "Series C", "Series D",
    "seed round", "investment round", "valuation", "valued at", "IPO",
    "goes public", "SPAC", "private equity", "PE investment", "venture capital",
    "VC funding", "$1B", "$500M", "$100M", "$50M", "billion", "million",

    # Rights & Contracts
    "media rights", "broadcast deal", "streaming deal", "rights agreement",
    "new contract", "extension", "renewal", "exclusive deal", "signed",
    "multi-year deal", "landmark deal", "record deal",

    # Business Events
    "launches", "opens", "debuts", "expands", "expansion",
    "new stadium", "new arena", "new venue", "groundbreaking",
    "sold out", "record revenue", "record attendance", "record valuation",
    "franchise record", "highest-grossing",

    # Legal & Regulatory
    "DOJ", "antitrust", "lawsuit", "settlement", "ruling", "approved",
    "investigation", "FTC", "regulatory", "breakup",

    # Leadership
    "CEO", "appointed", "names new", "hires", "resigns", "steps down",
]

# ─── NOISE FILTERS ─────────────────────────────────────────────────────────────
# Skip articles containing these terms (irrelevant)

NOISE_TERMS = [
    "fantasy football", "DFS", "daily fantasy", "gambling addiction",
    "injury report", "injury update", "player stats", "box score",
    "game recap", "highlights", "trade deadline player", "waiver wire",
    "fantasy draft", "mock draft", "player ranking", "weather forecast",
    "ticket giveaway", "contest", "sweepstakes",
]

# ─── ACCESS TYPE MAPPING ───────────────────────────────────────────────────────

PUBLIC_COMPANIES = [
    "Live Nation", "Ticketmaster", "MSG Entertainment", "MSG Sports",
    "Sportradar", "Genius Sports", "Vivid Seats", "Eventbrite", "Topgolf",
    "Six Flags", "Cedar Fair", "SeaWorld", "Disney", "Universal",
    "TKO Group", "WWE", "UFC", "Formula One", "Sphere Entertainment",
    "CTS Eventim", "Fanatics", "EVS", "Aramark", "Sodexo",
    "Hipgnosis", "Amazon", "Apple", "Netflix",
]

VENTURE_COMPANIES = [
    "Meow Wolf", "Five Iron Golf", "Dice FM", "SeatGeek", "BookMyShow",
    "Fever", "LiveLike", "VenueNext", "YinzCam", "Monterosa", "Tixr",
    "GameTime", "TicketSwap", "Activate Games", "Puttshack",
]


# ─── SCORING ───────────────────────────────────────────────────────────────────

def score_article(title: str, summary: str, source_weight: float) -> tuple[int, int]:
    """
    Returns (score, layer_idx)
    score: 0-10, layer: 0-4 (-1 = unclear)
    """
    text = (title + " " + summary).lower()
    score = 0
    layer_scores = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

    # Check noise filters first
    for noise in NOISE_TERMS:
        if noise.lower() in text:
            return 0, -1

    # Company name match (strong signal)
    for company in COMPANY_NAMES:
        if company.lower() in text:
            score += 3
            break

    # High signal event terms
    for term in HIGH_SIGNAL_TERMS:
        if term.lower() in text:
            score += 1.5
            break  # only count once

    # Additional high signal terms
    signal_count = sum(1 for t in HIGH_SIGNAL_TERMS if t.lower() in text)
    score += min(signal_count * 0.5, 2)  # cap bonus at 2

    # Layer keyword matching
    for layer_idx, keywords in LAYER_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw.lower() in text)
        layer_scores[layer_idx] = matches
        score += min(matches * 0.4, 2)

    # Apply source weight
    score *= source_weight

    # Determine most likely layer
    best_layer = max(layer_scores, key=layer_scores.get)
    if layer_scores[best_layer] == 0:
        best_layer = -1

    return min(round(score), 10), best_layer


def get_access_type(title: str, summary: str) -> str:
    text = (title + " " + summary).lower()
    for company in PUBLIC_COMPANIES:
        if company.lower() in text:
            return "public"
    for company in VENTURE_COMPANIES:
        if company.lower() in text:
            return "venture"
    # Check for PE/fundraising signals
    pe_signals = ["private equity", "pe firm", "pe fund", "buyout", "kkr", "blackstone",
                  "carlyle", "apollo", "sixth street", "silver lake", "tpg", "cvc"]
    if any(s in text for s in pe_signals):
        return "pe"
    # Default: PE for unknown private
    return "pe"


def make_event_id(date: str, headline: str) -> str:
    """Stable hash for deduplication"""
    return hashlib.md5(f"{date}:{headline}".encode()).hexdigest()[:12]


def clean_headline(text: str) -> str:
    """Strip HTML tags, normalize whitespace"""
    text = BeautifulSoup(text, "html.parser").get_text()
    text = re.sub(r'\s+', ' ', text).strip()
    # Truncate at sentence boundary if too long
    if len(text) > 140:
        text = text[:137] + "..."
    return text


def format_date(entry) -> str:
    """Extract and format date as YYYY-MM"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        return dt.strftime("%Y-%m")
    return datetime.now(timezone.utc).strftime("%Y-%m")


# ─── MAIN ──────────────────────────────────────────────────────────────────────

def load_existing_events() -> tuple[list, set]:
    """Load events.json and return (events_list, set_of_ids)"""
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE) as f:
            events = json.load(f)
    else:
        events = []
    ids = {e.get("id", "") for e in events}
    return events, ids


def save_events(events: list):
    # Sort by date descending
    events.sort(key=lambda e: e["date"], reverse=True)
    with open(EVENTS_FILE, "w") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(events)} total events to {EVENTS_FILE}")


def scrape_all() -> list:
    """Pull all RSS feeds and return list of new candidate events"""
    candidates = []

    for source in RSS_SOURCES:
        print(f"\n📡 Fetching: {source['name']}")
        try:
            feed = feedparser.parse(
                source["url"],
                request_headers={"User-Agent": "ExperienceEconomyBot/1.0"}
            )
            entries = feed.entries[:30]  # max 30 per source per run
            print(f"   Found {len(entries)} entries")

            for entry in entries:
                title = clean_headline(getattr(entry, "title", ""))
                summary = clean_headline(getattr(entry, "summary", ""))
                if not title:
                    continue

                score, layer = score_article(title, summary, source["weight"])
                if score < RELEVANCE_THRESHOLD or layer == -1:
                    continue

                date = format_date(entry)
                link = getattr(entry, "link", "")
                access = get_access_type(title, summary)
                event_id = make_event_id(date, title)

                candidates.append({
                    "id": event_id,
                    "date": date,
                    "headline": title,
                    "company": "",  # auto-detect below
                    "layer": layer,
                    "access": access,
                    "source": source["name"],
                    "url": link,
                    "score": score,
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                })

        except Exception as e:
            print(f"   ❌ Error fetching {source['name']}: {e}")

    return candidates


def detect_company(headline: str) -> str:
    """Try to detect the most relevant company name from the headline"""
    for company in sorted(COMPANY_NAMES, key=len, reverse=True):  # longest match first
        if company.lower() in headline.lower():
            return company
    return ""


def run():
    print("🚀 Experience Economy Scraper starting...")
    print(f"   Threshold: {RELEVANCE_THRESHOLD}/10")
    print(f"   Sources: {len(RSS_SOURCES)}")

    existing_events, existing_ids = load_existing_events()
    print(f"   Existing events: {len(existing_events)}")

    candidates = scrape_all()
    print(f"\n📊 Candidates after filtering: {len(candidates)}")

    new_events = []
    for c in candidates:
        if c["id"] in existing_ids:
            continue  # deduplicate
        # Auto-detect company if blank
        if not c["company"]:
            c["company"] = detect_company(c["headline"])
        new_events.append(c)
        existing_ids.add(c["id"])
        print(f"   ✨ [{c['score']}/10] Layer {c['layer']} | {c['date']} | {c['headline'][:80]}")

    print(f"\n🆕 New events added: {len(new_events)}")

    all_events = existing_events + new_events
    save_events(all_events)

    # Write summary for GitHub Actions step output
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "w") as f:
            f.write(f"## Scraper Run {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n")
            f.write(f"- **Sources checked:** {len(RSS_SOURCES)}\n")
            f.write(f"- **Candidates found:** {len(candidates)}\n")
            f.write(f"- **New events added:** {len(new_events)}\n")
            f.write(f"- **Total events:** {len(all_events)}\n\n")
            if new_events:
                f.write("### New Events\n")
                for e in new_events[:20]:
                    f.write(f"- [{e['headline'][:80]}]({e['url']})\n")

    return len(new_events)


if __name__ == "__main__":
    run()
