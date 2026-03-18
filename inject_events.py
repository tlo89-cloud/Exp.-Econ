#!/usr/bin/env python3
"""
inject_events.py
Reads events.json and injects it into experience-economy-map.html
replacing the TIMELINE_EVENTS array with the merged set
(hardcoded historical + scraped news)
"""

import json
import re
from pathlib import Path

EVENTS_FILE = Path(__file__).parent / "events.json"
HTML_FILE = Path(__file__).parent / "experience-economy-map.html"

# Hardcoded historical events that always stay in the map
# (these are the ones we built by hand in Phase 1)
HISTORICAL_EVENTS = [
    { "date": "2005-01", "headline": "YouTube launches, reshaping live content distribution", "company": "YouTube", "layer": 0, "access": "public" },
    { "date": "2012-06", "headline": "Formula 1 sold to Liberty Media for $4.4B", "company": "Formula One Group", "layer": 0, "access": "public" },
    { "date": "2016-09", "headline": "UFC sold to Endeavor/WME for $4B — first PE acquisition of major sports league", "company": "UFC", "layer": 0, "access": "public" },
    { "date": "2019-03", "headline": "F1 Drive to Survive launches on Netflix — sport fandom goes global", "company": "Formula One Group", "layer": 0, "access": "public" },
    { "date": "2021-08", "headline": "NFL opens ownership to PE firms for first time", "company": "NFL", "layer": 0, "access": "ref" },
    { "date": "2022-06", "headline": "CVC invests €2.7B for 10% stake in LaLiga commercial unit", "company": "LaLiga", "layer": 0, "access": "pe" },
    { "date": "2022-10", "headline": "Fenway Sports Group valued at $7.35B — Liverpool FC alone worth ~$6B", "company": "Fenway Sports Group", "layer": 0, "access": "pe" },
    { "date": "2023-04", "headline": "TKO Group formed — UFC and WWE merge under Endeavor", "company": "TKO Group Holdings", "layer": 0, "access": "public" },
    { "date": "2023-07", "headline": "KKR acquires majority stake in Arctos Partners at $1.4B valuation", "company": "Arctos Partners", "layer": 0, "access": "pe" },
    { "date": "2023-09", "headline": "NWSL secures $240M media rights deal — 40x increase in annual value", "company": "Angel City FC", "layer": 0, "access": "pe" },
    { "date": "2024-02", "headline": "WNBA signs 11-year $2.2B media deal — league revenue set to triple", "company": "WNBA", "layer": 0, "access": "pe" },
    { "date": "2024-04", "headline": "Caitlin Clark effect — WNBA draft viewership beats NBA and NHL playoffs", "company": "WNBA", "layer": 0, "access": "pe" },
    { "date": "2024-06", "headline": "NBA signs $76B media rights deal with Amazon, NBC, ESPN through 2036", "company": "NBA", "layer": 0, "access": "ref" },
    { "date": "2024-08", "headline": "Goldman Sachs takes majority stake in Excel Sports Management at ~$1B valuation", "company": "Excel Sports Management", "layer": 0, "access": "pe" },
    { "date": "2025-01", "headline": "PWHL adds Seattle and Vancouver — fastest-growing women's sports league", "company": "PWHL", "layer": 0, "access": "pe" },
    { "date": "2010-04", "headline": "Topgolf opens first US location — competitive socializing category born", "company": "Topgolf", "layer": 1, "access": "public" },
    { "date": "2017-08", "headline": "Battery Atlanta opens — sports-anchored mixed-use district becomes template", "company": "The Battery Atlanta", "layer": 1, "access": "public" },
    { "date": "2020-09", "headline": "SoFi Stadium opens — first privately financed NFL stadium, $5.5B development", "company": "SoFi Stadium", "layer": 1, "access": "ref" },
    { "date": "2021-07", "headline": "Sphere breaks ground in Las Vegas — $2.3B immersive venue bet", "company": "Sphere Entertainment Co.", "layer": 1, "access": "public" },
    { "date": "2023-09", "headline": "Sphere Las Vegas opens — U2 residency sells out instantly", "company": "Sphere Entertainment Co.", "layer": 1, "access": "public" },
    { "date": "2023-11", "headline": "Legends acquires ASM Global for $2.4B — largest venue management consolidation ever", "company": "Legends Global", "layer": 1, "access": "pe" },
    { "date": "2024-01", "headline": "Six Flags and Cedar Fair merge creating 42-park regional giant", "company": "Six Flags Entertainment", "layer": 1, "access": "public" },
    { "date": "2024-06", "headline": "Intuit Dome opens — most tech-integrated arena ever built", "company": "Intuit Dome", "layer": 1, "access": "ref" },
    { "date": "2024-07", "headline": "Topgolf takes $1.45B impairment charge — competitive socializing durability questioned", "company": "Topgolf", "layer": 1, "access": "public" },
    { "date": "2025-05", "headline": "Universal's Epic Universe opens — biggest theme park launch in decades", "company": "Universal Destinations & Experiences", "layer": 1, "access": "public" },
    { "date": "2025-10", "headline": "Sphere Q4 revenue +62% YoY — first operating profit quarter, global expansion announced", "company": "Sphere Entertainment Co.", "layer": 1, "access": "public" },
    { "date": "2026-01", "headline": "CPKC Stadium named most valuable women's sports venue — $41M local revenue", "company": "Kansas City Current", "layer": 1, "access": "pe" },
    { "date": "2010-01", "headline": "Live Nation and Ticketmaster merge — DOJ approves with conditions", "company": "Live Nation", "layer": 2, "access": "public" },
    { "date": "2016-06", "headline": "Amazon acquires Twitch — streaming enters live events race", "company": "Amazon Prime Video", "layer": 2, "access": "public" },
    { "date": "2020-03", "headline": "COVID shutters all live events — $30B+ revenue evaporates overnight", "company": "Live Nation", "layer": 2, "access": "public" },
    { "date": "2021-06", "headline": "Apple TV+ signs $2.5B MLS deal — streaming goes all-in on live sports", "company": "Apple TV", "layer": 2, "access": "public" },
    { "date": "2022-11", "headline": "StubHub files for IPO at $13.6B valuation", "company": "StubHub", "layer": 2, "access": "pe" },
    { "date": "2023-03", "headline": "Taylor Swift Eras Tour goes on sale — Ticketmaster crashes, DOJ scrutiny intensifies", "company": "Ticketmaster", "layer": 2, "access": "public" },
    { "date": "2024-05", "headline": "DOJ files antitrust suit against Live Nation/Ticketmaster — breakup demanded", "company": "Live Nation", "layer": 2, "access": "public" },
    { "date": "2024-12", "headline": "Taylor Swift Eras Tour ends — $2B+ gross, highest-grossing tour in history", "company": "Live Nation", "layer": 2, "access": "public" },
    { "date": "2026-03", "headline": "DOJ vs Live Nation antitrust trial begins", "company": "Live Nation", "layer": 2, "access": "public" },
    { "date": "2019-06", "headline": "CAA sold to TPG at $1.5B valuation — agency as institutional asset validated", "company": "Creative Artists Agency (CAA)", "layer": 3, "access": "pe" },
    { "date": "2021-09", "headline": "NIL era begins — college athletes can monetize name, image, likeness", "company": "NCAA", "layer": 3, "access": "ref" },
    { "date": "2022-08", "headline": "Sodexo Live reports sports hospitality market CAGR of 15.5% through 2036", "company": "Sodexo Live!", "layer": 3, "access": "public" },
    { "date": "2023-07", "headline": "CAA majority stake sold to Artémis (Pinault family) at ~$7B valuation", "company": "Creative Artists Agency (CAA)", "layer": 3, "access": "pe" },
    { "date": "2024-03", "headline": "TAIT builds Taylor Swift Eras Tour stage — most complex touring production ever", "company": "TAIT", "layer": 3, "access": "pe" },
    { "date": "2018-05", "headline": "US Supreme Court overturns federal sports betting ban — $10B+ market unlocked", "company": "Sportradar", "layer": 4, "access": "public" },
    { "date": "2021-10", "headline": "Sportradar IPO at $8B valuation — betting data infrastructure goes public", "company": "Sportradar", "layer": 4, "access": "public" },
    { "date": "2022-04", "headline": "Fanatics valued at $31B — licensed merchandise platform reaches scale", "company": "Fanatics", "layer": 4, "access": "pe" },
    { "date": "2023-06", "headline": "Genius Sports signs exclusive NFL data deal — official betting data moat deepens", "company": "Genius Sports", "layer": 4, "access": "public" },
    { "date": "2024-09", "headline": "AI-generated sports highlights reach broadcast quality — content production disrupted", "company": "EVS", "layer": 4, "access": "public" },
    { "date": "2025-06", "headline": "Hawk-Eye AI officiating adopted across Premier League, NBA, and ATP", "company": "Hawk-Eye Innovations", "layer": 4, "access": "ref" },
]


