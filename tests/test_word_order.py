import unittest
import spacy

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

def extract_words(content):
    # Process the text with spaCy
    doc = nlp(content.lower())
    
    # Extract lemmatized words and their original forms, keeping only those with alphabetic characters
    # and filtering out stop words and punctuation
    words = [(token.lemma_, token.text) for token in doc
            if token.is_alpha  # only alphabetic characters
            and not token.is_stop  # not a stop word
            and not token.is_punct  # not punctuation
            and len(token.text) > 1]  # more than one character
    
    return words

class TestWordOrder(unittest.TestCase):
    def test_word_order(self):
        test_text = """This is a test sentence.
        It's going to check if words
        are coming out in the correct order."""
        
        # extract_words returns tuples of (lemma, original), so we'll just take the lemmas
        word_pairs = extract_words(test_text)
        words = [pair[0] for pair in word_pairs]
        
        # Test that words are extracted in order, accounting for spaCy's lemmatization
        expected_words = ['test', 'sentence', 'go', 'check', 'word', 'come', 'correct', 'order']
        self.assertEqual(words, expected_words)

if __name__ == '__main__':
    unittest.main()
