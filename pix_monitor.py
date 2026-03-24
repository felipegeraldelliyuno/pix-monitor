#!/usr/bin/env python3
"""
Monitor de notícias sobre instabilidade no Pix
Envia alertas no Slack quando novas notícias são encontradas
"""

import feedparser
import json
import os
import requests
from datetime import datetime, timezone, timedelta

SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
STATE_FILE = "state.json"

# Janela de tempo para considerar notícias do mesmo incidente (em horas)
JANELA_INCIDENTE_HORAS = 12

FEEDS = [
    "https://news.google.com/rss/search?q=queda+pix&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss/search?q=instabilidade+pix&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss/search?q=pix+fora+do+ar&hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://news.google.com/rss/search?q=pix+indisponivel&hl=pt-BR&gl=BR&ceid=BR:pt-419",
]


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            data = json.load(f)
            return set(data.get("seen", [])), data.get("ultimo_incidente")
    return set(), None


def save_state(seen, ultimo_incidente):
    with open(STATE_FILE, "w") as f:
        json.dump({"seen": list(seen), "ultimo_incidente": ultimo_incidente}, f)


def e_novo_incidente(ultimo_incidente):
    if not ultimo_incidente:
        return True
    ultimo = datetime.fromisoformat(ultimo_incidente)
    agora = datetime.now(timezone.utc)
    return (agora - ultimo) > timedelta(hours=JANELA_INCIDENTE_HORAS)


def send_slack(title, url, source, published, novo_incidente, contagem):
    if novo_incidente:
        cabecalho = ":rotating_light: <!here> *NOVO INCIDENTE — Pix com instabilidade*"
    else:
        cabecalho = f":newspaper: *Mais cobertura do incidente em andamento* (notícia #{contagem})"

    text = (
        f"{cabecalho}\n"
        f"*{title}*\n"
        f"_{source}_ — {published}\n"
        f"{url}"
    )
    response = requests.post(SLACK_WEBHOOK, json={"text": text}, timeout=10)
    if response.status_code != 200:
        print(f"Erro ao enviar pro Slack: {response.status_code} {response.text}")


def main():
    seen, ultimo_incidente = load_state()
    new_seen = set(seen)
    found = 0
    contagem_incidente = 0

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

                novo = e_novo_incidente(ultimo_incidente)

                if novo:
                    contagem_incidente = 1
                    ultimo_incidente = datetime.now(timezone.utc).isoformat()
                    print(f"NOVO INCIDENTE: {title}")
                else:
                    contagem_incidente += 1
                    print(f"Cobertura #{contagem_incidente}: {title}")

                send_slack(title, url, source, published, novo, contagem_incidente)

        except Exception as e:
            print(f"Erro ao processar feed: {e}")

    save_state(new_seen, ultimo_incidente)
    print(f"Concluído. {found} nova(s) notícia(s) enviada(s).")


if __name__ == "__main__":
    main()
