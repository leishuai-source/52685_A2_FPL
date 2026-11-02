# Collect the saved tables and plots into a local, shareable review page.
from pathlib import Path
from html import escape
import json
import pandas as pd

folder = Path(__file__).resolve().parent
results = folder / 'results'
settings = json.loads((results / 'search_settings.json').read_text())
players = pd.read_csv(results / 'shortlist.csv')
minutes = pd.read_csv(results / 'minutes_summary.csv')
frontier = pd.read_csv(results / 'tradeoff_frontier.csv')
columns = ['player', 'club', 'price', 'ownership', 'minutes', 'points_rank', 'position_rank']
# pandas escapes cell text; html.escape protects settings inserted into page text.
shortlist = players.head(settings['top_n'])[columns].to_html(index=False, border=0)
page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FPL shortlist review</title><style>
body{max-width:1080px;margin:40px auto;padding:0 24px;background:#f5f1e8;color:#233c2d;font:17px/1.6 Georgia,serif}
h1{font-size:40px;line-height:1.15}h2{margin-top:40px}img{max-width:100%;height:auto}
table{border-collapse:collapse;width:100%;font:14px/1.6 Arial,sans-serif}th,td{border-bottom:1px solid #ccc5b6;padding:9px;text-align:left}
.note{background:#e5dfd1;padding:18px;border-left:4px solid #ae792d}.scroll{overflow:auto}
a{color:#285440}code{font-size:14px}</style><body>
<p> FPL PLAYER VALUE STUDY</p><h1>Transfer Recommendation in Fantasy Premier League 2026-2027</h1>
'''
page += '<p class="note">' + escape(settings['data_note']) + '. Run download_data.py to update the dataset to current date.</p>'
page += '<p>' + escape(f"{settings['position']} · {settings['ranking']} ranking · price ≤ £{settings['max_price']}m · ownership ≤ {settings['max_ownership']}% · minutes ≥ {settings['min_minutes']}") + '</p>'
# page += '<p>' + escape(f"Inherited snapshot timestamp: {settings['snapshot_saved']}.      Eligible players: {len(players)}.      Frontier members: {len(frontier)}.") + '</p>'
page += '<p style="white-space: pre-wrap;">' + escape(f"Inherited snapshot timestamp: {settings['snapshot_saved']}.\tEligible players: {len(players)}.\tFrontier members: {len(frontier)}.") + '</p>'
page += '<h2>1 / The shortlist</h2><div class="scroll">' + shortlist + '</div>'
if players.empty:
    page += '<p>No players match. Loosen a limit in preferences.json and rerun the workflow.</p>'
for title, image, explanation in [
    ('Value per price', 'value_shortlist.png', 'Each indicator is divided by minutes, multiplied by 90, then divided by price.'),
    ('Two ranking methods', 'ranking_comparison.png', 'Positive rank improvement means a better position-based rank. Both use one snapshot; this is not change over time.'),
    ('Raise the minutes floor', 'minutes_comparison.png', 'Scores stay fixed. Only eligibility changes; out means excluded, not a score of zero.'),
    ('Value and recorded minutes', 'tradeoff_comparison.png', 'A player is dominated only if another is at least as high on all three criteria and strictly higher on one. The frontier is a set, not a forecast.')]:
    page += '<h2>' + title + '</h2><p>' + explanation + '</p><img src="' + image + '" alt="' + title + '">'
page += '<h2>Minutes experiment</h2><div class="scroll">' + minutes.to_html(index=False, border=0) + '</div>'
page += '<h2>Inspect the evidence</h2><p><a href="shortlist.csv">All eligible players</a> · <a href="tradeoff_pool.csv">Dominance evidence</a> · <a href="search_settings.json">Run settings</a> · <a href="../FEEDBACK.md">Reviewer worksheet</a></p>'
page += '<p>Click on above links to export the result CSVs.</p></body></html>'
(results / 'review.html').write_text(page, encoding='utf-8')
print('Wrote results/review.html')
