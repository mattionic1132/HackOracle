import os
import sys
import requests
from dotenv import load_dotenv

import scraper
import database
import brain

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
TELEGRAM_MAX_LENGTH = 4096


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = TELEGRAM_API.format(token=token)
    chunks = [text[i : i + TELEGRAM_MAX_LENGTH] for i in range(0, len(text), TELEGRAM_MAX_LENGTH)]
    for chunk in chunks:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown"},
            timeout=10,
        )
        if not resp.ok:
            print(f"[telegram] Failed to send message: {resp.text}")


def format_message(hackathon: dict, ideas: str) -> str:
    return (
        f"🏆 *New Hackathon Alert!*\n\n"
        f"*{hackathon.get('title', 'Unknown')}*\n"
        f"📍 Source: {hackathon.get('source', 'N/A')}\n"
        f"👥 Participants: {hackathon.get('participants', 'N/A')}\n"
        f"🎯 Theme: {hackathon.get('theme', 'N/A')}\n"
        f"💰 Prize: {hackathon.get('prize', 'N/A')}\n"
        f"⏰ Deadline: {hackathon.get('deadline', 'N/A')}\n"
        f"🔗 {hackathon.get('url', '')}\n\n"
        f"--- *HackOracle Winning Ideas* ---\n\n"
        f"{ideas}"
    )


def main() -> None:
    load_dotenv()

    print("[main] Initialising HackOracle...")
    db = database.init_client()

    print("[main] Fetching hackathons...")
    all_hackathons = scraper.get_all_hackathons()

    if not all_hackathons:
        print("[main] No hackathons found. Exiting.")
        sys.exit(0)

    known_urls = database.get_known_urls(db)
    past_hackathons = database.get_recent_hackathons(db, limit=20)
    new_count = 0

    for hack in all_hackathons:
        url = hack.get("url", "")
        if not url or url in known_urls:
            continue

        print(f"[main] New hackathon found: {hack.get('title')}")

        try:
            ideas = brain.analyze_hackathon(hack, past_hackathons)
        except Exception as exc:
            print(f"[main] AI analysis failed for '{hack.get('title')}': {exc}")
            ideas = "AI analysis unavailable."

        try:
            database.save_hackathon(db, {**hack, "ai_analysis": ideas})
        except Exception as exc:
            print(f"[main] DB save failed for '{hack.get('title')}': {exc} — skipping notification")
            continue

        try:
            send_telegram(format_message(hack, ideas))
        except Exception as exc:
            print(f"[main] Telegram notify failed for '{hack.get('title')}': {exc}")

        new_count += 1

    print(f"[main] Done. {new_count} new hackathon(s) processed.")


if __name__ == "__main__":
    main()
