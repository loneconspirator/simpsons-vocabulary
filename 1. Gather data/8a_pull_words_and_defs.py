import sqlite3
import csv

# Database file
db_file = '../db/tv_vocab.db'

# CSV file to write to
csv_file = '../output/output.csv'

# Connect to the database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Query to select data from the 'uses' table where level is not NULL
query = """
SELECT id, episode_id, word, original_word, level, definition
FROM uses
WHERE level IS NOT NULL;
"""

# Execute the query
cursor.execute(query)
data = cursor.fetchall()

# Get column names
column_names = [description[0] for description in cursor.description]

# Write the data to a CSV file
with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
    csv_writer = csv.writer(csvfile)

    # Write the header
    csv_writer.writerow(column_names)

    # Write the data rows
    csv_writer.writerows(data)

# Close the connection
conn.close()

print(f"Data written to {csv_file}")
