import json
import os

# Path to your track database
DB_PATH = os.path.join("data", "track_db.json")

# Load existing database
with open(DB_PATH, "r") as f:
    db = json.load(f)

# --- 1. USA THOROUGHBRED PAR ADJUSTMENTS ---
usa_tiers = {
    "Saratoga": {"tier": "Tier 1 (Max)", "lengths": 6.0, "points": 15.0},
    "Del_Mar": {"tier": "Tier 1 (Summer Elite)", "lengths": 5.0, "points": 12.0},
    "Keeneland": {"tier": "Tier 1 (Huge Fields)", "lengths": 5.0, "points": 12.0},
    "Belmont_Park": {"tier": "Tier 1 (Stamina Test)", "lengths": 5.0, "points": 12.0},
    "Santa_Anita": {"tier": "Tier 1 (Insulated West)", "lengths": 4.5, "points": 10.0},
    "Gulfstream_Park": {"tier": "Tier 1 (Winter Elite)", "lengths": 4.5, "points": 10.0},
    "Churchill_Downs": {"tier": "Tier 1 (Major)", "lengths": 4.0, "points": 9.0},
    "Aqueduct": {"tier": "Tier 2 (Winter Grind)", "lengths": 2.5, "points": 6.0},
}
usa_tier_2 = ["Oaklawn_Park", "Fair_Grounds", "Tampa_Bay_Downs", "Monmouth_Park", "Laurel_Park", "Woodbine", "Kentucky_Downs", "Colonial_Downs"]

for track_name, track_data in db.get("USA_Thoroughbred", {}).items():
    if track_name in usa_tiers:
        track_data["par_adjustment"] = usa_tiers[track_name]
    elif track_name in usa_tier_2:
        track_data["par_adjustment"] = {"tier": "Tier 2 (Regional Premier)", "lengths": 2.0, "points": 5.0}
    else:
        track_data["par_adjustment"] = {"tier": "Tier 3 (Baseline)", "lengths": 0.0, "points": 0.0}

# --- 2. AUSTRALIA THOROUGHBRED PAR ADJUSTMENTS ---
aus_tiers = {
    "Tier 1 (Elite Metro)": {"tracks": ["Royal_Randwick", "Flemington", "Rosehill_Gardens", "Caulfield"], "lengths": 2.0, "points": 5.0},
    "Tier 1.5 (State Metro)": {"tracks": ["Eagle_Farm", "Doomben", "Ascot", "Morphettville", "Moonee_Valley", "Sandown", "Warwick_Farm"], "lengths": 1.0, "points": 2.5},
    "Tier 2 (Premier Provincial)": {"tracks": ["Newcastle", "Hawkesbury", "Scone", "Cranbourne", "Kembla_Grange"], "lengths": 0.5, "points": 1.0},
    "Tier 3 (Provincial Baseline)": {"tracks": ["Gosford", "Wyong", "Bendigo", "Ballarat", "Gold_Coast", "Sunshine_Coast", "Pakenham", "Ipswich", "Townsville", "Rockhampton", "Mackay"], "lengths": 0.0, "points": 0.0},
    "Tier 4 (Premium Country)": {"tracks": ["Wagga", "Tamworth", "Albury", "Seymour", "Terang", "Ararat", "Sale", "Balaklava", "Gawler", "Murray_Bridge", "Geraldton", "Bunbury", "Belmont_Park_WA", "Ashburton", "Te_Rapa", "Te_Aroha", "Manawatu"], "lengths": -1.0, "points": -2.5},
    "Tier 5 (Bush Country)": {"tracks": ["Dubbo", "Gatton", "Lismore", "Quirindi", "Thangool", "Warwick", "Esperance", "Clare", "Kingscote", "Kilmore", "Wodonga", "Orange", "Bathurst", "Nowra", "Port_Macquarie", "Taree", "Murwillumbah", "Grafton", "Launceston", "Queanbeyan", "Swan_Hill"], "lengths": -2.0, "points": -5.0}
}

def update_aus_tracks(data):
    for k, v in data.items():
        if isinstance(v, dict) and "location" in v:
            assigned = False
            for tier_name, tier_data in aus_tiers.items():
                if k in tier_data["tracks"]:
                    v["par_adjustment"] = {"tier": tier_name, "lengths": tier_data["lengths"], "points": tier_data["points"]}
                    assigned = True
                    break
            if not assigned:
                 v["par_adjustment"] = {"tier": "Tier 3 (Provincial Baseline)", "lengths": 0.0, "points": 0.0}
        elif isinstance(v, dict):
            update_aus_tracks(v)

update_aus_tracks(db.get("Australia_Thoroughbred", {}))

# --- 3. HARNESS PAR ADJUSTMENTS ---
harness_regions = ["USA_Harness", "Canada_Harness", "Australia_Harness", "Europe_Harness"]
for region in harness_regions:
    for track_name, track_data in db.get(region, {}).items():
        layout = str(track_data.get("layout", "")).lower()
        if "7/8" in layout or "1 mile" in layout or "1000m" in layout or "2100m" in layout:
            track_data["par_adjustment"] = {"tier": "Tier 1 (Big Track / Premier)", "lengths": 0.0, "points": 10.0}
        elif "5/8" in layout:
            track_data["par_adjustment"] = {"tier": "Tier 2 (Mid-Size)", "lengths": 0.0, "points": 5.0}
        else:
            track_data["par_adjustment"] = {"tier": "Tier 3 (Half-Mile Bullring Baseline)", "lengths": 0.0, "points": 0.0}

# Save updated database
with open(DB_PATH, "w") as f:
    json.dump(db, f, indent=2)

print("Successfully injected Par Adjustments into all 114 tracks!")