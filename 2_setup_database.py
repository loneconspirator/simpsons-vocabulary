import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('tv_vocab.db')
cursor = conn.cursor()

# Create table for words
cursor.execute('''
CREATE TABLE IF NOT EXISTS words (
    word TEXT PRIMARY KEY,
    count INTEGER DEFAULT 0,
    is_vocabulary BOOLEAN DEFAULT NULL,
    use BOOLEAN DEFAULT FALSE
)
''')

# Create table for episodes
cursor.execute('''
CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY,
    episode_name TEXT
)
''')

# Create join table for word appearances in episodes
cursor.execute('''
CREATE TABLE IF NOT EXISTS uses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT,
    original_word TEXT,
    episode_id TEXT,
    FOREIGN KEY (word) REFERENCES words(word),
    FOREIGN KEY (episode_id) REFERENCES episodes(episode_id)
)
''')

# Create an index on the count column
cursor.execute('CREATE INDEX IF NOT EXISTS idx_count ON words (count)')

# Commit changes and close the connection
conn.commit()
conn.close()
