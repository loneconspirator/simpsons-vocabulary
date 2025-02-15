import sqlite3
import pandas as pd

# Connect to the SQLite database
conn = sqlite3.connect('../tv_vocab.db')
cursor = conn.cursor()

# Query to get words used fewer than 5 times and their episodes
query = '''
SELECT w.word, GROUP_CONCAT(e.episode_id) as episodes
FROM words w
JOIN word_episodes we ON w.word = we.word
JOIN episodes e ON we.episode_id = e.episode_id
WHERE w.count < 5
GROUP BY w.word
'''

# Execute the query
cursor.execute(query)

# Fetch all results
results = cursor.fetchall()

# Create a DataFrame from the results
words_df = pd.DataFrame(results, columns=['Word', 'Episodes'])

# Write the DataFrame to an Excel file
words_df.to_excel('words_fewer_than_5.xlsx', index=False)

# Close the database connection
conn.close()
