import os
import requests

TABLE = "hackathons"


def init_client() -> requests.Session:
    session = requests.Session()
    key = os.environ["SUPABASE_KEY"]
    session.headers.update({
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    })
    session.base_url = os.environ["SUPABASE_URL"].rstrip("/") + f"/rest/v1/{TABLE}"
    return session


def get_known_urls(session: requests.Session) -> set[str]:
    resp = session.get(session.base_url, params={"select": "url"})
    resp.raise_for_status()
    return {row["url"] for row in resp.json()}


def save_hackathon(session: requests.Session, data: dict) -> None:
    resp = session.post(
        session.base_url,
        json=data,
        headers={"Prefer": "resolution=merge-duplicates"},
    )
    resp.raise_for_status()


def get_recent_hackathons(session: requests.Session, limit: int = 20) -> list[dict]:
    resp = session.get(
        session.base_url,
        params={
            "select": "title,theme,ai_analysis",
            "order": "created_at.desc",
            "limit": limit,
        },
    )
    resp.raise_for_status()
    return resp.json()
