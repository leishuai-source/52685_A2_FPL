import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# Keep the Week 1 limits so the effect of the new measure can be compared fairly.
# Choose GK, DEF, MID or FWD. Ranking can be "points" or "position".
position = "MID"
ranking = "position"
max_price = 6.5
max_ownership = 10
min_minutes = 180
top_n = 8

# Read the saved response and its source date; running this file needs no API call.
folder = Path(__file__).resolve().parent
snapshot = json.loads((folder / "dataset/fpl_snapshot.json").read_text(encoding="utf-8"))
metadata = json.loads((folder / "dataset/fpl_snapshot.metadata.json").read_text(encoding="utf-8"))
players = pd.DataFrame(snapshot["elements"])
players = players[["id", "web_name", "team", "element_type", "now_cost", "selected_by_percent",
                   "minutes", "total_points", "status", "expected_goals", "expected_assists",
                   "clean_sheets", "saves"]].copy()
players = players.rename(columns={"web_name": "player", "selected_by_percent": "ownership"})

# Map numeric team and position codes to readable labels. FPL stores prices in tenths.
teams = {team["id"]: team["short_name"] for team in snapshot["teams"]}
players["club"] = players["team"].map(teams)
players["position"] = players["element_type"].map({1: "GK", 2: "DEF", 3: "MID", 4: "FWD"})
players["price"] = players["now_cost"] / 10
# These API fields are strings; convert them before arithmetic or numeric comparisons.
for column in ["ownership", "expected_goals", "expected_assists"]:
    players[column] = players[column].astype(float)

# Each condition must be true. Positive minutes and price also protect the divisions below.
# Status "a" means available in this saved response, not necessarily available today.
shortlist = players[(players["position"] == position)
                    & (players["price"] <= max_price) & (players["price"] > 0)
                    & (players["ownership"] <= max_ownership)
                    & (players["minutes"] >= min_minutes) & (players["minutes"] > 0)
                    & (players["status"] == "a")].copy()

# Retain the Week 1 score as a baseline: output per 90 minutes, divided by price.
shortlist["points_per_90"] = shortlist["total_points"] * 90 / shortlist["minutes"]
shortlist["points_value"] = shortlist["points_per_90"] / shortlist["price"]

# New in Week 2: use a supporting measure suited to the selected position.
# MID/FWD use expected goal involvement. DEF use clean sheets. GK use saves.
# These are simple exploratory indicators; they do not capture every part of a role.
if position in ["MID", "FWD"]:
    total = shortlist["expected_goals"] + shortlist["expected_assists"]
    measure = "Expected goal involvement"
    unit = "(xG + xA) per 90 per £1m"
elif position == "DEF":
    total = shortlist["clean_sheets"]
    measure = "Clean sheets"
    unit = "Clean sheets per 90 per £1m"
else:
    total = shortlist["saves"]
    measure = "Goalkeeper saves"
    unit = "Saves per 90 per £1m"
shortlist["position_per_90"] = total * 90 / shortlist["minutes"]
shortlist["position_value"] = shortlist["position_per_90"] / shortlist["price"]
shortlist["measure"] = measure

# Rank the same eligible players twice. Sorting IDs first provides a consistent tie order.
shortlist = shortlist.sort_values("id")
shortlist["points_rank"] = shortlist["points_value"].rank(ascending=False, method="first").astype(int)
shortlist["position_rank"] = shortlist["position_value"].rank(ascending=False, method="first").astype(int)
# Positive movement means a better numerical rank under the position measure.
# This is a comparison of methods on one snapshot, not a change between gameweeks.
shortlist["rank_improvement"] = shortlist["points_rank"] - shortlist["position_rank"]
score_column = "position_value" if ranking == "position" else "points_value"
rank_column = "position_rank" if ranking == "position" else "points_rank"
axis_label = unit if ranking == "position" else "Points per 90 per £1m"
shortlist = shortlist.sort_values(rank_column)
top = shortlist.head(top_n)

# Save both scores and ranks, so each displayed result can be traced to its inputs.
results = folder / "results"
results.mkdir(exist_ok=True)
# Week 3 records the run settings so check_minutes.py uses the same ranking and pool.
settings = {"position": position, "ranking": ranking, "max_price": max_price,
            "max_ownership": max_ownership, "min_minutes": min_minutes, "top_n": top_n,
            "snapshot_saved": metadata["retrieved_utc"]}
