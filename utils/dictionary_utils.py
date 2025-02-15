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
                # Clean up the definition
                definition = def_line.group(0)
                
                # Remove the leading #
                definition = re.sub(r'^#\s*', '', definition)
                
                # Remove wiki templates {{...}}
                definition = re.sub(r'\{\{[^}]+\}\}', '', definition)
                
                # Handle links [[word|display]] -> display
                definition = re.sub(r'\[\[[^]|]+\|([^]]+)\]\]', r'\1', definition)
                
                # Handle simple links [[word]] -> word
                definition = re.sub(r'\[\[([^]]+)\]\]', r'\1', definition)
                
                # Remove quotes and other markup
                definition = re.sub(r"''([^']+)''", r'\1', definition)
                
                # Remove references <ref>...</ref>
                definition = re.sub(r'<ref>.*?</ref>', '', definition)
                
                # Clean up whitespace
                definition = definition.strip()
                
                if definition and not definition.startswith(('(', '*', '#', ':')):
                    definitions.append(f"{pos}: {definition}")
        
        return definitions
        
    except sqlite3.Error as e:
        print(f"Database error occurred: {e}")
        return []
        
    finally:
        cursor.close()
        conn.close()
