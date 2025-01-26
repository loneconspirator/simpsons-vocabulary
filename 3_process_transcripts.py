import sqlite3
import os
import re
import spacy

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Connect to the SQLite database
conn = sqlite3.connect('tv_vocab.db')
cursor = conn.cursor()

def extract_words(content):
    # Process the text with spaCy
    doc = nlp(content.lower())
    
    # Extract lemmatized words, keeping only those with alphabetic characters
    # and filtering out stop words and punctuation
    words = [token.lemma_ for token in doc 
            if token.is_alpha  # only alphabetic characters
            and not token.is_stop  # not a stop word
            and not token.is_punct  # not punctuation
            and len(token.text) > 1]  # more than one character
    
    return words

# Function to process a transcript file
def process_transcript(file_path, episode_id):
    # Check if episode_id is already in the database
    cursor.execute('SELECT episode_id FROM episodes WHERE episode_id = ?', (episode_id,))
    result = cursor.fetchone()

    if result:
        raise ValueError(f"Episode ID {episode_id} already exists in the database.")
    else:
        # Insert new episode
        cursor.execute('INSERT INTO episodes (episode_id) VALUES (?)', (episode_id,))

    # Read and process the transcript file
    with open(file_path, 'r') as file:
        content = file.read()
        words = extract_words(content)

        for word in words:
            # Check if the word is already in the database
            cursor.execute('SELECT count FROM words WHERE word = ?', (word,))
            result = cursor.fetchone()

            if result:
                # Increment the count
                cursor.execute('UPDATE words SET count = count + 1 WHERE word = ?', (word,))
            else:
                # Insert new word
                cursor.execute('INSERT INTO words (word, count) VALUES (?, 1)', (word,))

            # Insert into word_episodes join table
            cursor.execute('INSERT OR IGNORE INTO word_episodes (word, episode_id) VALUES (?, ?)', (word, episode_id))

    # Commit changes
    conn.commit()

# Example usage
# Assuming transcript files are stored in a directory named 'transcripts'
transcript_dir = 'transcripts'

for filename in os.listdir(transcript_dir):
    if filename.endswith('.txt'):
        episode_id = filename.replace('.txt', '')
        file_path = os.path.join(transcript_dir, filename)
        process_transcript(file_path, episode_id)

# Close the database connection
conn.close()
