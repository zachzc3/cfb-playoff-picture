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

- **Power rating:** an SRS-style margin-of-victory rating from completed games. Margins are capped at 24, home field is worth 2.5 points, and all FCS opponents are pooled into one team.
- **Win probability:** normal distribution on the rating difference, with SD 13.5 points.
- **Résumé:** for each game, a win minus the chance a typical playoff team (the #12 power team) would win the same game.
- **Conference tiebreakers:** head-to-head among the tied teams, then power rating. Each conference's real rules are more detailed.

## Updating the data

```
python scripts/fetch_data.py
```

This pulls the schedule, scores and conference lineups from ESPN's public scoreboard API and rewrites `data/season.js`. The GitHub Action in `.github/workflows/update-data.yml` does this every morning and commits the new data.

## Hosting on GitHub Pages

Push the repo to GitHub, then go to **Settings → Pages** and choose **Deploy from a branch**, using `main` and `/ (root)`.
