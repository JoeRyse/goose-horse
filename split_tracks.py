import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DB_PATH = os.path.join(BASE_DIR, "data", "track_db.json")
TRACKS_DIR = os.path.join(BASE_DIR, "tracks")

os.makedirs(TRACKS_DIR, exist_ok=True)

def recursive_extract(node, region_tag):
    """Recursively walks down any nested structure in track_db.json to find track dictionaries."""
    count = 0
    if isinstance(node, dict):
        # Check if this node is actually a track profile (contains layout/par keys)
        if "location" in node or "courses" in node or "par_adjustment" in node or "bias_notes" in node:
            # We found a track! But since the function caller passed the track name as a key, 
            # this base case is handled by the loop below.
            return 0

        for key, val in node.items():
            if key == "metadata":
                continue
            if isinstance(val, dict):
                # Check if val is a track dictionary
                if "location" in val or "courses" in val or "par_adjustment" in val or "bias_notes" in val:
                    save_track_file(key, region_tag, val)
                    count += 1
                else:
                    # Keep digging deeper (e.g., entering Queensland, Metropolitan, etc.)
                    new_tag = f"{region_tag}_{key}" if region_tag else key
                    count += recursive_extract(val, new_tag)
    return count

def save_track_file(track_name, region_tag, track_data):
    filename = f"{track_name.lower().replace(' ', '_').replace('-', '_')}.json"
    filepath = os.path.join(TRACKS_DIR, filename)
    
    track_data["region_group"] = region_tag
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(track_data, f, indent=4)

def split_master_database():
    if not os.path.exists(MASTER_DB_PATH):
        print(f"Error: Could not find {MASTER_DB_PATH}")
        return

    with open(MASTER_DB_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_extracted = recursive_extract(data, "")
    print(f"Successfully extracted and saved {total_extracted} track files into the 'tracks/' folder!")

if __name__ == "__main__":
    split_master_database()