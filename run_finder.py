# Run the complete offline shortlist workflow from preferences.json.
from pathlib import Path
import hashlib
import json
import subprocess
import sys

folder = Path(__file__).resolve().parent
settings = json.loads((folder / 'preferences.json').read_text(encoding='utf-8'))

# A small set of input rules catches accidental settings edits before old outputs change.
if settings['position'] not in ['GK', 'DEF', 'MID', 'FWD']:
    sys.exit('Set position to GK, DEF, MID or FWD in preferences.json.')
if settings['ranking'] not in ['points', 'position']:
    sys.exit('Set ranking to points or position in preferences.json.')
for field, low, high in [('max_price', 0.1, 100), ('max_ownership', 0, 100),
                         ('min_minutes', 1, 10000), ('top_n', 1, 15)]:
    value = settings[field]
    if type(value) not in (int, float) or not low <= value <= high:
        sys.exit(f'{field} must be a number between {low} and {high}.')
    if field in ['min_minutes', 'top_n'] and int(value) != value:
        sys.exit(f'{field} must be a whole number.')
# head() needs an integer even when JSON was edited as 8.0.
if type(settings['top_n']) is not int or type(settings['min_minutes']) is not int:
    sys.exit('Write top_n and min_minutes as integers, for example 8 and 180.')

metadata = json.loads((folder / 'dataset/fpl_snapshot.metadata.json').read_text())
actual = hashlib.sha256((folder / 'dataset/fpl_snapshot.json').read_bytes()).hexdigest()
if actual != metadata['sha256']:
    sys.exit('Snapshot and metadata do not match. Restore the supplied pair or download a new pair.')

# Each script does one analysis. check=True stops if a stage fails so the final
# report cannot silently combine a failed new run with earlier successful results.
for script in ['find_players.py', 'check_minutes.py', 'compare_tradeoffs.py', 'make_report.py']:
    print('\nRunning', script, flush=True)
    subprocess.run([sys.executable, str(folder / script)], check=True)
print('\nOpen results/review.html in a browser to inspect the complete run.')
