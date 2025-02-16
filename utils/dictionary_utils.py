import sqlite3
import re
import os
from typing import List

def get_word_definitions(word: str) -> List[str]:
    """
    Retrieve all English language definitions for a given word from the Wiktionary database.
    Each definition is prefixed with its part of speech (e.g., "Noun: a definition").
    
    Args:
        word (str): The word to look up definitions for
        
    Returns:
        List[str]: A list of English language definitions for the word, each prefixed with its part of speech.
        Returns an empty list if no definitions are found.
    """
    # Get the path to the database relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(os.path.dirname(current_dir), 'db', 'wiktionary.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Query the database for the word's entry
        cursor.execute('''
            SELECT entry 
            FROM words 
            WHERE word = ?
        ''', (word.lower(),))
        
        result = cursor.fetchone()
        if not result:
            return []
            
        entry_text = result[0]
        
        # Parse the entry text to extract English definitions
        definitions = []
        
        # Look for English section
        english_section_match = re.search(r'==English==.*?(?=^==\w)', entry_text, re.DOTALL | re.MULTILINE)
        if not english_section_match:
            # If no other language sections follow, take everything after English
            english_section_match = re.search(r'==English==(.*)', entry_text, re.DOTALL)
            if not english_section_match:
                return []
                
        english_section = english_section_match.group(0 if '==English==' in english_section_match.group(0) else 1)
        
        # Find definitions under various parts of speech
        pos_sections = re.finditer(r'===(Noun|Verb|Adjective|Adverb|Pronoun|Preposition|Conjunction|Interjection)===\s*(.*?)(?===|\Z)', 
                                 english_section, 
                                 re.DOTALL)
        
        for pos_section in pos_sections:
            pos = pos_section.group(1)
            section_text = pos_section.group(2)
            
            # Find all definition lines that start with # but not #* or ##
            def_lines = re.finditer(r'^#[^#\n*].*$', section_text, re.MULTILINE)
            
            for def_line in def_lines:
                # Get the raw definition line
                definition = def_line.group(0)
                
                # Remove the leading #
                definition = re.sub(r'^#\s*', '', definition)
                
                # Extract usage labels before removing templates
                usage_labels = []
                for label_match in re.finditer(r'\{\{(?:lb|label)\|en\|([^}]+)\}\}', definition):
                    label = label_match.group(1)
                    # Don't add duplicate labels
                    if label.lower() not in (l.lower() for l in usage_labels):
                        usage_labels.append(label)
                
                # Handle special templates before removing others
                special_templates = {
                    'non-gloss': r'\{\{non-gloss\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}',
                    'l': r'\{\{l\|en\|([^}|]+)(?:\|[^}]*)*\}\}',  # {{l|en|word|...}}
                    'cap': r'\{\{cap\|([^}]+)\}\}',  # {{cap|Word}}
                }
                
                for template_type, pattern in special_templates.items():
                    if template_type == 'non-gloss':
                        non_gloss_match = re.search(pattern, definition)
                        if non_gloss_match:
                            content = non_gloss_match.group(1)
                            content = re.sub(r'\{\{,\}\}', ',', content)
                            content = re.sub(r'\{\{[^{}]*\}\}', '', content)
                            definition = content
                    else:
                        definition = re.sub(pattern, r'\1', definition)
                
                # Handle links [[word|display]] -> display and [[word]] -> word
                definition = re.sub(r'\[\[[^]|]+\|([^]]+)\]\]', r'\1', definition)
                definition = re.sub(r'\[\[([^]]+)\]\]', r'\1', definition)
                
                # Remove references <ref>...</ref>
                definition = re.sub(r'<ref>.*?</ref>', '', definition)
                
                # Remove remaining wiki templates {{...}} - handle nested braces
                definition = re.sub(r'\{\{(?!l\|en)[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\}', '', definition)
                
                # Remove any remaining templates or markup
                definition = re.sub(r'[{}[\]<>]', '', definition)
                
                # Remove template prefixes that might remain after template removal
                definition = re.sub(r'^(?:Non-gloss|gloss|n)\|', '', definition, flags=re.IGNORECASE)
                
                # Clean up whitespace and ensure first letter is capitalized
                definition = definition.strip()
                # Remove leading commas and whitespace
                definition = re.sub(r'^,\s*', '', definition)
                
                # Remove duplicate words at the start (e.g. "Transitive Transitive")
                definition = re.sub(r'^(\w+)\s+\1\s+', r'\1 ', definition, flags=re.IGNORECASE)
                
                if definition and not definition.startswith(('(', '*', '#', ':')):
                    # Capitalize first letter of the definition
                    if len(definition) > 0:
                        definition = definition[0].upper() + definition[1:]
                    # Add usage labels in parentheses if present
                    if usage_labels:
                        definition = f"({', '.join(usage_labels)}) {definition}"
                    definitions.append(f"{pos}: {definition}")
        
        return definitions
        
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()
