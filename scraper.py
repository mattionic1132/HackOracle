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


def _scrape_devpost() -> list[dict]:
    """Uses Devpost's JSON API — no HTML parsing, not blocked."""
    try:
        resp = requests.get(
            "https://devpost.com/api/hackathons",
            params={"search": "singapore", "status[]": ["open", "upcoming"], "per_page": 50},
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        hackathons = []
        for h in resp.json().get("hackathons", []):
            themes = [t.get("name", "") for t in h.get("themes", [])]
            hackathons.append({
                "title": h.get("title", "Unknown"),
                "url": h.get("url", ""),
                "source": "Devpost",
                "theme": ", ".join(themes) if themes else "General",
                "prize": h.get("prize_amount") or "N/A",
                "deadline": h.get("submission_period_dates") or "N/A",
            })
        return hackathons
    except Exception as exc:
        print(f"[scraper] Devpost failed: {exc}")
        return []


def _scrape_luma() -> list[dict]:
    """Scrapes lu.ma Singapore tech events for hackathons."""
    try:
        resp = requests.get(
            "https://lu.ma/singapore",
            headers=HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        hackathons = []
        for card in soup.select("a[href*='/']"):
            title_el = card.select_one("h3, h2, [class*='title'], [class*='name']")
            title = _safe_text(title_el, "").strip()
            href = card.get("href", "")
            if not title or not href or "hackathon" not in title.lower():
                continue
            hack_url = href if href.startswith("http") else f"https://lu.ma{href}"
            date_el = card.select_one("time, [class*='date'], [class*='time']")
            hackathons.append({
                "title": title,
                "url": hack_url,
                "source": "Luma",
                "theme": "General",
                "prize": "N/A",
                "deadline": _safe_text(date_el),
            })
        return hackathons
    except Exception as exc:
        print(f"[scraper] Luma failed: {exc}")
        return []


def get_all_hackathons() -> list[dict]:
    tasks = {
        "devpost": _scrape_devpost,
        "luma": _scrape_luma,
    }

    results: dict[str, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {pool.submit(fn): name for name, fn in tasks.items()}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    devpost = results.get("devpost", [])
    luma = results.get("luma", [])
    print(f"[scraper] Found {len(devpost)} Devpost + {len(luma)} Luma hackathons")
    return devpost + luma
