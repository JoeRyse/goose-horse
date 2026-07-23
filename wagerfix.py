import sqlite3

conn = sqlite3.connect('logs/master_betting_history.db')
c = conn.cursor()

# Strip out rogue '$' following '#' in predictions
c.execute("UPDATE predictions SET raw_features = REPLACE(raw_features, '#$', '#') WHERE raw_features LIKE '%#$%'")
c.execute("UPDATE predictions SET p1_reason = REPLACE(p1_reason, '#$', '#') WHERE p1_reason LIKE '%#$%'")

conn.commit()
conn.close()
print("Database prediction text cleaned!")