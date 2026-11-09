"""
Scrape 15 core PostgreSQL runtime-config pages.
Run: python -m app.scrape_docs
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup

BASE = "https://www.postgresql.org/docs/16/"

PAGES = [
    "runtime-config-connection.html",
    "runtime-config-resource.html",
    "runtime-config-wal.html",
    "runtime-config-query.html",
    "runtime-config-client.html",
    "runtime-config-error-handling.html",
    "runtime-config-logging.html",
    "runtime-config-preset.html",
    "runtime-config-custom.html",
    "runtime-config-compatible.html",
    "runtime-config-locks.html",
    "runtime-config-statistics.html",
]

OUTPUT = os.path.join("data", "raw_pages.json")


def scrape_page(url: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # 页面标题
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True).rstrip(" #") if title_tag else url

    content = soup.find("div", id="docContent") or soup.body
    for tag in content.find_all(["script", "style", "nav", "table"]):
        tag.decompose()

    lines = []
    for el in content.find_all(["h1", "h2", "h3", "dt", "p", "pre"]):
        text = el.get_text(" ", strip=True).rstrip(" #").strip()
        if not text:
            continue
        if el.name in ("h1", "h2", "h3"):
            lines.append("\n## " + text)
        elif el.name == "dt":
            lines.append("\n**" + text + "**")
        elif el.name == "pre":
            lines.append("\n```\n" + text + "\n```")
        else:
            lines.append(text)

    return {
        "url": url,
        "title": title,
        "text": "\n\n".join(lines),
    }


def main():
    os.makedirs("data", exist_ok=True)
    results = []
    for i, page in enumerate(PAGES, 1):
        url = BASE + page
        print(f"[{i}/{len(PAGES)}] {page}")
        try:
            results.append(scrape_page(url))
            time.sleep(0.5)  # 礼貌性延迟，避免被服务器限流
        except Exception as e:
            print(f"  FAILED: {e}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    total_chars = sum(len(r["text"]) for r in results)
    print(f"\nSaved {len(results)} pages, {total_chars} characters to {OUTPUT}")


if __name__ == "__main__":
    main()