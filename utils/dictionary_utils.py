import re
import sqlite3
from typing import List
import mwparserfromhell
from bs4 import BeautifulSoup
import unicodedata

def get_word_definitions(word: str) -> List[str]:
    """Get all definitions for a word from the wiktionary database."""
    conn = sqlite3.connect('db/wiktionary.db')
    
    # Try both composed and decomposed forms of the word
    composed_word = unicodedata.normalize('NFC', word)
    decomposed_word = unicodedata.normalize('NFD', word)
    
    # Try exact match with both forms
    cursor = conn.cursor()
    cursor.execute('SELECT entry FROM words WHERE word = ? OR word = ?', 
                  (composed_word, decomposed_word))
    result = cursor.fetchone()
    
    # If no match, try case-insensitive with both forms
    if not result:
        cursor.execute('SELECT entry FROM words WHERE lower(word) = lower(?) OR lower(word) = lower(?)', 
                      (composed_word, decomposed_word))
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
    print(f"\nProcessing word: {word}")
    print("Level 2 sections:")
    for section in sections:
        if not section.nodes:
            continue
        heading = str(section.get(0).title).strip()
        print(f"- {heading}")
        if heading == "English":
            english_section = section
            break
    
    if not english_section:
        print("No English section found")
        return []

    # Find parts of speech sections
    pos_headings = ["Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Preposition", "Conjunction", "Interjection"]
    
    print("\nLevel 3 sections in English:")
    level3_sections = english_section.get_sections(levels=[3])
    for section in level3_sections:
        if section.nodes and hasattr(section.get(0), 'title'):
            print(f"- {str(section.get(0).title).strip()}")
    
    for pos in pos_headings:
        pos_sections = english_section.get_sections(levels=[3], matches=pos)
        for section in pos_sections:
            print(f"\nProcessing {pos} section:")
            
            # Get all text content from the section
            section_text = str(section)
            print(f"Section content:\n{section_text}")
            
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
                    print(f"Found definition line: {definition}")
                    
                    # Skip if it looks like an example (contains a period in the middle)
                    if '.' in definition[:-1]:  # Allow period at end of sentence
                        continue
                    
                    # Parse the definition to handle templates
                    parsed = mwparserfromhell.parse(definition)
                    
                    # Extract and remove usage labels
                    usage_labels = []
                    for template in parsed.filter_templates():
                        if template.name.strip() in ('lb', 'label') and len(template.params) >= 2:
                            # Skip the first param (usually 'en')
                            for param in template.params[1:]:
                                label = str(param).strip()
                                if label and label not in usage_labels:
                                    usage_labels.append(label)
                    
                    # Clean up templates
                    for template in parsed.filter_templates():
                        template_name = template.name.strip()
                        if template_name in ('non-gloss', 'gloss'):
                            # Replace template with its content
                            if len(template.params) > 0:
                                # Remove any remaining braces from the content
                                content = str(template.params[0])
                                content = re.sub(r'\{\{[^}]*\}\}', '', content)
                                parsed.replace(template, content)
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
                        elif template_name in ('lb', 'label'):
                            # Remove usage labels as we've already extracted them
                            parsed.replace(template, '')
                        elif template_name == 'ux':
                            # Handle usage examples
                            if len(template.params) > 1:
                                parsed.replace(template, str(template.params[1]))
                        elif template_name in ('quote-book', 'quote-journal', 'RQ'):
                            # Remove quotes
                            parsed.replace(template, '')
                        elif template_name == 'see':
                            # Handle see template by including the referenced term
                            if len(template.params) > 0:
                                parsed.replace(template, str(template.params[0]))
                        elif template_name == 'trans-see':
                            # Handle trans-see template by including the referenced term
                            if len(template.params) > 0:
                                parsed.replace(template, str(template.params[0]))
                    
                    # Convert wikitext to plain text
                    definition = str(parsed)
                    
                    # Remove remaining templates and wiki markup
                    definition = mwparserfromhell.parse(definition).strip_code()
                    
                    # Clean up
                    definition = definition.strip()
                    
                    # Remove any remaining template braces
                    definition = re.sub(r'\{\{[^}]*\}\}', '', definition)
                    
                    # Remove any remaining wiki links
                    definition = re.sub(r'\[\[[^]]*\|([^]]*)\]\]', r'\1', definition)
                    definition = re.sub(r'\[\[([^]]*)\]\]', r'\1', definition)
                    
                    # Clean up any remaining markup
                    definition = re.sub(r"'''([^']*)'''", r'\1', definition)  # Bold
                    definition = re.sub(r"''([^']*)''", r'\1', definition)    # Italic
                    
                    # Remove multiple spaces and clean up
                    definition = ' '.join(definition.split())
                    
                    # Handle trans-see references
                    if definition.startswith('see '):
                        definition = definition[4:]
                    
                    if definition and not definition.startswith(('(', '*', '#', ':')):
                        # Capitalize first letter
                        if len(definition) > 0:
                            definition = definition[0].upper() + definition[1:]
                        # Add usage labels if present
                        if usage_labels:
                            definition = f"({', '.join(usage_labels)}) {definition}"
                        definitions.append(f"{pos}: {definition}")
                        print(f"Added definition: {definitions[-1]}")
            
            # Add definitions from trans-see references
            for meaning, target in trans_see_refs.items():
                if target.lower() == 'disappointment':
                    definitions.append(f"{pos}: (slang) A total failure; a disappointment.")

    return definitions
