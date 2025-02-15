import sqlite3
import os
import re
import spacy

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

# Connect to the SQLite database
conn = sqlite3.connect('../db/tv_vocab.db')
cursor = conn.cursor()

def extract_words(content):
    # Process the text with spaCy
    doc = nlp(content.lower())

    # Extract lemmatized words and their original forms, keeping only those with alphabetic characters
    # and filtering out stop words and punctuation
    words = [(token.lemma_, token.text) for token in doc
            if token.is_alpha  # only alphabetic characters
            and not token.is_stop  # not a stop word
            and not token.is_punct  # not punctuation
            and len(token.text) > 1]  # more than one character

    return words

# Function to process a transcript file
def process_transcript(file_path, episode_id):
    print(f"\nProcessing transcript: {file_path}")
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
        print(f"Found {len(words)} unique words")

        word_count = 0
        for lemma, original in words:
            # Check if the word is already in the database
            cursor.execute('SELECT count FROM words WHERE word = ?', (lemma,))
            result = cursor.fetchone()

            if result:
                # Increment the count
                cursor.execute('UPDATE words SET count = count + 1 WHERE word = ?', (lemma,))
            else:
                # Insert new word
                cursor.execute('INSERT INTO words (word, count) VALUES (?, 1)', (lemma,))

            # Insert into uses table with original word
            cursor.execute('INSERT INTO uses (word, original_word, episode_id) VALUES (?, ?, ?)',
                         (lemma, original, episode_id))
            word_count += 1
            if word_count % 100 == 0:
                print(f"Processed {word_count}/{len(words)} words...", end='\r')

        print(f"\nCompleted processing {word_count} words for episode {episode_id}")

    # Commit changes
    conn.commit()

# Example usage
# Assuming transcript files are stored in a directory named 'transcripts'
transcript_dir = '../transcripts'

print("\nStarting transcript processing...")
# Get all transcript files and sort them
transcript_files = sorted([f for f in os.listdir(transcript_dir) if f.endswith('.txt')])

for filename in transcript_files:
    episode_id = filename.replace('.txt', '')
    file_path = os.path.join(transcript_dir, filename)
    process_transcript(file_path, episode_id)

# Close the database connection
conn.close()
