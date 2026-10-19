# Playoff Picture 2026

Pick the rest of the 2026 college football season and see what it does to conference standings, title games, the committee's rankings and the 12-team playoff bracket.

Open `index.html` in a browser. It has no build step and needs no server.

## What it does

- **Pick games.** Every FBS game, week by week. Completed games are locked with their real scores. Tap a team to pick it. Any game you don't pick goes to the favorite.
- **Standings.** Projected final conference standings from the real results, your picks and the favorites.
- **Title games.** Conference championship matchups come from your standings. Pick the winners.
- **Rankings.** A stand-in for the selection committee that blends a résumé score (strength of record) with a power rating. A slider controls how much weight each one gets.
- **Playoff.** The 12-team field: the five highest-ranked conference champions plus seven at-large teams, seeded straight by ranking. Seeds 1–4 get byes. Pick your way to a national champion.
- **Odds.** 2,000 simulated seasons that keep your picks fixed. Shows each team's chances of reaching its title game, winning its conference, making the playoff, earning a bye and winning it all.

Picks are saved in your browser.

## The model

- **Win probability:** from [ESPN FPI](https://www.espn.com/college-football/fpi), [Sagarin's PREDICTOR](http://sagarin.com/sports/cfsend.htm), or an average of the two (the default). Pick the source in the app. The spread is the rating difference plus home field (Sagarin's published edge, about 3.8 points; 2.5 points for FPI, an estimate). Win chance is a normal distribution around that spread with a 14-point standard deviation. Sagarin also rates FCS teams, so FCS opponents get real ratings.
- **Résumé:** for each game, a win minus the chance a typical playoff team (the #12 rated team) would win the same game.
- **Committee ranking:** a blend of résumé and rating, with a small bonus for conference champions. With head-to-head on, a team that beat a higher-ranked team moves directly ahead of it when it has the same or fewer losses and the two are comparable. Three-way loops cancel out.
- **Conference tiebreakers:** head-to-head among the tied teams, then rating. Each conference's real rules are more detailed.

## Updating the data

```
python scripts/fetch_data.py
```

This pulls the schedule, scores, conference lineups and FPI from ESPN, plus Sagarin's ratings, and rewrites `data/season.js`. The GitHub Action in `.github/workflows/update-data.yml` does this every morning and commits the new data.

## Hosting on GitHub Pages

Push the repo to GitHub, then go to **Settings → Pages** and choose **Deploy from a branch**, using `main` and `/ (root)`.
