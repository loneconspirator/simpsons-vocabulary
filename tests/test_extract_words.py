import unittest
import re

def extract_words(content):
    # This pattern matches:
    # 1. Words with apostrophes (don't, we're, etc.)
    # 2. Possessives (Mike's, dog's)
    # 3. Regular words
    # While excluding standalone punctuation
    words = re.findall(r"\b[A-Za-z]+(?:[''][A-Za-z]+)*\b", content.lower())
    return words

class TestWordExtraction(unittest.TestCase):
    def test_basic(self):
        result = extract_words("This is a basic test.")
        self.assertEqual(result, ['this', 'is', 'a', 'basic', 'test'])

    def test_contractions(self):
        result = extract_words("Don't break contractions!")
        self.assertEqual(result, ["don't", 'break', 'contractions'])

    def test_possessives(self):
        result = extract_words("We're testing Mike's code.")
        self.assertEqual(result, ["we're", 'testing', "mike's", 'code'])

    def test_complex_contractions(self):
        result = extract_words("I'll make sure we've got all cases, won't we?")
        self.assertEqual(result, ["i'll", 'make', 'sure', "we've", 'got', 'all', 'cases', "won't", 'we'])

    def test_multiple_possessives(self):
        result = extract_words("The dog's bowl and cats' toys.")
        self.assertEqual(result, ['the', "dog's", 'bowl', 'and', 'cats', 'toys'])

    def test_final_test(self):
        result = extract_words("That's what she's saying, isn't it?")
        self.assertEqual(result, ["that's", 'what', "she's", 'saying', "isn't", 'it'])

if __name__ == '__main__':
    unittest.main()
