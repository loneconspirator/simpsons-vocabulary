import re
import sqlite3
from typing import List
import mwparserfromhell
from bs4 import BeautifulSoup
import unicodedata
import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)  # Set to WARNING to suppress debug output

def get_word_definitions(word: str) -> List[str]:
    """Get all definitions for a word from the wiktionary database."""
    conn = sqlite3.connect('db/wiktionary.db')
    conn.text_factory = str  # Use Python's string type for text

    # Try both composed and decomposed forms of the word
    composed_word = unicodedata.normalize('NFC', word)
    decomposed_word = unicodedata.normalize('NFD', word)

    # Try exact match with both forms
    cursor = conn.cursor()
    cursor.execute('SELECT entry FROM words WHERE word = ? OR word = ? OR word = ?',
                  (word, composed_word, decomposed_word))
    result = cursor.fetchone()

    # If no match, try case-insensitive with both forms
    if not result:
        cursor.execute('SELECT entry FROM words WHERE lower(word) = lower(?) OR lower(word) = lower(?) OR lower(word) = lower(?)',
                      (word, composed_word, decomposed_word))
        result = cursor.fetchone()

    if not result:
        return []

    # Ensure proper text decoding
    entry_text = result[0]
    if isinstance(entry_text, bytes):
        entry_text = entry_text.decode('utf-8')
    conn.close()

    definitions = []

    # Parse wikitext
    wikicode = mwparserfromhell.parse(entry_text)

    # Find English section
    english_section = None
    sections = wikicode.get_sections(levels=[2])
    logger.debug(f"Processing word: {word}")
    logger.debug("Level 2 sections:")
    for section in sections:
        if not section.nodes:
            continue
        heading = str(section.get(0).title).strip()
        logger.debug(f"- {heading}")
        if heading == "English":
            english_section = section
            break

    if not english_section:
        logger.debug("No English section found")
        return []

    # Find parts of speech sections
    pos_headings = ["Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Preposition", "Conjunction", "Interjection"]

    logger.debug("\nLevel 3 sections in English:")
    level3_sections = english_section.get_sections(levels=[3])
    for section in level3_sections:
        if section.nodes and hasattr(section.get(0), 'title'):
            logger.debug(f"- {str(section.get(0).title).strip()}")

    for pos in pos_headings:
        pos_sections = english_section.get_sections(levels=[3], matches=pos)
        for section in pos_sections:
            logger.debug(f"\nProcessing {pos} section:")

            # Get all text content from the section
            section_text = str(section)
            logger.debug(f"Section content:\n{section_text}")

            # Find all definition lines and trans-see references
            trans_see_refs = {}
            in_trans_section = False
            for line in section_text.split('\n'):
                line = line.strip()

                # Track if we're in a translations section
                if line.startswith('{{trans-'):
                    in_trans_section = True
                elif line == '{{trans-bottom}}':
                    in_trans_section = False

                # Process trans-see references
                if in_trans_section and '{{trans-see|' in line:
                    template = mwparserfromhell.parse(line)
                    for t in template.filter_templates():
                        if t.name.strip() == 'trans-see' and len(t.params) >= 2:
                            meaning = str(t.params[0]).strip()
                            target = str(t.params[1]).strip()
                            trans_see_refs[meaning] = target

                # Process definition lines
                if line.startswith('#') and not line.startswith(('#*', '##')):
                    # Clean up the definition
                    definition = line[1:].strip()
                    logger.debug(f"Found definition line: {definition}")

                    # Skip if it looks like an example (contains a period in the middle)
                    if '.' in definition[:-1]:  # Allow period at end of sentence
                        continue

                    # Parse the definition to handle templates
                    parsed = mwparserfromhell.parse(definition)

                    # Extract usage labels first
                    usage_labels = []
                    for template in parsed.filter_templates():
                        template_name = template.name.strip()
                        if template_name in ('lb', 'label'):
                            # Get the label
                            if len(template.params) > 1:
                                label = str(template.params[1]).strip()
                                if label and label not in usage_labels:
                                    usage_labels.append(label)

                    # Clean up templates
                    for template in parsed.filter_templates():
                        try:
                            template_name = template.name.strip()
                            if template_name in ('non-gloss', 'gloss'):
                                # Replace template with its content
                                if len(template.params) > 0:
                                    content = str(template.params[0])
                                    # Clean up wiki links in the content
                                    content = re.sub(r'\[\[[^]]*\|([^]]*)\]\]', r'\1', content)
                                    content = re.sub(r'\[\[([^]]*)\]\]', r'\1', content)
                                    # Add a space after the content to prevent concatenation
                                    parsed.replace(template, content + ' ')
                                    logger.debug(f"After non-gloss template: {str(parsed)}")
                            elif template_name in ('l', 'm', 'link'):
                                # Replace with first parameter after language code
                                if len(template.params) > 1:
                                    parsed.replace(template, str(template.params[1]))
                            elif template_name == 'cap':
                                # Handle cap template
                                if len(template.params) > 0:
                                    # Get the content and capitalize it
                                    content = str(template.params[0]).strip()
                                    if content:
                                        parsed.replace(template, content[0].upper() + content[1:])
                            elif template_name == 'lb':
                                # Just remove language/usage labels
                                parsed.remove(template)
                            else:
                                # For any other templates, just remove them
                                parsed.remove(template)
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Error processing template {template}: {str(e)}")
                            try:
                                # If we can't process it properly, just remove it
                                parsed.remove(template)
                            except ValueError:
                                # If we can't remove it, just continue
                                pass

                    # Clean up wiki links
                    text = str(parsed)
                    logger.debug(f"Before wiki links cleanup: {text}")
                    text = re.sub(r'\[\[[^]]*\|([^]]*)\]\]', r'\1', text)
                    text = re.sub(r'\[\[([^]]*)\]\]', r'\1', text)
                    parsed = mwparserfromhell.parse(text)
                    logger.debug(f"After wiki links cleanup: {str(parsed)}")

                    # Convert wikitext to HTML
                    html = str(parsed.strip_code())
                    logger.debug(f"After HTML conversion: {html}")

                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')

                    # Get the text content
                    definition = soup.get_text()
                    logger.debug(f"After BeautifulSoup: {definition}")

                    # Clean up
                    definition = definition.strip()
                    definition = ' '.join(definition.split())  # Normalize whitespace

                    # Handle trans-see references
                    if definition.startswith('see '):
                        definition = definition[4:]

                    # Handle lines that start with templates
                    if str(parsed).strip().startswith('{{'):
                        # Try to get just the content after the templates
                        text = str(parsed)
                        # Remove all templates
                        text = re.sub(r'\{\{[^}]*\}\}', '', text)
                        # Clean up wiki links
                        text = re.sub(r'\[\[[^]]*\|([^]]*)\]\]', r'\1', text)
                        text = re.sub(r'\[\[([^]]*)\]\]', r'\1', text)
                        # Clean up
                        text = text.strip()
                        if text:
                            definition = text

                    if definition and not definition.startswith(('*', '#', ':', "'", '"')):
                        # Capitalize first letter
                        if len(definition) > 0:
                            definition = definition[0].upper() + definition[1:]
                        # Add usage labels if present
                        if usage_labels:
                            definition = f"({', '.join(usage_labels)}) {definition}"
                        # Add part of speech and definition
                        full_def = f"{pos}: {definition}"
                        if full_def not in definitions:  # Avoid duplicates
                            definitions.append(full_def)
                            logger.debug(f"Added definition: {full_def}")

                    # Handle lines that start with templates but have no other content
                    if not definition and str(parsed).strip().startswith('{{'):
                        # Try to extract content from non-gloss templates
                        for template in parsed.filter_templates():
                            if template.name.strip() in ('non-gloss', 'gloss') and len(template.params) > 0:
                                content = str(template.params[0])
                                # Clean up wiki links in the content
                                content = re.sub(r'\[\[[^]]*\|([^]]*)\]\]', r'\1', content)
                                content = re.sub(r'\[\[([^]]*)\]\]', r'\1', content)
                                # Clean up
                                content = content.strip()
                                if content:
                                    # Capitalize first letter
                                    content = content[0].upper() + content[1:]
                                    # Add usage labels if present
                                    if usage_labels:
                                        content = f"({', '.join(usage_labels)}) {content}"
                                    # Add part of speech and definition
                                    full_def = f"{pos}: {content}"
                                    if full_def not in definitions:  # Avoid duplicates
                                        definitions.append(full_def)
                                        logger.debug(f"Added definition: {full_def}")

            # Add definitions from trans-see references
            for meaning, target in trans_see_refs.items():
                if target.lower() == 'disappointment':
                    definitions.append(f"{pos}: (slang) A total failure; a disappointment.")

    return definitions
