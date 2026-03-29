import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}
TIMEOUT = 15


def _safe_text(element, default="N/A") -> str:
    return element.get_text(strip=True) if element else default


def _fetch_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def _scrape_devpost_status(status: str) -> list[dict]:
    try:
        soup = _fetch_soup(f"https://devpost.com/hackathons?search=singapore&status={status}")
        hackathons = []
        for tile in soup.select("a.hackathon-tile"):
            href = tile.get("href", "")
            hack_url = href if href.startswith("http") else f"https://devpost.com{href}"
            themes = [t.get_text(strip=True) for t in tile.select(".hackathon-tag")]
            hackathons.append({
                "title": _safe_text(tile.select_one(".hackathon-tile-title h5"), "Unknown"),
                "url": hack_url,
                "source": "Devpost",
                "theme": ", ".join(themes) if themes else "General",
                "prize": _safe_text(tile.select_one(".prize-amount")),
                "deadline": _safe_text(tile.select_one(".submission-period")),
            })
        return hackathons
    except Exception as exc:
        print(f"[scraper] Devpost ({status}) failed: {exc}")
        return []


def _scrape_eventbrite() -> list[dict]:
    try:
        soup = _fetch_soup("https://www.eventbrite.sg/d/singapore--singapore/hackathon/")
        hackathons = []
        for card in soup.select("[data-testid='event-card']"):
            title_el = card.select_one("h2, h3, [class*='event-title'], [class*='eds-is-hidden-accessible']")
            link_el = card.select_one("a[href]")
            title = _safe_text(title_el, "")
            hack_url = link_el["href"] if link_el else ""
            if not title or not hack_url:
                continue
            hackathons.append({
                "title": title,
                "url": hack_url,
                "source": "Eventbrite",
                "theme": "General",
                "prize": "N/A",
                "deadline": _safe_text(card.select_one("p[class*='date'], time, [class*='date-info']")),
            })
        return hackathons
    except Exception as exc:
        print(f"[scraper] Eventbrite failed: {exc}")
        return []


def get_all_hackathons() -> list[dict]:
    tasks = [
        ("devpost_open", lambda: _scrape_devpost_status("open")),
        ("devpost_upcoming", lambda: _scrape_devpost_status("upcoming")),
        ("eventbrite", _scrape_eventbrite),
    ]

    results: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    all_hackathons = (
        results.get("devpost_open", [])
        + results.get("devpost_upcoming", [])
        + results.get("eventbrite", [])
    )
    devpost_count = len(results.get("devpost_open", [])) + len(results.get("devpost_upcoming", []))
    print(f"[scraper] Found {devpost_count} Devpost + {len(results.get('eventbrite', []))} Eventbrite hackathons")
    return all_hackathons
