"""Pull the FBS schedule, results and conference lineups from ESPN's public API.

Writes data/season.js (window.CFB_DATA = {...}) so index.html works offline.
Usage: python scripts/fetch_data.py [season]
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEASON = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
BASE = "https://site.api.espn.com/apis"
OUT = Path(__file__).resolve().parent.parent / "data" / "season.js"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cfb-playoff-predictor"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def fetch_conferences():
    d = get(f"{BASE}/v2/sports/football/college-football/standings?group=80&season={SEASON}")
    confs, members = [], {}
    for c in d["children"]:
        conf = {"id": c["id"], "name": c["name"], "abbr": c["abbreviation"], "divisions": []}
        groups = c.get("children") or [c]
        for g in groups:
            div = g["name"].split(" - ")[-1] if g is not c else None
            if div:
                conf["divisions"].append(div)
            for e in g.get("standings", {}).get("entries", []):
                members[e["team"]["id"]] = (c["id"], div)
        confs.append(conf)
    return confs, members


def fetch_week(week):
    url = (f"{BASE}/site/v2/sports/football/college-football/scoreboard"
           f"?groups=80&seasontype=2&week={week}&dates={SEASON}&limit=400")
    return get(url).get("events", [])


def main():
    confs, members = fetch_conferences()
    teams, games = {}, []
    for week in range(1, 16):
        for ev in fetch_week(week):
            comp = ev["competitions"][0]
            notes = " ".join(n.get("headline", "") for n in comp.get("notes", []))
            if "Championship" in notes:
                continue  # conference title games are built by the app
            side = {}
            for c in comp["competitors"]:
                t = c["team"]
                tid = t["id"]
                if tid in members and tid not in teams:
                    conf, div = members[tid]
                    teams[tid] = {
                        "id": tid, "abbr": t.get("abbreviation", ""), "name": t.get("location") or t.get("displayName"),
                        "mascot": t.get("name", ""), "color": t.get("color", "666666"),
                        "logo": t.get("logo", ""), "conf": conf, "div": div,
                    }
                side[c["homeAway"]] = {
                    "id": tid if tid in members else "FCS",
                    "label": t.get("location") or t.get("displayName"),
                    "score": int(c["score"]) if c.get("score") not in (None, "") else None,
                }
            state = ev["status"]["type"]["state"]
            done = ev["status"]["type"]["completed"]
            if ev["status"]["type"]["name"] in ("STATUS_CANCELED", "STATUS_POSTPONED"):
                continue
            g = {
                "id": ev["id"], "week": week, "date": ev["date"],
                "home": side["home"]["id"], "away": side["away"]["id"],
                "neutral": comp.get("neutralSite", False),
                "conf": comp.get("conferenceCompetition", False),
                "final": bool(done),
            }
            if "FCS" in (g["home"], g["away"]):
                g["fcsName"] = side["home"]["label"] if g["home"] == "FCS" else side["away"]["label"]
            if done:
                g["hs"], g["as"] = side["home"]["score"], side["away"]["score"]
            elif state == "in":
                g["live"] = True
            games.append(g)
        print(f"week {week}: {len(games)} games so far")

    data = {
        "season": SEASON,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "conferences": confs, "teams": list(teams.values()),
        "games": sorted(games, key=lambda g: g["date"]),
    }
    OUT.write_text("window.CFB_DATA = " + json.dumps(data, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote {OUT} - {len(teams)} teams, {len(games)} games, {sum(g['final'] for g in games)} final")


if __name__ == "__main__":
    main()
