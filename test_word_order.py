import importlib.util
import sys

# Import the module
spec = importlib.util.spec_from_file_location("process_transcripts", "3_process_transcripts.py")
module = importlib.util.module_from_spec(spec)
sys.modules["process_transcripts"] = module
spec.loader.exec_module(module)

test_text = """This is a test sentence.
It's going to check if words
are coming out in the correct order."""

words = module.extract_words(test_text)
print("Original text:", test_text)
print("\nExtracted words:", words)
