"""Pull the FBS schedule, results and conference lineups from ESPN's public API.

Writes data/season.js (window.CFB_DATA = {...}) so index.html works offline.
Usage: python scripts/fetch_data.py [season]
"""
import html
import json
import re
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


SAGARIN_URL = "http://sagarin.com/sports/cfsend.htm"
# ESPN location name -> Sagarin name, where a simple normalization doesn't match them up
SAGARIN_ALIAS = {
    "USC": "Southern California", "San José State": "San Jose State", "UCF": "Central Florida(UCF)",
    "Miami": "Miami-Florida", "UConn": "Connecticut", "Army": "Army West Point", "Miami (OH)": "Miami-Ohio",
    "App State": "Appalachian State", "Florida International": "Fla. International",
    "Sam Houston": "Sam Houston State", "UL Monroe": "LouisianaMonroe(ULM)", "Louisiana": "Louisiana-Lafayette",
    "Ole Miss": "Mississippi",
}


def norm(name):
    return re.sub(r"[^a-z0-9]", "", name.lower().replace("state", "st").replace("&", ""))


def fetch_sagarin():
    """Sagarin PREDICTOR ratings (FBS and FCS) plus its home-field edge."""
    req = urllib.request.Request(SAGARIN_URL, headers={"User-Agent": "cfb-playoff-predictor"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = re.sub(r"<[^>]+>", "", r.read().decode("latin-1"))
    hfa = float(re.search(r"HOME ADVANTAGE=\[\s*[\d.]+\]\s+\[\s*([\d.]+)\]", text).group(1))
    row = re.compile(r"^\s*\d+\s+(.+?)\s+(AA|A)\s+=\s+[\d.]+\s+\d+\s+\d+\s+[\d.]+\(\s*\d+\)\s+\d+\s+\d+\s+\|"
                     r"\s+\d+\s+\d+\s+\|\s+([\d.]+)", re.M)
    ratings = {}
    for m in row.finditer(text):
        ratings.setdefault(html.unescape(m.group(1)).strip(), float(m.group(3)))
    stamp = re.search(r"through games of ([^\n-]+)", text)
    return hfa, ratings, stamp.group(1).strip() if stamp else ""


def sagarin_lookup(ratings, name):
    by_norm = {norm(k): v for k, v in ratings.items()}
    if name in SAGARIN_ALIAS:
        return ratings.get(SAGARIN_ALIAS[name])
    return by_norm.get(norm(name))


def fetch_fpi():
    d = get(f"https://site.web.api.espn.com/apis/fitt/v3/sports/football/college-football/powerindex"
            f"?region=us&lang=en&season={SEASON}&limit=200")
    names = next(c for c in d["categories"] if c["name"] == "fpi")["names"]
    out = {}
    for t in d["teams"]:
        cat = next(c for c in t["categories"] if c["name"] == "fpi")
        v = dict(zip(names, cat["values"]))
        out[t["team"]["id"]] = {
            "fpi": round(v["fpi"], 2),
            # ESPN's own season simulations, as percentages
            "espn": {k: round(v[k], 1) for k in ("probmakeplayoffs", "probwinconf", "probwinout", "probwintitle") if k in v}
                    | {"projW": round(v.get("projectedw", 0), 1), "projL": round(v.get("projectedl", 0), 1)},
        }
    return out


def fetch_polls():
    """AP poll now; the CFP committee rankings once they're released (ESPN lists them in the same feed)."""
    d = get(f"{BASE}/site/v2/sports/football/college-football/rankings")
    polls = {}
    for r in d.get("rankings", []):
        name, kind = r.get("name", ""), r.get("type", "")
        key = "cfp" if kind == "cfp" or "Playoff" in name else "ap" if kind == "ap" else None
        if key:
            polls[key] = {"name": name, "headline": r.get("headline", ""), "date": r.get("date", ""),
                          "ranks": {x["team"]["id"]: x["current"] for x in r.get("ranks", [])}}
    return polls


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
                g["ls"] = [side["home"]["score"], side["away"]["score"]]
            games.append(g)
        print(f"week {week}: {len(games)} games so far")

    fpi = fetch_fpi()
    sag_hfa, sag, sag_through = fetch_sagarin()
    missing = []
    for t in teams.values():
        f = fpi.get(t["id"]) or {}
        t["fpi"] = f.get("fpi")
        if f.get("espn"):
            t["espn"] = f["espn"]
        t["sag"] = sagarin_lookup(sag, t["name"])
        if t["fpi"] is None or t["sag"] is None:
            missing.append(t["name"])
    for g in games:
        if "fcsName" in g:
            v = sagarin_lookup(sag, g["fcsName"])
            if v is not None:
                g["fcsSag"] = v
    if missing:
        print("WARNING: no FPI or Sagarin rating for", missing)

    data = {
        "season": SEASON,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "ratings": {"sagHfa": sag_hfa, "fpiHfa": 2.5, "sagThrough": sag_through},
        "polls": fetch_polls(),
        "conferences": confs, "teams": list(teams.values()),
        "games": sorted(games, key=lambda g: g["date"]),
    }
    text = "window.CFB_DATA = " + json.dumps(data, separators=(",", ":")) + ";\n"
    # Skip the write when only the timestamp changed, so frequent runs don't make empty commits
    if OUT.exists():
        strip = lambda t: re.sub(r'"updated":"[^"]*"', "", t)
        if strip(OUT.read_text(encoding="utf-8")) == strip(text):
            print("no changes")
            return
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} - {len(teams)} teams, {len(games)} games, {sum(g['final'] for g in games)} final")


if __name__ == "__main__":
    main()
