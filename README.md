# Playoff Picture 2026

Pick the rest of the 2026 college football season and see what it does to conference standings, title games, the committee's rankings and the 12-team playoff bracket.

Open `index.html` in a browser. It has no build step and needs no server.

## What it does

- **Pick games.** Every FBS game, week by week. Completed games are locked with their real scores. Tap a team to pick it. Any game you don't pick goes to the favorite.
- **Standings.** Projected final conference standings from the real results, your picks and the favorites, with a note on how each tie was broken.
- **Team schedules.** Click any team in Standings, Rankings or Odds to see its full schedule and change its games.
- **Title games.** Conference championship matchups come from your standings. Pick the winners.
- **Rankings.** A stand-in for the selection committee that blends a résumé score (strength of record) with a power rating. A slider controls how much weight each one gets.
- **Playoff.** The 12-team field: the five highest-ranked conference champions plus seven at-large teams, seeded straight by ranking. Seeds 1–4 get byes. Pick your way to a national champion.
- **Big games.** Pick a team and see the 25 or 50 open games that swing its playoff or first-round-bye chances the most, its own games and everyone else's, with its chances if each side wins. Every game card also shows each team's playoff chance with a win and with a loss.
- **Simulator.** Play the rest of the season one week at a time or all at once. Each game is a weighted coin flip on its win chance, so a 50/50 game goes either way equally often. Re-roll as often as you like; your own picks stay locked. Each run shows the upsets versus how many were expected, plus a fairness check that replays every game 2,000 times.
- **Odds.** 4,000 simulated seasons that keep your picks fixed. Shows each team's chances of reaching its title game, winning its conference, making the playoff, earning a bye and winning it all.

Picks are saved in your browser.

## The model

- **Win probability:** from [ESPN FPI](https://www.espn.com/college-football/fpi), [Sagarin's PREDICTOR](http://sagarin.com/sports/cfsend.htm), or an average of the two (the default). Pick the source in the app. The spread is the rating difference plus home field (Sagarin's published edge, about 3.8 points; 2.5 points for FPI, an estimate). Win chance is a normal distribution around that spread with a 14-point standard deviation. Sagarin also rates FCS teams, so FCS opponents get real ratings.
- **Résumé:** for each game, a win minus the chance a typical playoff team (the #12 rated team) would win the same game.
- **Committee ranking:** a blend of résumé and rating, with a small bonus for conference champions. With head-to-head on, a team that beat a higher-ranked team moves directly ahead of it when it has the same or fewer losses and the two are comparable. Three-way loops cancel out.
- **Conference tiebreakers:** head-to-head, record vs. common opponents, record vs. the best common opponent, opponents' combined conference win %, then team rating. When a step splits a multi-team tie, each smaller group starts over at step 1. The Standings tab lists the steps and shows which one settled each tie. Each conference's official procedure has more detail.

## Updating the data

```
python scripts/fetch_data.py
```

This pulls the schedule, scores, conference lineups and FPI from ESPN, plus Sagarin's ratings, and rewrites `data/season.js`. The GitHub Action in `.github/workflows/update-data.yml` does this every morning and commits the new data.

## Hosting on GitHub Pages

Push the repo to GitHub, then go to **Settings → Pages** and choose **Deploy from a branch**, using `main` and `/ (root)`.
