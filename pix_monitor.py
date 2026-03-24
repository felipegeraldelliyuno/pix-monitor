#!/usr/bin/env python3
"""
Monitor de notícias sobre instabilidade no Pix
Envia alertas no Slack quando novas notícias são encontradas
"""

import feedparser
import json
import os
import requests
from datetime import datetime

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
SEEN_FILE = "seen.json"

FEEDS = [
    "https://news.google.com/rss/search?q=queda+pix&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss/search?q=instabilidade+pix&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss/search?q=pix+fora+do+ar&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss/search?q=pix+indisponivel&hl=pt-BR&gl=BR&ceid=BR:pt-419",
]


def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_slack(title, url, source, published):
    text = (
        f":rotating_light: *Nova notícia sobre instabilidade no Pix*\n"
        f"*{title}*\n"
        f"_{source}_ — {published}\n"
        f"{url}"
    )
    response = requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=10)
    if response.status_code != 200:
        print(f"Erro ao enviar pro Slack: {response.status_code} {response.text}")


def main():
    seen = load_seen()
    new_seen = set(seen)
    found = 0

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                entry_id = entry.get("id") or entry.get("link")
                if not entry_id or entry_id in seen:
                    continue

                new_seen.add(entry_id)
                found += 1

                title = entry.get("title", "Sem título")
                url = entry.get("link", "")
                source = entry.get("source", {}).get("title", "Google News")
                published = entry.get("published", "")

                send_slack(title, url, source, published)
                print(f"Notícia enviada: {title}")

        except Exception as e:
            print(f"Erro ao processar feed: {e}")

    save_seen(new_seen)
    print(f"Concluído. {found} nova(s) notícia(s) enviada(s).")


if __name__ == "__main__":
    main()
