import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('../db/tv_vocab.db')
cursor = conn.cursor()

# Create table for words
cursor.execute('''
CREATE TABLE IF NOT EXISTS words (
    word TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0,
    is_vocabulary BOOLEAN DEFAULT NULL
)
''')

# Create table for episodes
cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY,
    episode_name TEXT,
    publishable BOOLEAN DEFAULT FALSE,
    season INTEGER DEFAULT NULL,
    episode INTEGER DEFAULT NULL
)
''')

# Create join table for word appearances in episodes
cursor.execute('''
CREATE TABLE IF NOT EXISTS uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT,
    original_word TEXT,
    episode_id TEXT,
    definition TEXT,
    use BOOLEAN DEFAULT FALSE,
    appearance_order INTEGER,
    level TEXT CHECK (level IN ('elementary', 'middle', 'high', 'college', 'graduate', 'not vocabulary')) DEFAULT NULL,
    no_definition BOOLEAN DEFAULT FALSE NOT NULL,
    FOREIGN KEY (word) REFERENCES words(word),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
)
''')

# Create an index on the count column
cursor.execute('CREATE INDEX IF NOT EXISTS idx_count ON words (count)')

# Commit changes and close the connection
conn.commit()
conn.close()
