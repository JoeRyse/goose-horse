import os

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
MEETINGS_DIR = os.path.join(DOCS_DIR, "meetings")

def update_homepage():
    print("🎨 Building New White/Orange Index...")
    files = [f for f in os.listdir(MEETINGS_DIR) if f.endswith('.html')]
    
    # 1. Group by Country
    grouped_files = {}
    
    for f in files:
        path = os.path.join(MEETINGS_DIR, f)
        country = "International" 
        try:
            with open(path, 'r', encoding='utf-8') as file_obj:
                first_line = file_obj.readline()
                if "META_COUNTRY" in first_line:
                    country = first_line.split("META_COUNTRY:")[1].split("-->")[0].strip()
        except:
            pass
            
        if country not in grouped_files:
            grouped_files[country] = []
        grouped_files[country].append(f)

    # 2. Build HTML (Clean White/Orange Theme)
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>World Handicapper HQ</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { margin: 0; font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background: #ffffff; color: #333; }
            .hero { text-align: center; padding: 50px 20px; background: #fff; border-bottom: 4px solid #003366; }
            .logo { max-height: 100px; margin-bottom: 20px; }
            h1 { margin: 0; color: #003366; text-transform: uppercase; letter-spacing: 2px; font-size: 2.2rem; font-weight: 800; }
            .subtitle { color: #666; font-size: 1.1rem; margin-top: 5px; font-weight: 500; }
            .container { max-width: 1100px; margin: 0 auto; padding: 40px 20px; }
            .section-title { border-bottom: 3px solid #ff6b00; padding-bottom: 10px; margin: 50px 0 30px 0; font-size: 1.6rem; color: #003366; font-weight: 700; display: flex; align-items: center; }
            .flag { margin-right: 12px; font-size: 1.5rem; }
            .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }
            .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; transition: all 0.2s ease; text-decoration: none; color: #333; display: block; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .card:hover { transform: translateY(-4px); box-shadow: 0 12px 20px rgba(0,0,0,0.1); border-color: #ff6b00; }
            .card-body { padding: 20px; }
            .track-name { font-size: 1.3rem; font-weight: 700; margin-bottom: 8px; display: block; color: #003366; }
            .date-badge { display: inline-block; background: #f0f9ff; color: #003366; padding: 5px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; }
            .status { color: #ff6b00; font-size: 0.8rem; font-weight: 800; margin-top: 15px; display: block; text-transform: uppercase; letter-spacing: 1px; }
        </style>
    </head>
    <body>
        <div class="hero">
            <img src="logo.png" class="logo" alt="Logo">
            <h1>World Handicapper</h1>
            <div class="subtitle">Professional Racing Intelligence</div>
        </div>
        <div class="container">
    """
    
    for country, files in grouped_files.items():
        flag = "🌍"
        if "Australia" in country: flag = "🇦🇺"
        elif "USA" in country: flag = "🇺🇸"
        elif "UK" in country: flag = "🇬🇧"
        elif "Hong Kong" in country: flag = "🇭🇰"
        
        html += f'<div class="section-title"><span class="flag">{flag}</span> {country} Racing</div><div class="grid">'
        for f in sorted(files, reverse=True):
            display_name = f.replace(".html", "").replace("_", " ")
            html += f'<a href="meetings/{f}" class="card"><div class="card-body"><span class="track-name">{display_name}</span><span class="date-badge">Full Analysis</span><span class="status">● View Form</span></div></a>'
        html += "</div>"
        
    html += "</div></body></html>"
    
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding='utf-8') as f:
        f.write(html)
    print("✅ Index Rebuilt! Open docs/index.html to check.")

if __name__ == "__main__":
    update_homepage()