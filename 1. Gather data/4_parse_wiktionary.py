import xml.sax
import sqlite3
import os
import atexit
from tqdm import tqdm

# Connect to the new wiktionary database
conn = sqlite3.connect('../db/wiktionary.db')
cursor = conn.cursor()

# Disable auto-commit and set PRAGMA synchronous to OFF
conn.isolation_level = None
cursor.execute('PRAGMA synchronous = OFF')

# Create the words table if it does not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT,
    entry TEXT
)
''')

# Batch insert
batch_size = 1000
batch = []

# Insert word and definition into the database
# Collect entries in a batch and insert them together
def insert_word_definition(word, entry):
    batch.append((word, entry))
    if len(batch) >= batch_size:
        cursor.executemany('INSERT INTO words (word, entry) VALUES (?, ?)', batch)
        conn.commit()
        batch.clear()

# Ensure remaining entries are inserted after parsing
atexit.register(lambda: cursor.executemany('INSERT INTO words (word, entry) VALUES (?, ?)', batch) if batch else None)
atexit.register(conn.commit)

class WiktionaryHandler(xml.sax.ContentHandler):
    def __init__(self, file_size, progress_bar):
        self.current_tag = ""
        self.is_page = False
        self.is_revision = False
        self.is_text = False
        self.is_ns = False
        self.title = ""
        self.text = ""
        self.ns = ""
        self.file_size = file_size
        self.bytes_read = 0
        self.progress_bar = progress_bar

    def startElement(self, tag, attributes):
        self.current_tag = tag
        if tag == "page":
            self.is_page = True
            self.title = ""
            self.text = ""
            self.ns = ""
        elif self.is_page and tag == "revision":
            self.is_revision = True
        elif self.is_revision and tag == "text":
            self.is_text = True
        elif self.is_page and tag == "ns":
            self.is_ns = True

    def endElement(self, tag):
        if tag == "page":
            self.is_page = False
            if self.title and self.text and self.ns == "0":
                insert_word_definition(self.title, self.text)
        elif tag == "revision":
            self.is_revision = False
        elif tag == "text":
            self.is_text = False
        elif tag == "ns":
            self.is_ns = False

        # Update progress bar
        self.bytes_read += len(tag) + 2  # Approximate bytes read
        self.progress_bar.update(len(tag) + 2)

    def characters(self, content):
        if self.current_tag == "title":
            self.title += content
        elif self.is_text:
            self.text += content
        elif self.is_ns:
            self.ns += content

        # Update the number of bytes read
        self.bytes_read += len(content.encode('utf-8'))
        self.progress_bar.update(len(content.encode('utf-8')))

# Create a parser and set the handler
file_path = '../wiktionary/dump.xml'
file_size = os.path.getsize(file_path)
parser = xml.sax.make_parser()

# Initialize progress bar
progress_bar = tqdm(total=file_size, unit='B', unit_scale=True, desc='Parsing XML')

parser.setContentHandler(WiktionaryHandler(file_size, progress_bar))

# Parse the XML file
with open(file_path, 'r', encoding='utf-8') as file:
    parser.parse(file)

# Close progress bar
progress_bar.close()

# Now I want to create an index on the word column
print("Creating index on word column...")
cursor.execute('CREATE INDEX idx_word ON words (word)')

# Close the database connection
conn.close()
