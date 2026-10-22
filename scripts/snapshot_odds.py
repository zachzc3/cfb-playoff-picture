"""Record today's playoff odds for every team into data/history.js.

Opens the site in a headless browser with no picks, waits for its season simulations to finish, and reads each
team's playoff chance. ESPN's FPI playoff chance comes from data/season.js. One snapshot per day (Eastern time);
a later run on the same day replaces that day's numbers.

Usage: python scripts/snapshot_odds.py   (needs: pip install playwright && python -m playwright install chromium)
"""
import json
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SEASON = ROOT / "data" / "season.js"
OUT = ROOT / "data" / "history.js"
PREFIX = "window.CFB_HISTORY = "


def load_js(path, prefix):
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text[len(prefix):].rstrip(";"))


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def simulate():
    port = free_port()
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "-d", str(ROOT)],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.route("**/combiner/**", lambda route: route.abort())  # team logos aren't needed
            page.goto(f"http://127.0.0.1:{port}/index.html")
            page.wait_for_function("typeof ODDS !== 'undefined' && ODDS && !ODDS.running && ODDS.done >= ODDS.N",
                                   timeout=300_000)
            odds = page.evaluate("() => Object.fromEntries(FBS.map(i => [i, Math.round(ODDS.cnt[i].cfp / ODDS.done * 1000) / 10]))")
            browser.close()
            return odds
    finally:
        server.terminate()


def main():
    ours = simulate()
    season = load_js(SEASON, "window.CFB_DATA = ")
    espn = {t["id"]: (t.get("espn") or {}).get("probmakeplayoffs") for t in season["teams"]}
    hist = load_js(OUT, PREFIX) if OUT.exists() else {"dates": [], "ours": {}, "espn": {}}

    today = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    if today in hist["dates"]:
        k = hist["dates"].index(today)
    else:
        hist["dates"].append(today)
        k = len(hist["dates"]) - 1
    for key, values in (("ours", ours), ("espn", espn)):
        for tid, v in values.items():
            series = hist[key].setdefault(tid, [])
            series.extend([None] * (len(hist["dates"]) - len(series)))
            series[k] = v

    # Keep every AP poll and CFP ranking, keyed by release date, so past weeks can be compared with the model
    polls = hist.setdefault("polls", {})
    for kind, poll in (season.get("polls") or {}).items():
        if poll.get("date"):
            polls.setdefault(kind, {})[poll["date"][:10]] = {"name": poll.get("headline") or poll.get("name", ""),
                                                             "ranks": poll["ranks"]}

    OUT.write_text(PREFIX + json.dumps(hist, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"snapshot for {today}: {len(ours)} teams, {len(hist['dates'])} days of history")


if __name__ == "__main__":
    main()
