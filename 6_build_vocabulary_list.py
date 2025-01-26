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
        print(f"Episode ID: {episode_id}")
        
        # Query to get vocabulary words for the episode
        cursor.execute('''
            SELECT w.word FROM words w
            JOIN word_episodes we ON w.word = we.word
            WHERE we.episode_id = ? AND w.is_vocabulary = 1
        ''', (episode_id,))
        vocabulary_words = cursor.fetchall()
        
        # Print vocabulary words
        for word in vocabulary_words:
            print(word[0])
        print("\n")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    get_vocabulary_list()
