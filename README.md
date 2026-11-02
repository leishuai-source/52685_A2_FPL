# FPL Player Value Finder

A Python tool for shortlisting Fantasy Premier League players by position, price, ownership and minutes. It compares two value rankings, checks stricter minutes requirements, and produces an HTML report with four charts.

## Run

Use Python 3.12. From the project folder:

```bash
python -m venv .venv
```

For Windows, use `.venv\Scripts\activate` to activate python environment. 

For macOS use `source .venv/bin/activate`

Then run this:

```bash
python -m pip install -r requirements.txt
python run_finder.py
```

Open **`results/review.html`** in a browser. After package installation, the analysis runs offline using the saved snapshot. Keep the report inside `results/` so its charts and links work.

## Preferences

Edit `preferences.json`, then rerun `python run_finder.py`:

```json
{
  "position": "FWD",
  "ranking": "points",
  "max_price": 8.5,
  "max_ownership": 10,
  "min_minutes": 250,
  "top_n": 15
}
```

- Positions: `GK`, `DEF`, `MID`, `FWD`. Rankings: `points` or `position`.
- Price is in £ millions; ownership is a percentage; minutes are recorded playing time.
- `top_n` sets the display limit from 1 to 15. All eligible players remain in `shortlist.csv`.
- Only players marked available in the snapshot are included. Rerunning replaces the generated results.

## Scripts

| File | Purpose |
| --- | --- |
| `run_finder.py` | Checks preferences and the snapshot checksum, then runs the complete workflow. |
| `find_players.py` | Filters players, calculates both value rankings and saves the first two charts. |
| `check_minutes.py` | Compares the chosen minutes floor with floors 90 and 180 minutes higher. |
| `compare_tradeoffs.py` | Compares both value scores and recorded minutes together. |
| `make_report.py` | Combines the saved tables and charts into the HTML report. |
| `download_data.py` | Downloads a fresh snapshot and source metadata. |

Both value scores use **statistic × 90 ÷ minutes ÷ price**. Points value uses total FPL points. Position value uses expected goals plus expected assists for MID/FWD, clean sheets for DEF, and saves for GK.

The trade-off set contains players for whom no alternative is at least as high on both scores and minutes, with a strict advantage on one. It is a candidate set rather than an overall ranking.

## Data and results

Source: [public FPL API](https://fantasy.premierleague.com/api/bootstrap-static/). The included metadata records **2 November 2026, 00:33:13 UTC**, **670 players** and **gameweek 9**.

The current settings produce **14 eligible forwards** and **8 trade-off candidates**. Minutes floors of **250, 340 and 430** leave **14, 12 and 11** players. Although `top_n` is 15, only 14 players qualify.

`dataset/` holds the snapshot and metadata. `results/` contains the report, four PNG charts, CSV tables, explanatory notes and `search_settings.json`.

## Get the latest data (optional)

The included results were regenerated after updating the snapshot. To analyse newer data yourself, run these commands in order:

```bash
python download_data.py
python run_finder.py
```

`download_data.py` fetches the current API response and overwrites both snapshot files. `run_finder.py` then applies your preferences and rebuilds all tables, charts and the report. Downloading requires internet access; results may change as FPL statistics change.

## To Note

These comparisons describe one saved data snapshot. High per-90 values can reflect limited playing time, and recorded minutes do not guarantee future starts. The tool supports player screening but it does not predict future points or prove that a player is undervalued.
