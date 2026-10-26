# Week 4: find players not beaten on both value measures and recorded minutes.
import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

folder = Path(__file__).resolve().parent
results = folder / "results"
settings = json.loads((results / "search_settings.json").read_text())
players = pd.read_csv(results / "shortlist.csv").sort_values("id").reset_index(drop=True)

# Recalculate from source columns, rather than comparing rounded exported value scores.
players["points_value"] = players.total_points * 90 / players.minutes / players.price
if settings["position"] in ["MID", "FWD"]:
    total = players.expected_goals + players.expected_assists
elif settings["position"] == "DEF":
    total = players.clean_sheets
else:
    total = players.saves
players["position_value"] = total * 90 / players.minutes / players.price

# Higher values are preferred on these three explicit prototype criteria.
# More minutes is a sample-size preference, not another performance score.
criteria = players[["points_value", "position_value", "minutes"]]
counts, examples = [], []
for index, row in criteria.iterrows():
    at_least_as_high = criteria.ge(row).all(axis=1)
    strictly_higher = criteria.gt(row).any(axis=1)
    better = players[at_least_as_high & strictly_higher]
    counts.append(len(better))
    # Show one concrete comparison, using the lowest ID for a consistent example.
    examples.append(int(better.iloc[0].id) if len(better) else None)
players["dominator_count"] = counts
players["example_dominator_id"] = pd.array(examples, dtype="Int64")
players["frontier"] = players.dominator_count == 0
frontier = players[players.frontier].sort_values("position_value", ascending=False)

# Keep the full pool as evidence, not just the highlighted names.
columns = ["id", "player", "club", "minutes", "price", "points_value", "position_value",
           "dominator_count", "example_dominator_id", "frontier"]
players[columns].round(6).to_csv(results / "tradeoff_pool.csv", index=False)
frontier[columns].round(6).to_csv(results / "tradeoff_frontier.csv", index=False)
text = (f"FPL WEEK 4 / THREE-CRITERION COMPARISON\nPosition: {settings['position']}\n"
        f"Snapshot: {settings['snapshot_saved']}\nEligible: {len(players)}; frontier: {len(frontier)}\n\n"
        + frontier[columns].round(4).to_string(index=False) + "\n\n"
        "A dominates B only if A is at least as high on both values and minutes, and strictly higher on at least one.\n"
        "Exactly tied players do not dominate each other. The frontier is a set, not a final ranking.\n"
        "Minutes favour a larger observed sample; they do not establish future playing time or statistical certainty.\n"
        "The two plot axes show values; marker area shows minutes. No weighted score or prediction is used.\n")
(results / "tradeoff_notes.txt").write_text(text, encoding="utf-8")
print(text)

# A third criterion can keep a lower-value player on the frontier if they have more minutes.
plt.rcParams.update({"axes.titlesize": 14, "axes.titleweight": "bold", "axes.labelsize": 12, "axes.labelweight": "bold"})
fig, ax = plt.subplots(figsize=(11, 7), facecolor="#f5f1e8")
ax.set_facecolor("#f5f1e8")
other = players[~players.frontier]
ax.scatter(other.points_value, other.position_value, s=other.minutes * 0.4, color="#c9c0ad", alpha=0.55, label="Dominated on the three criteria")
ax.scatter(frontier.points_value, frontier.position_value, s=frontier.minutes * 0.4,
           color="#285440", edgecolor="white", linewidth=0.8, label="Three-criterion frontier")
# Numbered labels stay compact; the matching names are listed beside the plot.
for number, row in enumerate(frontier.itertuples(), 1):
    ax.annotate(str(number), (row.points_value, row.position_value), xytext=(6, 7), textcoords="offset points", fontsize=9)
listing = "FRONTIER / recorded minutes\n\n" + "\n".join(
    f"{i}. {r.player} ({r.club}) / {r.minutes}" for i, r in enumerate(frontier.itertuples(), 1))
fig.text(0.70, 0.82, listing if len(frontier) else "No eligible players", va="top", fontsize=10, linespacing=1.5)
ax.set(title=f"{settings['position']} / value and minutes trade-offs", xlabel="Points per 90 per £1m", ylabel="Position measure per 90 per £1m")
ax.set_xlim(left=0); ax.set_ylim(bottom=0); ax.margins(0.15)
ax.grid(color="#ded9cc", linestyle=":");ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="upper left", fontsize=9, frameon=False)
fig.text(0.06, 0.04, f"Same {len(players)} eligible players as the saved shortlist | snapshot {settings['snapshot_saved'][:10]}\nMarker area is proportional to minutes; frontier membership is not a future-points forecast.", fontsize=9)
fig.tight_layout(rect=(0.02, 0.12, 0.69, 0.98))
fig.savefig(results / "tradeoff_comparison.png", dpi=300)
plt.close(fig)
