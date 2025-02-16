import unittest
import sys
import os

# Add the parent directory to the Python path so we can import our module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dictionary_utils import get_word_definitions

class TestDictionaryUtils(unittest.TestCase):
    def test_get_word_definitions_example(self):
        # Get definitions for the word "example"
        definitions = get_word_definitions("example")
        
        # Verify we got some definitions
        self.assertTrue(len(definitions) > 0, "Should have found definitions for 'example'")
        
        # Expected patterns for specific parts of speech
        expected_patterns = {
            'Noun': [
                "representative of all such things",
                "illustrate",
                "pattern",
                "warning"
            ]
        }
        
        # Convert definitions to lowercase for case-insensitive matching
        lower_definitions = [d.lower() for d in definitions]
        
        # Check that we have at least one definition for each part of speech
        found_pos = set()
        for definition in definitions:
            pos = definition.split(':', 1)[0].strip()
            found_pos.add(pos)
            
        self.assertIn('Noun', found_pos, "Should have found noun definitions")
        
        # Check that each part of speech's patterns appear in appropriate definitions
        for pos, patterns in expected_patterns.items():
            pos_definitions = [d.split(':', 1)[1].strip().lower() 
                             for d in definitions 
                             if d.startswith(pos + ':')]
            
            for pattern in patterns:
                self.assertTrue(
                    any(pattern in d for d in pos_definitions),
                    f"Should have found a {pos} definition containing '{pattern}'"
                )
        
        # Verify format of definitions
        for definition in definitions:
            self.assertRegex(
                definition,
                r'^(Noun|Verb|Adjective|Adverb|Pronoun|Preposition|Conjunction|Interjection): .+$',
                f"Definition should start with part of speech: {definition}"
            )
        
        # Print the actual definitions for manual review
        print("\nActual definitions found for 'example':")
        for i, definition in enumerate(definitions, 1):
            print(f"{i}. {definition}")

    def test_get_word_definitions_scrawny(self):
        # Get definitions for the word "scrawny"
        definitions = get_word_definitions("scrawny")
        
        # Print actual definitions for debugging
        print("\nActual definitions found for 'scrawny':")
        for i, definition in enumerate(definitions, 1):
            print(f"{i}. {definition}")
        
        # Verify we got exactly one definition
        self.assertEqual(len(definitions), 1, "Should have found exactly one definition for 'scrawny'")
        
        # Verify the exact definition
        expected_definition = "Adjective: Thin, malnourished and weak."
        self.assertEqual(definitions[0], expected_definition, 
                        f"Definition should be exactly '{expected_definition}'")

    def test_nonexistent_word(self):
        # Test a word that shouldn't exist in the dictionary
        definitions = get_word_definitions("xyzzynonexistent")
        self.assertEqual(len(definitions), 0, "Should return empty list for nonexistent word")

    def test_case_insensitivity(self):
        # Test that the function handles different cases the same way
        lower_defs = get_word_definitions("example")
        upper_defs = get_word_definitions("EXAMPLE")
        title_defs = get_word_definitions("Example")
        
        self.assertEqual(lower_defs, upper_defs, "Case should not affect the definitions returned")
        self.assertEqual(lower_defs, title_defs, "Case should not affect the definitions returned")

    def test_word_with_accent(self):
        """Test that words with accents like 'touché' are handled correctly"""
        definitions = get_word_definitions("touché")
        
        # Verify we got some definitions
        self.assertTrue(len(definitions) > 0, "Should have found definitions for 'touché'")
        
        # Check format of each definition
        for definition in definitions:
            # Each definition should start with a part of speech followed by a colon
            self.assertRegex(
                definition,
                r'^(Noun|Verb|Adjective|Adverb|Pronoun|Preposition|Conjunction|Interjection): .+$',
                f"Definition should start with part of speech and be properly formatted: {definition}"
            )
            
            # Definition should not contain stray brackets or braces
            self.assertNotRegex(
                definition,
                r'[{}\\[\\]]',
                f"Definition should not contain stray brackets or braces: {definition}"
            )
            
            # Definition should be a complete, coherent sentence or phrase
            self.assertNotRegex(
                definition,
                r'^[a-z]',  # Definition content should not start with lowercase
                f"Definition content should start with uppercase: {definition}"
            )
        
        # Print the actual definitions for manual review
        print("\nActual definitions found for 'touché':")
        for i, definition in enumerate(definitions, 1):
            print(f"{i}. {definition}")

if __name__ == '__main__':
    unittest.main()
