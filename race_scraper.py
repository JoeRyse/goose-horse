import requests
from bs4 import BeautifulSoup
import datetime
import re
import webbrowser

# === MASTER TRACK PROFILE DIRECTORY ===
# This matches the tracks in your track_profiles.md
# It tells the script WHERE to look (Country) and WHAT code to use.

TRACK_DIRECTORY = {
    # --- US TRACKS (Equibase Codes) ---
    "Saratoga":         {"country": "US", "code": "SAR"},
    "Gulfstream_Park":  {"country": "US", "code": "GP"},
    "Santa_Anita":      {"country": "US", "code": "SA"},
    "Del_Mar":          {"country": "US", "code": "DMR"},
    "Keeneland":        {"country": "US", "code": "KEE"},
    "Churchill_Downs":  {"country": "US", "code": "CD"},
    "Aqueduct":         {"country": "US", "code": "AQU"},
    "Belmont_Park":     {"country": "US", "code": "BEL"},
    "Tampa_Bay_Downs":  {"country": "US", "code": "TAM"},
    "Oaklawn_Park":     {"country": "US", "code": "OP"},
    "Parx_Racing":      {"country": "US", "code": "PRX"},
    "Turfway_Park":     {"country": "US", "code": "TP"},
    "Fair_Grounds":     {"country": "US", "code": "FG"},
    "Woodbine":         {"country": "US", "code": "WO"}, # Uses Equibase even though Canada

    # --- AUSTRALIAN TRACKS (Racing Australia) ---
    "Flemington":       {"country": "AU", "code": "Flemington"},
    "Moonee_Valley":    {"country": "AU", "code": "Moonee Valley"},
    "Caulfield":        {"country": "AU", "code": "Caulfield"},
    "Randwick":         {"country": "AU", "code": "Randwick"},
    "Rosehill":         {"country": "AU", "code": "Rosehill"},
    "Doomben":          {"country": "AU", "code": "Doomben"},
    "Eagle_Farm":       {"country": "AU", "code": "Eagle Farm"},
}

def get_track_profile(db_track_name):
    """
    1. Tries exact match.
    2. Tries to match by replacing underscores with spaces (common database difference).
    """
    # Try exact match
    if db_track_name in TRACK_DIRECTORY:
        return TRACK_DIRECTORY[db_track_name]
    
    # Try "Fuzzy" match (Database: "Tampa_Bay_Downs" vs Directory: "Tampa Bay Downs")
    # This loop helps if you named them slightly differently
    clean_name = db_track_name.replace("_", " ").lower()
    
    for key, val in TRACK_DIRECTORY.items():
        if key.replace("_", " ").lower() == clean_name:
            return val
            
    return None

def get_us_results(track_profile, date_obj):
    code = track_profile['code']
    date_str = date_obj.strftime("%m%d%y")
    url = f"https://www.equibase.com/static/chart/summary/{code}{date_str}USA.html"
    
    print(f"   🔎 Checking Equibase for {code}...")
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers)
        if r.status_code == 404: return {}
            
        soup = BeautifulSoup(r.content, 'html.parser')
        results = {}
        tables = soup.find_all('table', class_='table-hover')
        
        for table in tables:
            header = table.find_previous('h3')
            if not header: continue
            
            match = re.search(r'Race (\d+)', header.text)
            if not match: continue
            race_num = int(match.group(1))
            
            rows = table.find_all('tr')[1:] 
            race_positions = {}
            rank_counter = 1
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                prog_num = cols[0].text.strip()
                if prog_num.isdigit():
                    race_positions[rank_counter] = prog_num
                    rank_counter += 1
                if rank_counter > 4: break
            
            if race_positions:
                results[race_num] = race_positions

        return results
    except Exception as e:
        print(f"   ❌ Scraper Error: {e}")
        return {}

def get_au_results(track_name, date_obj):
    # Because AU sites are hard to scrape without Selenium, 
    # we just open the page for you to see.
    date_str = date_obj.strftime("%Y-%m-%d")
    print(f"   ℹ️  Opening Racing Australia for {track_name}...")
    url = f"https://racingaustralia.horse/FreeFields/Calendar_Results.aspx?Date={date_str}"
    webbrowser.open(url)
    return {}