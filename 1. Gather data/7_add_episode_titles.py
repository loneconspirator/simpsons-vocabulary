import csv
import sqlite3
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db():
    db = sqlite3.connect('../db/tv_vocab.db')
    db.row_factory = sqlite3.Row
    return db

def update_episode_data(csv_path):
    if not Path(csv_path).exists():
        logging.error(f"CSV file not found: {csv_path}")
        sys.exit(1)

    db = get_db()
    cursor = db.cursor()

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Construct episode_id in the format s01e01
                episode_id = f"s{int(row['Season']):02d}e{int(row['Episode']):02d}"

                # Check if episode exists
                cursor.execute(
                    "SELECT episode_id FROM episodes WHERE episode_id = ?",
                    (episode_id,)
                )

                if cursor.fetchone():
                    # Update existing episode
                    cursor.execute("""
                        UPDATE episodes
                        SET episode_name = ?,
                            season = ?,
                            episode = ?
                        WHERE episode_id = ?
                    """, (
                        row['Title'],
                        int(row['Season']),
                        int(row['Episode']),
                        episode_id
                    ))
                    logging.info(f"Updated episode {episode_id}: {row['Title']}")
                else:
                    logging.warning(f"Episode {episode_id} not found in database")

        db.commit()
        logging.info("Episode data update completed")

    except Exception as e:
        db.rollback()
        logging.error(f"Error updating episode data: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python 7_add_episode_titles.py <csv_file_path>")
        sys.exit(1)

    csv_file = sys.argv[1]
    update_episode_data(csv_file)
