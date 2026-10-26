# Compare the saved shortlist under several minimum-minutes rules.
import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Run find_players.py first. Its settings and scores define the starting pool.
folder = Path(__file__).resolve().parent
results = folder / "results"
settings = json.loads((results / "search_settings.json").read_text(encoding="utf-8"))
players = pd.read_csv(results / "shortlist.csv")
rank_column = "position_rank" if settings["ranking"] == "position" else "points_rank"
players = players.sort_values(rank_column)
top_n = settings["top_n"]
baseline = players.head(top_n)

# These cutoffs fit the included snapshot, whose maximum minutes is 450.
# Do not use a cutoff below the original filter: those players are absent from the CSV.
minutes_to_compare = [180, 270, 360]
thresholds = sorted(set([settings["min_minutes"]] + [
    n for n in minutes_to_compare if n >= settings["min_minutes"]]))

summaries = []
all_top = []
rank_maps = {}
for minimum in thresholds:
    eligible = players[players["minutes"] >= minimum].copy()
    # Filtering preserves score order. Consecutive ranks refer to the smaller pool.
    # Reuse saved ranks rather than ranking rounded CSV scores and changing ties.
    eligible["filtered_rank"] = range(1, len(eligible) + 1)
    leaders = eligible.head(top_n).copy()
    leaders.insert(0, "minimum_minutes", minimum)
    all_top.append(leaders)
    rank_maps[minimum] = eligible.set_index("id")["filtered_rank"]
    retained = baseline.id.isin(leaders.id).sum()
    summaries.append({"minimum_minutes": minimum, "eligible_players": len(eligible),
                      "shown_players": len(leaders), "baseline_top_retained": int(retained),
                      "new_top_entries": int((~leaders.id.isin(baseline.id)).sum())})

# Track every original top player, including players excluded by a stricter cutoff.
tracking = baseline[["id", "player", "club", "minutes"]].copy()
for minimum in thresholds:
    tracking[f"rank_at_{minimum}"] = tracking.id.map(rank_maps[minimum]).astype("Int64")
summary = pd.DataFrame(summaries)
summary.to_csv(results / "minutes_summary.csv", index=False)
pd.concat(all_top, ignore_index=True).to_csv(results / "minutes_shortlists.csv", index=False)
tracking.to_csv(results / "minutes_tracking.csv", index=False)

# A compact matrix shows the original shortlist's rank or exclusion at each cutoff.
# Grey means no longer eligible; it is not a score of zero.
plt.rcParams.update({"axes.titlesize": 14, "axes.titleweight": "bold",
                     "axes.labelsize": 12, "axes.labelweight": "bold"})
fig, ax = plt.subplots(figsize=(10, 6.5), facecolor="#f5f1e8")
ax.set_facecolor("#f5f1e8")
for row, record in enumerate(tracking.to_dict("records")):
    for col, minimum in enumerate(thresholds):
        rank = record[f"rank_at_{minimum}"]
        missing = pd.isna(rank)
        colour = "#ded9cc" if missing else "#d3e4d7"
        ax.add_patch(plt.Rectangle((col - 0.46, row - 0.40), 0.92, 0.8, color=colour))
        ax.text(col, row, "out" if missing else str(int(rank)), ha="center", va="center",
                fontsize=12, color="#6c6558" if missing else "#285440")
ax.set_xlim(-0.5, len(thresholds) - 0.5)
ax.set_ylim(max(len(tracking) - 0.5, 0.5), -0.5)
ax.set_xticks(range(len(thresholds)), [f"{n}+ min\n{len(rank_maps[n])} eligible" for n in thresholds])
ax.set_yticks(range(len(tracking)), tracking.player + " (" + tracking.club + ") / " + tracking.minutes.astype(str) + " min")
ax.tick_params(length=0, pad=12)
ax.spines[:].set_visible(False)
ax.set_title(f"{settings['position']} shortlist / raising the minutes floor", loc="left", pad=20)
ax.set_xlabel("Minimum minutes in the same saved snapshot", labelpad=15)
if tracking.empty:
    ax.text(0.5, 0.5, "No players match the starting filters", transform=ax.transAxes, ha="center")
fig.text(0.04, 0.04, f"Original top {len(baseline)} under {settings['ranking']} ranking · numbers are ranks in each eligible pool\n"
         f"out = below the minutes cutoff · snapshot {settings['snapshot_saved'][:10]} · not a forecast", fontsize=9)
fig.tight_layout(rect=(0.02, 0.12, 0.98, 0.98))
fig.savefig(results / "minutes_comparison.png", dpi=300)
plt.close(fig)

# Keep the experiment's settings beside the results so the comparison is traceable.
report = (f"FPL WEEK 4 / MINUTES SENSITIVITY\n"
          f"Snapshot: {settings['snapshot_saved']}\n"
          f"Position: {settings['position']}; ranking: {settings['ranking']}; top_n: {top_n}\n"
          f"Price <= {settings['max_price']}m; ownership <= {settings['max_ownership']}%; status=a\n\n"
          + summary.to_string(index=False) + "\n\nOriginal shortlist tracking:\n"
          + tracking.to_string(index=False) + "\n\n"
          "Only the eligibility cutoff changes. Scores and source statistics remain fixed.\n"
          "Blank ranks in the CSV / <NA> here mean the player does not qualify at that cutoff.\n"
          "The matrix tracks the original top players; minutes_shortlists.csv includes replacement names.\n"
          "Retention is agreement between settings, not evidence of future scoring accuracy.\n")
(results / "minutes_notes.txt").write_text(report, encoding="utf-8")
print(report)
