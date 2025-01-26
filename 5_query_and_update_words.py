import sqlite3
import time
import logging
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to SQLite databases
conn = sqlite3.connect('tv_vocab.db')
cursor = conn.cursor()
wiktionary_conn = sqlite3.connect('wiktionary.db')
wiktionary_cursor = wiktionary_conn.cursor()

# Function to query the local wiktionary database
# Perform a case-insensitive search for the word in the database
def query_local_wiktionary(word):
    start_time = time.time()
    wiktionary_cursor.execute('''
    SELECT 1 FROM words WHERE word = ?
    ''', (word.lower(),))
    result = wiktionary_cursor.fetchone()
    query_time = time.time() - start_time
    # logging.verbose(f"Query time for word '{word}': {query_time:.4f} seconds, result: {result}")
    return result is not None

# Loop through numbers 1 to 5
for count in range(1, 6):
    # Query database for words with the current count and is_vocabulary as NULL
    cursor.execute('''
    SELECT word FROM words WHERE count = ? AND is_vocabulary IS NULL
    ''', (count,))
    words = cursor.fetchall()

    # Use tqdm to show progress with total number of words
    total_words = len(words)
    for (word,) in tqdm(words, desc=f'Processing words with count {count}', total=total_words):
        word_start_time = time.time()
        # Query the local wiktionary database for the word definition
        definition = query_local_wiktionary(word)

        if definition:
            # Update the database and set is_vocabulary to TRUE if definition was found
            cursor.execute('''
            UPDATE words SET is_vocabulary = TRUE WHERE word = ?
            ''', (word,))
        else:
            # Set is_vocabulary to FALSE if no definition is found
            cursor.execute('''
            UPDATE words SET is_vocabulary = FALSE WHERE word = ?
            ''', (word,))

        # Commit changes after each update
        conn.commit()
        word_processing_time = time.time() - word_start_time
        # logging.debug(f"Total processing time for word '{word}': {word_processing_time:.4f} seconds")

# Close the database connections
conn.close()
wiktionary_conn.close()
