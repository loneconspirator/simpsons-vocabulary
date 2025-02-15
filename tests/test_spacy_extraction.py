import unittest
import spacy

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

def extract_words(content):
    # Process the text with spaCy
    doc = nlp(content.lower())
    
    # Extract lemmatized words, keeping only those with alphabetic characters
    # and filtering out stop words and punctuation
    words = [token.lemma_ for token in doc 
            if token.is_alpha  # only alphabetic characters
            and not token.is_stop  # not a stop word
            and not token.is_punct  # not punctuation
            and len(token.text) > 1]  # more than one character
    
    return words

class TestSpacyExtraction(unittest.TestCase):
    def test_basic(self):
        result = extract_words("This is a basic test.")
        self.assertEqual(result, ['basic', 'test'])

    def test_contractions(self):
        result = extract_words("Don't break contractions! We're testing.")
        self.assertEqual(result, ['break', 'contraction', 'test'])

    def test_verb_forms(self):
        result = extract_words("Running and jumped become their base forms.")
        self.assertEqual(result, ['run', 'jump', 'base', 'form'])

    def test_comparatives(self):
        result = extract_words("Better and best become good.")
        self.assertEqual(result, ['well', 'well', 'good'])  # spaCy lemmatizes 'better/best' to 'well'

    def test_possessives(self):
        result = extract_words("The dog's bowl and cats' toys.")
        self.assertEqual(result, ['dog', 'bowl', 'cat', 'toy'])

    def test_she_s(self):
        result = extract_words("That's what she's saying, isn't it?")
        self.assertEqual(result, ['say'])  # spaCy correctly filters stop words

    def test_ll_won_t(self):
        result = extract_words("I'll make sure we've got all cases, won't we?")
        self.assertEqual(result, ['sure', 'get', 'case', 'will'])  # spaCy's actual lemmatization

    def print_token_info(self, text):
        """Helper method to print detailed token information for debugging"""
        doc = nlp(text.lower())
        print(f"\nDetailed token information for: {text}")
        for token in doc:
            if token.is_alpha and len(token.text) > 1:
                print(f"Token: {token.text:15} Lemma: {token.lemma_:15} POS: {token.pos_:10} Stop word: {token.is_stop}")

if __name__ == '__main__':
    unittest.main()
