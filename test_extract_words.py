import re

def extract_words(content):
    # This pattern matches:
    # 1. Words with apostrophes (don't, we're, etc.)
    # 2. Possessives (Mike's, dog's)
    # 3. Regular words
    # While excluding standalone punctuation
    words = re.findall(r"\b[A-Za-z]+(?:[''][A-Za-z]+)*\b", content.lower())
    return words

# Test cases
test_cases = [
    "This is a basic test.",
    "Don't break contractions!",
    "We're testing Mike's code.",
    "I'll make sure we've got all cases, won't we?",
    "The dog's bowl and cats' toys.",
    "That's what she's saying, isn't it?"
]

print("Testing word extraction:")
for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test}")
    words = extract_words(test)
    print(f"Extracted words: {words}")
