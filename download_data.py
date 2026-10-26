import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import requests

# Create the data folder beside this script.
folder = Path(__file__).resolve().parent / "dataset"
folder.mkdir(exist_ok=True)

# Download the current data from the public FPL API.
# This optional step replaces the saved snapshot; it is not needed for the included demo.
url = "https://fantasy.premierleague.com/api/bootstrap-static/"
response = requests.get(url, timeout=30)
# Stop on an HTTP failure so an error page is not saved as player data.
response.raise_for_status()
# Parse the response into Python dictionaries and lists.
data = response.json()
download_time = datetime.now(timezone.utc)

# Save the complete API response as a readable JSON file.
# elements holds players, teams holds clubs, and events holds gameweek information.
snapshot_file = folder / "fpl_snapshot.json"
snapshot_text = json.dumps(data, ensure_ascii=False, indent=2)
snapshot_file.write_text(snapshot_text, encoding="utf-8")

# Calculate a fingerprint of the exact saved file.
# SHA-256 identifies these bytes; it does not prove the data is accurate.
checksum = hashlib.sha256(snapshot_file.read_bytes()).hexdigest()

# Identify the current gameweek recorded in the response.
# This is a list because the API flag may identify no current event at some times.
current_events = [
    event["id"]
    for event in data["events"]
    if event["is_current"]
]

# Record where and when the dataset was downloaded.
metadata = {
    "source_url": url,
    "retrieved_utc": download_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    "data_type": "Real FPL API response, saved for reproducible offline demonstration",
    "player_count": len(data["elements"]),
    "current_event_ids": current_events,
    "sha256": checksum
}

# Save the source information in a separate JSON file.
# The analysis displays this date so an older snapshot is not mistaken for live data.
metadata_file = folder / "fpl_snapshot.metadata.json"
metadata_file.write_text(
    json.dumps(metadata, indent=2),
    encoding="utf-8"
)

print(f"Downloaded {len(data['elements'])} players.")
print(f"Saved: {snapshot_file}")
print(f"Saved: {metadata_file}")