def load_scraped_events() -> list:
    if EVENTS_FILE.exists():
        with open(EVENTS_FILE) as f:
            return json.load(f)
    return []


def merge_events(historical: list, scraped: list) -> list:
    """
    Merge historical + scraped events.
    Scraped events only included if score >= 7 (high quality).
    Deduplication by headline similarity.
    """
    seen_headlines = {e["headline"].lower()[:60] for e in historical}
    merged = list(historical)

    for e in scraped:
        # Only high-quality scraped events in the timeline
        if e.get("score", 0) < 7:
            continue
        key = e["headline"].lower()[:60]
        if key in seen_headlines:
            continue
        seen_headlines.add(key)
        # Clean up scraped event format to match timeline format
        merged.append({
            "date": e["date"],
            "headline": e["headline"],
            "company": e.get("company", ""),
            "layer": e["layer"],
            "access": e["access"],
        })

    merged.sort(key=lambda e: e["date"], reverse=True)
    return merged


def inject_into_html(events: list):
    """Replace TIMELINE_EVENTS array in the HTML file"""
    with open(HTML_FILE) as f:
        html = f.read()

    # Build new JS array
    events_js = "const TIMELINE_EVENTS = " + json.dumps(events, indent=2) + ";"

    # Replace existing TIMELINE_EVENTS array
    pattern = r'const TIMELINE_EVENTS = \[[\s\S]*?\];'
    if re.search(pattern, html):
        new_html = re.sub(pattern, events_js, html)
        with open(HTML_FILE, "w") as f:
            f.write(new_html)
        print(f"✅ Injected {len(events)} events into {HTML_FILE}")
    else:
        print("⚠️  Could not find TIMELINE_EVENTS in HTML — skipping injection")


def run():
    print("🔄 Injecting events into HTML...")
    scraped = load_scraped_events()
    print(f"   Historical events: {len(HISTORICAL_EVENTS)}")
    print(f"   Scraped events: {len(scraped)}")

    merged = merge_events(HISTORICAL_EVENTS, scraped)
    high_quality_scraped = [e for e in merged if e not in HISTORICAL_EVENTS]
    print(f"   High-quality scraped added: {len(high_quality_scraped)}")
    print(f"   Total merged: {len(merged)}")

    inject_into_html(merged)


if __name__ == "__main__":
    run()
