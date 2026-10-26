# FPL Undervalued-Player Finder — Week 4

### Meeting Notes

Week 4 adds a comparison that considers points value, position value and recorded minutes together. The new script identifies players for whom no eligible alternative is at least as high on all three criteria and strictly higher on one. This produces a set of trade-off candidates without assigning arbitrary weights to a combined score. In the supplied midfield pool, fourteen of seventy-nine players remain in this set. A scatter plot shows the two value measures, with marker size representing minutes, while CSV exports record every player's status and an example alternative where applicable. Earlier rankings and minutes-threshold comparisons remain available. The approach makes competing criteria explicit, but it does not predict future points or establish that a player is undervalued. Comments and documentation explain the comparison rule.

### What changed since Week 3?

| Earlier work | Week 4 addition |
| --- | --- |
| Two separate value rankings | Both considered together with recorded minutes |
| Eligibility sensitivity at different minutes floors | Pairwise comparison within one eligible pool |
| Top-eight lists and rank matrix | A set of non-dominated candidates and a scatter plot |
| Individual scores and ranks | Dominator count and one example alternative per excluded candidate |

The new file is `compare_tradeoffs.py`. It retains the simple top-to-bottom script style and green/cream output palette. No model training, command-line parser or weighted score is introduced.

`find_players.py` prepares the starting shortlist and settings. The two later scripts analyse that saved run independently. Run the main script again after changing its settings, then rerun the comparison scripts so the outputs agree.

Defaults remain MID, price at most £6.5m, ownership at most 10%, at least 180 minutes, available status in the snapshot, and eight displayed leaders under the position ranking. Edit these values near the top of `find_players.py`. The Week 4 comparison always uses both value measures and minutes, regardless of which ranking is chosen for the earlier top-eight display.

For the meeting, open `results/tradeoff_comparison.png` and `results/tradeoff_frontier.csv`. Explain why Yalcouyé's high values and 236 recorded minutes represent a different trade-off from a candidate with more minutes. Then inspect a non-frontier row in `tradeoff_pool.csv`, find its `example_dominator_id`, and compare the three criteria. The numbers beside plotted names identify entries in the figure, not a final overall ranking.

`download_data.py` remains an optional network step. It replaces the saved dataset and metadata with a fresh API response. It was not run for Week 4. If needed can copy the current dataset first if the original demonstration must be preserved.

### Description of Files


- `compare_tradeoffs.py` : New three-criterion comparison and plot 
- `find_players.py` : Starting filters, both value scores and ranks 
- `check_minutes.py` : Week 3-style minutes-floor experiment 
- `download_data.py` : Optional source download and provenance metadata 
- `dataset/fpl_snapshot.json` : Supplied saved response 
- `dataset/fpl_snapshot.metadata.json` : Source attribution, timestamp, player count and checksum 
- `results/tradeoff_pool.csv` : All eligible players, dominance counts and example IDs 
- `results/tradeoff_frontier.csv` : Candidates not dominated on the chosen criteria 
- `results/tradeoff_comparison.png` : Two value axes and minutes-sized markers 
- `results/tradeoff_notes.txt` : Rule, source date and resulting set 
- `results/shortlist.csv`, `search_settings.json` : Starting pool and matching run settings
- `results/rank_comparison.csv`, `value_shortlist.png`, `ranking_comparison.png`, `search_notes.txt` : Earlier ranking outputs 
- `results/minutes_summary.csv`, `minutes_shortlists.csv`, `minutes_tracking.csv`, `minutes_comparison.png`, `minutes_notes.txt` : Earlier threshold-comparison outputs 
- `Explanation.txt` : Week 4 meeting paragraph 

All comparison files are under `results`, including abbreviated filenames in the table. Each script replaces its own output files and leaves the source dataset unchanged.

### Working Principle

Start from the existing eligible pool. 

- The main script converts FPL prices from tenths to millions, maps club/position IDs to labels, and converts numeric strings. Each filter must pass. Positive price and minutes avoid division by zero. Available status applies to the saved response and does not establish availability today.

- The points score remains `(total_points × 90 ÷ minutes) ÷ price`. The position score is `(selected total × 90 ÷ minutes) ÷ price`. For MID/FWD the total is expected goals plus expected assists; for DEF it is clean sheets, and for GK it is saves. The earlier ranks and threshold experiment remain available.

Recalculate the scores before comparison.

- `compare_tradeoffs.py` reads the full eligible shortlist and its settings. It recalculates the values from exported source-statistic columns rather than comparing the four-decimal value scores. The raw source columns used in the supplied snapshot retain sufficient precision for these formulas. Results are rounded only when written for viewing.

Define dominance explicitly.

- Candidate A dominates candidate B only when A has at least as high points value, at least as high position value and at least as many recorded minutes, with a strict advantage on one or more of those criteria. Equality across all three is not dominance. A row does not dominate itself.

- For example, hypothetical values A = `(1.0, 0.08, 400)` and B = `(0.9, 0.07, 350)` would make A dominate B. If B instead had 450 minutes, neither would dominate the other: B offers more recorded minutes while A offers better rates. This example explains the rule; it is not another player observation.

Apply the rule with readable operations.

- -`criteria.ge(row).all(axis=1)` finds alternatives that are no lower on every criterion. `criteria.gt(row).any(axis=1)` requires at least one strict advantage. Combining them identifies dominators. The script records their count and the lowest-ID example for a reproducible lookup. That example is not claimed to be the best replacement.

- Players with a zero dominator count form the *frontier*: the candidates not beaten under this precise rule. The default result is fourteen out of seventy-nine eligible midfielders. Increasing the number of criteria can retain more candidates, so this is not necessarily a small final recommendation list.

Why include minutes?
- A per-90 rate can be high in a limited sample. The Week 4 rule explicitly prefers more observed minutes when all other criteria are at least as good. Minutes are not another measure of scoring quality, nor a confidence interval. Their inclusion can keep a player whose two values are lower if that player has more recorded minutes. This does not prove future playing time or remove uncertainty.

Read the plot correctly.
- The x-axis shows points value and y-axis shows the position measure. Marker area is proportional to recorded minutes. Green markers are on the three-criterion frontier; grey markers are dominated. Because minutes are a third criterion, the green set is not simply a two-dimensional upper edge. The list is displayed in descending position-value order for convenience. It does not assign one overall score.

Retain the earlier calculations.
- `check_minutes.py` separately applies 180, 270 and 360-minute floors to the same saved ranking. It retains six and four of the initial top eight at the stricter cutoffs. This answers a different question from dominance: how a filter changes the eligible pool, rather than how candidates compare on several criteria at once.

### Data Source

Both dataset JSON files are unchanged from Week 3. Their metadata attributes the response to the public FPL bootstrap-static endpoint and records 667 players and a retrieval timestamp of 30 September 2026, 14:44:31 UTC. Its original collection process and historical accuracy were not independently audited in this update. No new player records or future performance were fabricated.

### Ongoing Work

The three selected criteria are prototype choices. They do not capture fixture difficulty, future starts, all defensive contributions or subsequent results. The frontier changes when filters, indicators or the snapshot change. A dominated player may be attractive on an omitted criterion. The output is a screening aid, not a prediction or proof of a bargain. All seventy-nine dominance counts and example IDs were checked independently against the supplied JSON statistics. The resulting fourteen-member set and chart were reviewed.