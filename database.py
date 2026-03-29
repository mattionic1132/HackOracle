import os
from supabase import create_client, Client


def init_client() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def get_known_urls(client: Client) -> set[str]:
    result = client.table("hackathons").select("url").execute()
    return {row["url"] for row in result.data}


def save_hackathon(client: Client, data: dict) -> None:
    client.table("hackathons").upsert(data, on_conflict="url").execute()


def get_recent_hackathons(client: Client, limit: int = 20) -> list[dict]:
    result = (
        client.table("hackathons")
        .select("title, theme, ai_analysis")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data