(results / "search_settings.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
columns = ["id", "player", "club", "position", "price", "ownership", "minutes", "total_points",
           "expected_goals", "expected_assists", "clean_sheets", "saves", "points_per_90",
           "points_value", "measure", "position_per_90", "position_value", "points_rank",
           "position_rank", "rank_improvement"]
shortlist[columns].round(4).to_csv(results / "shortlist.csv", index=False)
comparison = shortlist[["player", "club", "points_rank", "position_rank", "rank_improvement"]]
comparison.to_csv(results / "rank_comparison.csv", index=False)
report = (f"FPL WEEK 4: {position}; ranking = {ranking}\n"
          f"Snapshot saved: {metadata['retrieved_utc']}\n"
          f"Input players: {len(players)}; eligible: {len(shortlist)}; showing: {len(top)}\n"
          f"Filters: price <= {max_price}m; ownership <= {max_ownership}%; minutes >= {min_minutes}; status=a\n"
          f"Position measure: {measure}. Both scores are per 90 minutes divided by price.\n\n"
          + comparison.head(top_n).to_string(index=False)
          + "\n\nRank improvement = points rank - position rank. Positive means better position rank.\n"
          "Both rankings use the same snapshot and eligible pool. These are not gameweek changes or predictions.\n")
(results / "search_notes.txt").write_text(report, encoding="utf-8")
print(report)

# Keep the Week 1 dot-chart style, with units matching the chosen ranking method.
plt.rcParams.update({"axes.titlesize": 14, "axes.titleweight": "bold",
                     "axes.labelsize": 12, "axes.labelweight": "bold"})
fig, ax = plt.subplots(figsize=(10, 6.5), facecolor="#f5f1e8")
ax.set_facecolor("#f5f1e8")
rows = range(len(top))
labels = top["player"] + "  (" + top["club"] + ")"
ax.scatter(top[score_column], rows, s=100, color="#285440", zorder=3)
ax.set_yticks(list(rows), labels, fontsize=11)
ax.invert_yaxis()
ax.margins(x=0.25, y=0.12)
for row, value in enumerate(top[score_column]):
    ax.annotate(f"{value:.3f}", (value, row), xytext=(10, 0), textcoords="offset points", va="center")
ax.set_title(f"FPL / {position} / {ranking} value", loc="left", pad=20)
ax.set_xlabel(axis_label, labelpad=14)
ax.grid(axis="x", color="#ded9cc", linestyle=":")
ax.set_axisbelow(True)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, pad=12)
fig.text(0.04, 0.04, f"Saved snapshot {metadata['retrieved_utc'][:10]} · {len(shortlist)} eligible · {len(top)} shown\n"
         f"Price ≤ £{max_price}m · ownership ≤ {max_ownership}% · minutes ≥ {min_minutes}", fontsize=9)
fig.tight_layout(rect=(0.02, 0.12, 0.98, 0.98))
fig.savefig(results / "value_shortlist.png", dpi=300)
plt.close(fig)

# New comparison chart: joined dots show how the two methods rank these same players.
fig, ax = plt.subplots(figsize=(10, 6.5), facecolor="#f5f1e8")
ax.set_facecolor("#f5f1e8")
ax.hlines(list(rows), top["points_rank"], top["position_rank"], color="#c9c0ad", linewidth=2)
ax.scatter(top["points_rank"], rows, color="#ae792d", s=85, label="Points value", zorder=3)
ax.scatter(top["position_rank"], rows, color="#285440", s=65, label="Position value", zorder=4)
ax.set_yticks(list(rows), labels, fontsize=11)
ax.invert_yaxis()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
ax.set_xlim(0, max(2, top[["points_rank", "position_rank"]].max().max() + 2) if len(top) else 2)
ax.set_title(f"Same {position} players, two ranking methods", loc="left", pad=20)
ax.set_xlabel("Rank within the eligible position group (1 = highest)", labelpad=14)
ax.spines[["top", "right", "left"]].set_visible(False)
ax.grid(axis="x", color="#ded9cc", linestyle=":")
ax.set_axisbelow(True)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False)
fig.text(0.04, 0.025, f"Top {len(top)} under {ranking} ranking · {measure} supports the position ranking\n"
         "Rank differences reflect the scoring method, not changes over time.", fontsize=9)
fig.tight_layout(rect=(0.02, 0.10, 0.98, 0.98))
fig.savefig(results / "ranking_comparison.png", dpi=300)
plt.close(fig)
