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

# Test cases
test_cases = [
    "This is a basic test.",
    "Don't break contractions! We're testing.",
    "Running and jumped become their base forms.",
    "Better and best become good.",
    "The dog's bowl and cats' toys.",
    "That's what she's saying, isn't it?",
    "I'll make sure we've got all cases, won't we?"
]

print("Testing spaCy word extraction and lemmatization:")
for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test}")
    words = extract_words(test)
    print(f"Extracted words: {words}")
    
    # Show detailed token information
    doc = nlp(test.lower())
    print("\nDetailed token information:")
    for token in doc:
        if token.is_alpha and len(token.text) > 1:
            print(f"Token: {token.text:15} Lemma: {token.lemma_:15} POS: {token.pos_:10} Stop word: {token.is_stop}")
