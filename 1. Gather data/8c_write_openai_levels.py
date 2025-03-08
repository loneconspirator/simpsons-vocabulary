import csv
import sqlite3
import sys

# Database file
db_file = '../db/tv_vocab.db'

# CSV file to read from
csv_file = '../output/new_levels.csv'

# Function to count lines in a file
def count_lines(file_path):
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        return sum(1 for _ in f) - 1  # Subtract 1 for the header row

# Get total number of records
total_records = count_lines(csv_file)
print(f"Found {total_records} records to process")

# Connect to the database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Read new_levels.csv
updated_count = 0
with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader, 1):
        user_id = row['id']
        level = row['level']

        # Update the level in the uses table
        cursor.execute("""
        UPDATE uses
        SET level = ?
        WHERE id = ?
        """, (level, user_id))

        if cursor.rowcount > 0:
            updated_count += 1

        # Display progress
        progress = (i / total_records) * 100
        sys.stdout.write(f"\rProgress: {i}/{total_records} ({progress:.1f}%) - Updated: {updated_count}")
        sys.stdout.flush()

# Print final summary
sys.stdout.write('\n')  # Move to a new line after the progress meter
print(f"Completed! Updated {updated_count} records in the uses table")

# Commit the changes
conn.commit()

# Close the connection
conn.close()
