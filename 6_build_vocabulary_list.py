import sqlite3

# Connect to the SQLite database
def connect_db():
    return sqlite3.connect('tv_vocab.db')

# Function to get vocabulary words for each episode
def get_vocabulary_list():
    conn = connect_db()
    cursor = conn.cursor()
    
    # Query to get episode IDs in order
    cursor.execute('SELECT episode_id FROM episodes ORDER BY episode_id')
    episodes = cursor.fetchall()
    
    # Iterate through each episode and get vocabulary words
    for episode in episodes:
        episode_id = episode[0]
        print(f"\nEpisode {episode_id}")
        print("-" * (len(str(episode_id)) + 8))
        
        # Query to get vocabulary words for the episode in order of first appearance
        # Using MIN(u.id) to get the first occurrence of each word
        cursor.execute('''
            WITH FirstAppearance AS (
                SELECT 
                    w.word,
                    MIN(u.id) as first_appearance_id,
                    MIN(u.original_word) as original_form
                FROM words w
                JOIN uses u ON w.word = u.word
                WHERE u.episode_id = ? AND w.is_vocabulary = 1
                GROUP BY w.word
            )
            SELECT word, original_form
            FROM FirstAppearance
            ORDER BY first_appearance_id
        ''', (episode_id,))
        
        vocabulary_words = cursor.fetchall()
        
        # Print vocabulary words with their original form
        if vocabulary_words:
            for lemma, original in vocabulary_words:
                if lemma != original:
                    print(f"{lemma} ({original})")
                else:
                    print(lemma)
        else:
            print("No vocabulary words found")
        
    # Close the connection
    conn.close()

if __name__ == "__main__":
    get_vocabulary_list()
